# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# receiver_runner.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Receiver runner - handles receiver mode, converting incoming GPS data to NMEA output."""

import asyncio
import logging
import threading
from typing import Optional

from .network.receiver import NetworkReceiver
from .nmea.engine import NmeaEngine
from .serial_manager import SerialManager
from .config import get_settings

logger = logging.getLogger(__name__)


class ReceiverRunner:
    """Runs the receiver mode - listens for GPS data and outputs NMEA to USB.

    Receives GPS JSON packets from network, converts to NMEA sentences,
    and writes to serial port.
    """

    def __init__(self):
        self._receiver: Optional[NetworkReceiver] = None
        self._engine: Optional[NmeaEngine] = None
        self._serial: Optional[SerialManager] = None
        self._running = False
        self._ws_manager = None
        self._event_loop = None
        self._serial_device = None
        self._enabled_sentences: set[str] = set()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        if self._receiver:
            return self._receiver.state.is_connected
        return False

    def set_ws_manager(self, ws_manager, event_loop):
        """Set the WebSocket manager for broadcasting output."""
        self._ws_manager = ws_manager
        self._event_loop = event_loop

    def start(
        self,
        port: int,
        protocol: str,
        serial_device: Optional[str],
        enabled_sentences: set[str],
        baudrate: int = 115200,
    ) -> None:
        """Start the receiver.

        Args:
            port: Network port to listen on
            protocol: "udp" or "tcp"
            serial_device: Serial device path for NMEA output
            enabled_sentences: Set of enabled NMEA sentence types
        """
        if self._running:
            logger.warning("Receiver already running")
            return

        settings = get_settings()
        self._serial_device = serial_device
        self._enabled_sentences = enabled_sentences

        logger.info(f"Starting receiver on port {port} ({protocol})")
        logger.info(f"Serial device: {serial_device}")
        logger.info(f"Enabled sentences: {enabled_sentences}")

        # Create NMEA engine (will be updated when packets arrive)
        self._engine = NmeaEngine(
            lat=0,
            lon=0,
            altitude_ft=0,
            speed_kts=0,
            heading=0,
            enabled_sentences=enabled_sentences,
            altitude_rate_ft_per_2sec=settings.altitude_rate_ft_per_2sec,
            airspeed_rate_kts_per_sec=settings.airspeed_rate_kts_per_sec,
            heading_rate_deg_per_sec=settings.heading_rate_deg_per_sec,
        )

        # Open serial port if device specified
        if serial_device:
            try:
                logger.info(f"Opening serial port: {serial_device} at {baudrate} baud")
                self._serial = SerialManager(serial_device, baudrate=baudrate)
                self._serial.open()
                logger.info(f"Serial port opened successfully: {serial_device}")
            except Exception as e:
                logger.error(f"Failed to open serial port {serial_device}: {e}")
                raise RuntimeError(f"Failed to open serial port: {e}")

        # Create and start network receiver
        self._receiver = NetworkReceiver(
            port=port,
            protocol=protocol,
            on_packet=self._handle_packet,
        )
        self._receiver.start()
        self._running = True
        logger.info("Receiver started")

    def stop(self) -> None:
        """Stop the receiver."""
        if not self._running:
            return

        logger.info("Stopping receiver...")

        if self._receiver:
            self._receiver.stop()
            self._receiver = None

        if self._serial:
            try:
                self._serial.close()
                logger.info(f"Serial port closed: {self._serial_device}")
            except Exception as e:
                logger.warning(f"Error closing serial port: {e}")
            self._serial = None

        self._engine = None
        self._running = False
        self._serial_device = None
        logger.info("Receiver stopped")

    def _handle_packet(self, data: dict) -> None:
        """Handle received GPS packet - convert to NMEA and output."""
        if not self._engine:
            logger.warning("No engine configured, ignoring packet")
            return

        logger.info(f"Received packet: lat={data['lat']}, lon={data['lon']}")

        # Update engine with received position
        self._engine.update_position(
            lat=data["lat"],
            lon=data["lon"],
            altitude_ft=data["alt_ft"],
            speed_kts=data["speed_kts"],
            heading=data["heading"],
        )

        # Generate NMEA sentences
        sentences = self._engine.generate()
        logger.info(f"Generated {len(sentences)} NMEA sentences")

        # Write to serial port
        if self._serial and self._serial.is_open:
            bytes_written = 0
            for sentence in sentences:
                bytes_written += self._serial.write(sentence)
            logger.info(f"Wrote {bytes_written} bytes to serial port")
        elif self._serial:
            logger.warning("Serial port not open")
        else:
            logger.info("No serial port configured")

        # Broadcast via WebSocket for UI display
        self._broadcast_nmea(sentences)

    def _broadcast_nmea(self, sentences: list[str]) -> None:
        """Broadcast NMEA sentences via WebSocket."""
        if self._ws_manager and self._event_loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._ws_manager.broadcast(
                        {"type": "nmea_output", "sentences": sentences}
                    ),
                    self._event_loop,
                )
            except Exception as e:
                logger.debug(f"Failed to broadcast NMEA: {e}")

    def get_state(self) -> Optional[dict]:
        """Get current receiver state."""
        if self._receiver:
            return {
                "is_connected": self._receiver.state.is_connected,
                "packet_count": self._receiver.state.packet_count,
                "sender_address": self._receiver.state.sender_address,
            }
        return None


# Singleton instance
_receiver_runner: Optional[ReceiverRunner] = None
_receiver_lock = threading.Lock()


def get_receiver_runner() -> ReceiverRunner:
    """Get singleton receiver runner instance."""
    global _receiver_runner
    if _receiver_runner is None:
        with _receiver_lock:
            if _receiver_runner is None:
                _receiver_runner = ReceiverRunner()
    return _receiver_runner
