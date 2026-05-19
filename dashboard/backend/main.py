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
import socket
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from .config import get_settings, SimConfig
from .airports import find_closest_airport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimulatorState:
    """State for a single simulator."""

    def __init__(self, name: str, port: int, gps_system: str = ""):
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
            }


class FleetMonitor:
    """Monitors multiple simulators via UDP."""

    def __init__(self):
        self.simulators: dict[int, SimulatorState] = {}
        self._sockets: list[socket.socket] = []
        self._running = False
        self._threads: list[threading.Thread] = []

    def configure(self, sims: list[SimConfig]) -> None:
        """Configure simulators to monitor."""
        for sim in sims:
            self.simulators[sim.port] = SimulatorState(
                sim.name, sim.port, sim.gps_system
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
        return [sim.to_dict() for sim in self.simulators.values()]


# Global fleet monitor instance
fleet_monitor = FleetMonitor()

# WebSocket connections
websocket_connections: set[WebSocket] = set()


async def broadcast_state():
    """Broadcast fleet state to all connected WebSocket clients."""
    while True:
        if websocket_connections:
            state = fleet_monitor.get_all_states()
            message = json.dumps({"type": "fleet_state", "simulators": state})
            disconnected = set()
            for ws in websocket_connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)
            websocket_connections.difference_update(disconnected)
        await asyncio.sleep(1.0)  # Update every second


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()
    fleet_monitor.configure(settings.simulators)
    fleet_monitor.start()

    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_state())

    yield

    broadcast_task.cancel()
    fleet_monitor.stop()


app = FastAPI(
    title="Fleet Dashboard API",
    description=(
        "REST + WebSocket API for the Fleet Dashboard. Aggregates UDP "
        "telemetry and heartbeats from multiple NMEA GPS Simulator instances "
        "and broadcasts a combined fleet view to connected web clients."
    ),
    version="1.0.0",
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
        "timestamp": datetime.utcnow().isoformat(),
    }


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
            json.dumps({"type": "fleet_state", "simulators": state})
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
