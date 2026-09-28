# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# main.py
#
# Fleet Dashboard - Main FastAPI application
# Monitors multiple GPS simulators via UDP
#
# Richard J. Sears
# richardjsears@protonmail.com
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Fleet Dashboard API server."""

import asyncio
import json
import logging
import platform
import socket
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

from .config import get_settings, SimConfig
from .airports import find_closest_airport
from .recorder import EXPORT_FORMATS, FlightRecorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SWITCH_PING_INTERVAL: float = 1.0  # seconds between switch pings per simulator


def ping_host(ip: str) -> bool:
    """Send one ICMP echo to ip. Returns True iff ping exits 0. Never raises."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", param, "1", "-W", "1", ip],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


class SimulatorState:
    """State for a single simulator."""

    def __init__(self, name: str, port: int, gps_system: str = "", switch_ip: str = ""):
        self.name = name
        self.port = port
        self.gps_system = gps_system  # Which system runs the GPS software
        self.lat: float = 0.0
        self.lon: float = 0.0
        self.altitude_ft: float = 0.0
        self.speed_kts: float = 0.0
        self.heading: float = 0.0
        self.last_update: Optional[float] = None
        self.packet_count: int = 0
        self.closest_airport: Optional[dict] = None
        self.airport_distance_nm: Optional[float] = None
        self._lock = threading.Lock()
        # Health monitoring
        self.switch_ip: str = switch_ip
        self.switch_reachable: Optional[bool] = None  # None = not configured/checked
        self.last_switch_check: Optional[float] = None
        self.emulator_connected: bool = False
        self.sim_reachable: bool = False
        self.receiving_udp: bool = False
        self.last_heartbeat: Optional[float] = None
        self.emulator_uptime: int = 0

    @property
    def emulator_online(self) -> bool:
        """Check if emulator is online (received heartbeat within last 3 seconds)."""
        if self.last_heartbeat is None:
            return False
        return (time.time() - self.last_heartbeat) < 3.0

    @property
    def is_online(self) -> bool:
        """Check if simulator is online (received packet within last 5 seconds)."""
        if self.last_update is None:
            return False
        return (time.time() - self.last_update) < 5.0

    def update(self, data: dict) -> None:
        """Update state from received packet."""
        with self._lock:
            self.lat = data.get("lat", 0.0)
            self.lon = data.get("lon", 0.0)
            self.altitude_ft = data.get("alt_ft", 0.0)
            self.speed_kts = data.get("speed_kts", 0.0)
            self.heading = data.get("heading", 0.0)
            self.last_update = time.time()
            self.packet_count += 1

            # Find closest airport
            result = find_closest_airport(self.lat, self.lon)
            if result:
                self.closest_airport = result["airport"]
                self.airport_distance_nm = result["distance_nm"]

    def update_heartbeat(self, data: dict) -> None:
        """Update state from heartbeat packet."""
        with self._lock:
            self.emulator_connected = True
            self.sim_reachable = data.get("sim_reachable", False)
            self.receiving_udp = data.get("receiving_udp", False)
            self.emulator_uptime = data.get("uptime_seconds", 0)
            self.last_heartbeat = time.time()

    def update_switch(self, reachable: bool) -> None:
        """Record the latest switch ping result (called from the ping thread)."""
        with self._lock:
            self.switch_reachable = reachable
            self.last_switch_check = time.time()

    def to_dict(self) -> dict:
        """Convert state to dictionary for API response."""
        with self._lock:
            return {
                "name": self.name,
                "port": self.port,
                "gps_system": self.gps_system,
                "is_online": self.is_online,
                "lat": round(self.lat, 6),
                "lon": round(self.lon, 6),
                "altitude_ft": round(self.altitude_ft),
                "speed_kts": round(self.speed_kts),
                "heading": round(self.heading),
                "packet_count": self.packet_count,
                "last_update": self.last_update,
                "closest_airport": self.closest_airport,
                "airport_distance_nm": round(self.airport_distance_nm, 1)
                if self.airport_distance_nm
                else None,
                # Health data
                "emulator_online": self.emulator_online,
                "sim_reachable": self.sim_reachable,
                "receiving_udp": self.receiving_udp,
                "emulator_uptime": self.emulator_uptime,
                "switch_ip": self.switch_ip,
                "switch_reachable": self.switch_reachable,
            }


