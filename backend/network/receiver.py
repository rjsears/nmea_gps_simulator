# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# receiver.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""UDP/TCP receiver for GPS data."""

import json
import socket
import logging
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SUPPORTED_PROTOCOLS = {"udp", "tcp"}


REQUIRED_FIELDS = {"lat", "lon", "alt_ft", "speed_kts", "heading", "timestamp"}


def parse_cygnus_packet(packet: str) -> Optional[dict]:
    """Parse CYGNUS format GPS packet.

    Format: $CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3

    Args:
        packet: CYGNUS format string

    Returns:
        Parsed dict in standard format or None if invalid
    """
    try:
        # Remove $CYGNUS: prefix
        if not packet.startswith("$CYGNUS:"):
            logger.warning("parse_cygnus_packet: packet doesn't start with $CYGNUS:")
            return None

        params_str = packet[8:]  # Skip "$CYGNUS:"
        logger.info(f"parse_cygnus_packet: params_str = {repr(params_str)}")

        # Parse query string format
        params = {}
        for pair in params_str.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                # Strip whitespace and null bytes from values
                params[key.strip()] = value.strip().rstrip("\x00")

        logger.info(f"parse_cygnus_packet: parsed params = {params}")

        # Validate required fields
        required = {"lat", "lon", "heading", "alt", "airspeed"}
        if not required.issubset(params.keys()):
            logger.warning(f"CYGNUS packet missing fields: {required - params.keys()}")
            return None

        # Convert to standard format
        data = {
            "lat": float(params["lat"]),
            "lon": float(params["lon"]),
            "heading": float(params["heading"]),  # true ground track
            "alt_ft": float(params["alt"]),  # altitude in feet MSL
            "speed_kts": float(params["airspeed"]),  # true airspeed in knots
            "timestamp": time.time(),  # Add timestamp
        }

        logger.info(
            f"Parsed CYGNUS packet: lat={data['lat']}, lon={data['lon']}, alt={data['alt_ft']}, speed={data['speed_kts']}"
        )
        return data

    except (ValueError, KeyError) as e:
        logger.warning(f"Failed to parse CYGNUS packet: {e}")
        return None


def parse_gps_packet(packet: str) -> Optional[dict]:
    """Parse GPS packet - auto-detects JSON or CYGNUS format.

    Supported formats:
    - JSON: {"lat": ..., "lon": ..., "alt_ft": ..., "speed_kts": ..., "heading": ..., "timestamp": ...}
    - CYGNUS: $CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3

    Args:
        packet: GPS data string (JSON or CYGNUS format)

    Returns:
        Parsed dict or None if invalid
    """
    # Strip whitespace and null bytes
    packet = packet.strip().rstrip("\x00")
    logger.info(f"parse_gps_packet: stripped packet = {repr(packet[:80])}")

    # Try CYGNUS format first (starts with $CYGNUS:)
    if packet.startswith("$CYGNUS:"):
        logger.info("Detected CYGNUS format, calling parse_cygnus_packet")
        return parse_cygnus_packet(packet)

    # Try JSON format
    try:
        data = json.loads(packet)
        if not REQUIRED_FIELDS.issubset(data.keys()):
            logger.warning(
                f"JSON packet missing required fields: {REQUIRED_FIELDS - data.keys()}"
            )
            return None
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse packet (not JSON or CYGNUS): {e}")
        return None


@dataclass
class ReceiverState:
    """State of the network receiver."""

    is_running: bool = False
    is_connected: bool = False
    last_packet: Optional[dict] = None
    packet_count: int = 0
    sender_address: Optional[str] = None
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )


class NetworkReceiver:
    """Receives GPS data packets via UDP or TCP."""

    def __init__(
        self,
        port: int = 12000,
        protocol: str = "udp",
        on_packet: Optional[Callable[[dict], None]] = None,
    ):
        """Initialize network receiver.

        Args:
            port: Port to listen on (default 12000)
            protocol: "udp" or "tcp"
            on_packet: Callback function when packet received

        Raises:
            ValueError: If protocol is not "udp" or "tcp"
        """
        protocol_lower = protocol.lower()
        if protocol_lower not in SUPPORTED_PROTOCOLS:
            raise ValueError(
                f"Unsupported protocol: {protocol!r}. "
                f"Supported protocols: {', '.join(sorted(SUPPORTED_PROTOCOLS))}"
            )
        self.port = port
        self.protocol = protocol_lower
        self.on_packet = on_packet

        self.state = ReceiverState()
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start receiving in background thread."""
        if self.state.is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.state.is_running = True
        logger.info(f"Receiver started on port {self.port} ({self.protocol.upper()})")

    def stop(self) -> None:
        """Stop receiving."""
        self._stop_event.set()
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join(timeout=2)
        self.state.is_running = False
        self.state.is_connected = False
        logger.info("Receiver stopped")

    def _run(self) -> None:
        """Main receive loop."""
        if self.protocol == "udp":
            self._run_udp()
        else:
            self._run_tcp()

    def _run_udp(self) -> None:
        """UDP receive loop."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("0.0.0.0", self.port))
        self._socket.settimeout(1.0)  # Allow checking stop event
        logger.info(f"UDP receiver listening on 0.0.0.0:{self.port}")

        while not self._stop_event.is_set():
            try:
                data, addr = self._socket.recvfrom(1024)
                raw_data = data.decode()
                logger.info(
                    f"UDP received {len(data)} bytes from {addr[0]}: {repr(raw_data[:100])}"
                )
                self._handle_packet(raw_data, addr[0])
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"UDP receive error: {e}")

    def _run_tcp(self) -> None:
        """TCP receive loop."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("0.0.0.0", self.port))
        self._socket.listen(1)
        self._socket.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                conn, addr = self._socket.accept()
                self.state.is_connected = True
                self.state.sender_address = addr[0]
                logger.info(f"TCP client connected: {addr[0]}")

                conn.settimeout(1.0)
                buffer = ""

                while not self._stop_event.is_set():
                    try:
                        data = conn.recv(1024).decode()
                        if not data:
                            break
                        buffer += data

                        # Process complete lines
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line.strip():
                                self._handle_packet(line.strip(), addr[0])
                    except socket.timeout:
                        continue

                conn.close()
                self.state.is_connected = False
                logger.info("TCP client disconnected")

            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"TCP receive error: {e}")

    def _handle_packet(self, packet: str, sender: str) -> None:
        """Handle received packet."""
        logger.info(f"_handle_packet called with packet from {sender}")
        data = parse_gps_packet(packet)
        if data:
            logger.info(f"Packet parsed successfully: {data}")
            with self.state._lock:
                self.state.last_packet = data
                self.state.packet_count += 1
                self.state.sender_address = sender
                self.state.is_connected = True
                packet_count = self.state.packet_count

            if self.on_packet:
                logger.info("Calling on_packet callback")
                self.on_packet(data)
            else:
                logger.warning("No on_packet callback registered!")

            logger.info(f"Received packet #{packet_count} from {sender}")
        else:
            logger.warning(f"Failed to parse packet from {sender}: {repr(packet[:80])}")
