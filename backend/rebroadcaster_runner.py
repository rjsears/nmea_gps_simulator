# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# rebroadcaster_runner.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 27th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Rebroadcaster runner - receives GPS data and rebroadcasts to multiple outputs."""

import asyncio
import logging
import socket
import threading
from typing import Optional

from .network.receiver import NetworkReceiver
from .network.foreflight import EFBSender, parse_ip_list
from .nmea.engine import NmeaEngine
from .serial_manager import SerialManager
from .config import get_settings

logger = logging.getLogger(__name__)


class RebroadcasterRunner:
    """Runs the rebroadcaster mode - receives GPS data and rebroadcasts to multiple outputs.

    Receives GPS JSON packets from network and can output to:
    - USB serial port (NMEA)
    - EFB apps (ForeFlight broadcast and/or Garmin Pilot IPs)
    - UDP retransmit (different IP/port)
    """

    def __init__(self):
        self._receiver: Optional[NetworkReceiver] = None
        self._engine: Optional[NmeaEngine] = None
        self._serial: Optional[SerialManager] = None
        self._efb_sender: Optional[EFBSender] = None
        self._udp_socket: Optional[socket.socket] = None
        self._running = False
        self._ws_manager = None
        self._event_loop = None
        self._serial_device = None
        self._enabled_sentences: set[str] = set()
        self._udp_retransmit_ip: Optional[str] = None
        self._udp_retransmit_port: int = 12001

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
        # USB output options
        rebroadcast_usb: bool = False,
        serial_device: Optional[str] = None,
        baudrate: int = 115200,
        enabled_sentences: Optional[set[str]] = None,
        # EFB output options
        efb_enabled: bool = False,
        foreflight_broadcast: bool = False,
        efb_ip_enabled: bool = False,
        efb_target_ips: Optional[str] = None,
        foreflight_sim_name: str = "LOFT GPS",
        # UDP retransmit options
        rebroadcast_udp: bool = False,
        rebroadcast_udp_ip: Optional[str] = None,
        rebroadcast_udp_port: int = 12001,
    ) -> None:
        """Start the rebroadcaster.

        Args:
            port: Network port to listen on
            rebroadcast_usb: Enable USB serial output
            serial_device: Serial device path for NMEA output
            baudrate: Serial baud rate
            enabled_sentences: Set of enabled NMEA sentence types
            efb_enabled: Enable EFB output
            foreflight_broadcast: Send to broadcast address
            efb_ip_enabled: Send to specific IP addresses
            efb_target_ips: Comma-separated IPs or ranges
            foreflight_sim_name: Simulator name for EFB apps
            rebroadcast_udp: Enable UDP retransmit
            rebroadcast_udp_ip: Target IP for UDP retransmit
            rebroadcast_udp_port: Target port for UDP retransmit
        """
        if self._running:
            logger.warning("Rebroadcaster already running")
            return

        settings = get_settings()
        self._serial_device = serial_device
        self._enabled_sentences = enabled_sentences or {"GPGGA", "GPRMC"}

        logger.info(f"Starting rebroadcaster on port {port}")

        # Create NMEA engine (will be updated when packets arrive)
        self._engine = NmeaEngine(
            lat=0,
            lon=0,
            altitude_ft=0,
            speed_kts=0,
            heading=0,
            enabled_sentences=self._enabled_sentences,
            altitude_rate_ft_per_2sec=settings.altitude_rate_ft_per_2sec,
            airspeed_rate_kts_per_sec=settings.airspeed_rate_kts_per_sec,
            heading_rate_deg_per_sec=settings.heading_rate_deg_per_sec,
        )

        # Open serial port if USB output enabled
        if rebroadcast_usb and serial_device:
            try:
                logger.info(f"Opening serial port: {serial_device} at {baudrate} baud")
                self._serial = SerialManager(serial_device, baudrate=baudrate)
                self._serial.open()
                logger.info(f"Serial port opened successfully: {serial_device}")
            except Exception as e:
                logger.error(f"Failed to open serial port {serial_device}: {e}")
                raise RuntimeError(f"Failed to open serial port: {e}")

        # Set up EFB sender if enabled
        logger.info(
            f"EFB config: efb_enabled={efb_enabled}, foreflight_broadcast={foreflight_broadcast}, efb_ip_enabled={efb_ip_enabled}, efb_target_ips={efb_target_ips}, sim_name={foreflight_sim_name}"
        )
        if efb_enabled and (foreflight_broadcast or efb_ip_enabled):
            target_ips = []
            if efb_ip_enabled and efb_target_ips:
                target_ips = parse_ip_list(efb_target_ips)

            self._efb_sender = EFBSender(
                sim_name=foreflight_sim_name,
                broadcast=foreflight_broadcast,
                target_ips=target_ips,
            )
            logger.info(
                f"EFB sender configured: broadcast={foreflight_broadcast}, ips={target_ips}, sim_name={foreflight_sim_name}"
            )
        else:
            logger.info(
                "EFB sender NOT configured - missing efb_enabled or sub-options"
            )

        # Set up UDP retransmit socket if enabled
        if rebroadcast_udp and rebroadcast_udp_ip:
            self._udp_retransmit_ip = rebroadcast_udp_ip
            self._udp_retransmit_port = rebroadcast_udp_port
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(
                f"UDP retransmit configured: {rebroadcast_udp_ip}:{rebroadcast_udp_port}"
            )

        # Create and start network receiver
        self._receiver = NetworkReceiver(
            port=port,
            protocol="udp",
            on_packet=self._handle_packet,
        )
        self._receiver.start()
        self._running = True
        logger.info("Rebroadcaster started")

    def stop(self) -> None:
        """Stop the rebroadcaster."""
        if not self._running:
            return

        logger.info("Stopping rebroadcaster...")

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

        if self._efb_sender:
            self._efb_sender.close()
            self._efb_sender = None

        if self._udp_socket:
            self._udp_socket.close()
            self._udp_socket = None

        self._engine = None
        self._running = False
        self._serial_device = None
        self._udp_retransmit_ip = None
        logger.info("Rebroadcaster stopped")

    def _handle_packet(self, data: dict) -> None:
        """Handle received GPS packet - rebroadcast to all configured outputs."""
        if not self._engine:
            logger.warning("No engine configured, ignoring packet")
            return

        logger.debug(f"Received packet: lat={data['lat']}, lon={data['lon']}")

        lat = data["lat"]
        lon = data["lon"]
        altitude_ft = data["alt_ft"]
        speed_kts = data["speed_kts"]
        heading = data["heading"]

        # Update engine with received position
        self._engine.update_position(
            lat=lat,
            lon=lon,
            altitude_ft=altitude_ft,
            speed_kts=speed_kts,
            heading=heading,
        )

        # Generate NMEA sentences
        sentences = self._engine.generate()

        # Write to serial port if configured
        if self._serial and self._serial.is_open:
            bytes_written = 0
            for sentence in sentences:
                bytes_written += self._serial.write(sentence)
            logger.debug(f"Wrote {bytes_written} bytes to serial port")

        # Send to EFB apps if configured
        if self._efb_sender:
            logger.info(
                f"Sending to EFB: lat={lat}, lon={lon}, alt={altitude_ft}, hdg={heading}, spd={speed_kts}"
            )
            self._efb_sender.send(
                lat=lat,
                lon=lon,
                altitude_ft=altitude_ft,
                heading=heading,
                speed_kts=speed_kts,
            )
        else:
            logger.debug("No EFB sender configured")

        # UDP retransmit if configured
        if self._udp_socket and self._udp_retransmit_ip:
            try:
                # Retransmit the original GPS JSON data
                import json

                payload = json.dumps(data).encode()
                self._udp_socket.sendto(
                    payload, (self._udp_retransmit_ip, self._udp_retransmit_port)
                )
                logger.debug(
                    f"UDP retransmit to {self._udp_retransmit_ip}:{self._udp_retransmit_port}"
                )
            except Exception as e:
                logger.error(f"UDP retransmit failed: {e}")

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
        """Get current rebroadcaster state."""
        if self._receiver:
            return {
                "is_connected": self._receiver.state.is_connected,
                "packet_count": self._receiver.state.packet_count,
                "sender_address": self._receiver.state.sender_address,
            }
        return None


# Singleton instance
_rebroadcaster_runner: Optional[RebroadcasterRunner] = None
_rebroadcaster_lock = threading.Lock()


def get_rebroadcaster_runner() -> RebroadcasterRunner:
    """Get singleton rebroadcaster runner instance."""
    global _rebroadcaster_runner
    if _rebroadcaster_runner is None:
        with _rebroadcaster_lock:
            if _rebroadcaster_runner is None:
                _rebroadcaster_runner = RebroadcasterRunner()
    return _rebroadcaster_runner