class FleetMonitor:
    """Monitors multiple simulators via UDP."""

    def __init__(self):
        self.simulators: dict[int, SimulatorState] = {}
        self._sockets: list[socket.socket] = []
        self._running = False
        self._threads: list[threading.Thread] = []
        self.recorder: Optional[FlightRecorder] = None
        self.last_evaluated: Optional[float] = None

    def mark_evaluated(self) -> None:
        """Record that the fleet state was just re-evaluated (called by the 1 Hz tick only)."""
        self.last_evaluated = time.time()

    @property
    def generated_at(self) -> Optional[str]:
        """ISO-8601 UTC 'Z' timestamp of the last evaluation tick, or None before the first tick."""
        if self.last_evaluated is None:
            return None
        return datetime.fromtimestamp(self.last_evaluated, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    def configure(self, sims: list[SimConfig]) -> None:
        """Configure simulators to monitor."""
        for sim in sims:
            self.simulators[sim.port] = SimulatorState(
                sim.name, sim.port, sim.gps_system, sim.switch_ip
            )
        logger.info(f"Configured {len(sims)} simulators: {[s.name for s in sims]}")

    def start(self) -> None:
        """Start listening on all configured ports."""
        if self._running:
            return

        self._running = True
        for port, sim in self.simulators.items():
            thread = threading.Thread(target=self._listen, args=(port,), daemon=True)
            thread.start()
            self._threads.append(thread)
            logger.info(f"Started listener for {sim.name} on port {port}")

        for port, sim in self.simulators.items():
            if sim.switch_ip:
                thread = threading.Thread(
                    target=self._ping_switch, args=(port,), daemon=True
                )
                thread.start()
                self._threads.append(thread)
                logger.info(f"Started switch monitor for {sim.name} -> {sim.switch_ip}")

        self.mark_evaluated()

    def _ping_switch(self, port: int) -> None:
        """Ping this simulator's switch every SWITCH_PING_INTERVAL seconds while running."""
        sim = self.simulators[port]
        while self._running:
            started = time.monotonic()
            reachable = ping_host(sim.switch_ip)
            previous = sim.switch_reachable
            sim.update_switch(reachable)
            if previous != reachable:
                logger.info(
                    f"{sim.name} switch {sim.switch_ip} "
                    f"{'reachable' if reachable else 'UNREACHABLE'}"
                )
            time.sleep(max(0.0, SWITCH_PING_INTERVAL - (time.monotonic() - started)))

    def stop(self) -> None:
        """Stop all listeners."""
        self._running = False
        for sock in self._sockets:
            try:
                sock.close()
            except Exception:
                pass
        self._sockets.clear()
        self._threads.clear()
        logger.info("Fleet monitor stopped")

    def _listen(self, port: int) -> None:
        """Listen for UDP packets on a specific port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.settimeout(1.0)
        self._sockets.append(sock)

        sim = self.simulators[port]
        logger.info(f"Listening for {sim.name} on UDP port {port}")

        while self._running:
            try:
                data, addr = sock.recvfrom(1024)
                packet = data.decode().strip()
                try:
                    gps_data = json.loads(packet)
                    if gps_data.get("type") == "heartbeat":
                        sim.update_heartbeat(gps_data)
                        logger.debug(f"Received heartbeat for {sim.name}: {gps_data}")
                    else:
                        sim.update(gps_data)
                        if self.recorder:
                            self.recorder.record(sim.name, gps_data)
                        logger.debug(f"Received packet for {sim.name}: {gps_data}")
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {addr}: {packet[:50]}")
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Error receiving on port {port}: {e}")

    def get_all_states(self) -> list[dict]:
        """Get current state of all simulators."""
        states = []
        for sim in self.simulators.values():
            state = sim.to_dict()
            state["recording"] = bool(
                self.recorder and self.recorder.is_enabled(sim.name)
            )
            states.append(state)
        return states


# Global fleet monitor instance
fleet_monitor = FleetMonitor()

# Flight data recorder (created at startup)
flight_recorder: Optional[FlightRecorder] = None

# WebSocket connections
websocket_connections: set[WebSocket] = set()


async def broadcast_state():
    """Broadcast fleet state to all connected WebSocket clients."""
    while True:
        await evaluate_and_broadcast()
        await asyncio.sleep(1.0)  # Update every second


async def evaluate_and_broadcast():
    """Evaluate fleet state once and broadcast it to connected clients."""
    try:
        state = fleet_monitor.get_all_states()
        fleet_monitor.mark_evaluated()
        message = json.dumps(
            {
                "type": "fleet_state",
                "generated_at": fleet_monitor.generated_at,
                "simulators": state,
            }
        )
    except Exception:
        logger.exception("Fleet state evaluation failed; generated_at not advanced")
        return

    try:
        if websocket_connections:
            disconnected = set()
            for ws in websocket_connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            websocket_connections.difference_update(disconnected)
    except Exception:
        logger.exception("Fleet state broadcast failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global flight_recorder
    settings = get_settings()
    fleet_monitor.configure(settings.simulators)

    flight_recorder = FlightRecorder(
        settings.recording_db_path,
        retention_days=settings.recording_retention_days,
        default_enabled=settings.recording_default_enabled,
    )
    flight_recorder.register_sims([s.name for s in settings.simulators])
    flight_recorder.start()
    fleet_monitor.recorder = flight_recorder

    fleet_monitor.start()

    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_state())

    yield

    broadcast_task.cancel()
    fleet_monitor.stop()
    flight_recorder.stop()


app = FastAPI(
    title="Fleet Dashboard API",
    description=(
        "REST + WebSocket API for the Fleet Dashboard. Aggregates UDP "
        "telemetry and heartbeats from multiple NMEA GPS Simulator instances "
        "and broadcasts a combined fleet view to connected web clients."
    ),
    version="1.0.1",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status", tags=["Status"])
async def get_status():
    """Get current fleet status."""
    return {
        "simulators": fleet_monitor.get_all_states(),
        "generated_at": fleet_monitor.generated_at,
        "timestamp": datetime.utcnow().isoformat(),
    }


class RecordingToggle(BaseModel):
    enabled: bool


def _get_recorder() -> FlightRecorder:
    if flight_recorder is None:
        raise HTTPException(status_code=503, detail="Flight recorder not running")
    return flight_recorder


def _parse_time(value: str, field: str) -> int:
    """Parse an ISO 8601 date/time (UTC if no offset) into UTC milliseconds."""
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid {field} time: {value!r}"
        ) from None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _parse_range(
    start: str, end: str, sims: Optional[str]
) -> tuple[int, int, Optional[list[str]]]:
    start_ms = _parse_time(start, "start")
    end_ms = _parse_time(end, "end")
    if end_ms < start_ms:
        raise HTTPException(status_code=400, detail="End time is before start time")
    sim_list = [s.strip() for s in sims.split(",") if s.strip()] if sims else None
    return start_ms, end_ms, sim_list


@app.get("/api/recording", tags=["Recording"])
async def get_recording_status():
    """Recording toggles, stored time span and database size."""
    return await asyncio.to_thread(_get_recorder().status)


@app.put("/api/recording/{sim_name}", tags=["Recording"])
async def set_recording(sim_name: str, body: RecordingToggle):
    """Turn recording on or off for one simulator."""
    recorder = _get_recorder()
    try:
        await asyncio.to_thread(recorder.set_enabled, sim_name, body.enabled)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Unknown simulator: {sim_name}"
        ) from None
    return {"name": sim_name, "recording": body.enabled}


@app.get("/api/recording/count", tags=["Recording"])
async def count_recorded(
    start: str = Query(..., description="ISO 8601 start time (UTC if no offset)"),
    end: str = Query(..., description="ISO 8601 end time (UTC if no offset)"),
    sims: Optional[str] = Query(None, description="Comma-separated sim names"),
):
    """Number of recorded positions in a time range (export preview)."""
    start_ms, end_ms, sim_list = _parse_range(start, end, sims)
    rows = await asyncio.to_thread(_get_recorder().count, start_ms, end_ms, sim_list)
    return {"rows": rows}


@app.get("/api/recording/export", tags=["Recording"])
async def export_recorded(
    start: str = Query(..., description="ISO 8601 start time (UTC if no offset)"),
    end: str = Query(..., description="ISO 8601 end time (UTC if no offset)"),
    format: str = Query("csv", description="csv, json, xml, gpx or kml"),
    sims: Optional[str] = Query(None, description="Comma-separated sim names"),
):
    """Download recorded positions in a time range as a file."""
    fmt = format.lower()
    if fmt not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format {format!r}. Use one of: "
            + ", ".join(EXPORT_FORMATS),
        )
    start_ms, end_ms, sim_list = _parse_range(start, end, sims)
    media_type, ext = EXPORT_FORMATS[fmt]
    stamp = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
    filename = f"flight_data_{stamp:%Y%m%dT%H%MZ}.{ext}"
    return StreamingResponse(
        _get_recorder().export(fmt, start_ms, end_ms, sim_list),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    """ReDoc UI served from a pinned CDN.

    FastAPI's default ReDoc mount uses an `@next` CDN tag that periodically
    returns 404. Serving ReDoc through this custom route with a pinned version
    keeps the page reliable.
    """
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="Fleet Dashboard API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    websocket_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(websocket_connections)}")

    try:
        # Send initial state
        state = fleet_monitor.get_all_states()
        await websocket.send_text(
            json.dumps(
                {
                    "type": "fleet_state",
                    "generated_at": fleet_monitor.generated_at,
                    "simulators": state,
                }
            )
        )

        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        websocket_connections.discard(websocket)
        logger.info(
            f"WebSocket client disconnected. Total: {len(websocket_connections)}"
        )


# Serve static files (frontend build)
frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount(
        "/assets", StaticFiles(directory=frontend_build / "assets"), name="assets"
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Serve frontend files."""
        file_path = frontend_build / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_build / "index.html")
