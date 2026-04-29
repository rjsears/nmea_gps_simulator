# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# emulator.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""GPS Emulator runner - handles the main output loop."""

import asyncio
import logging
import threading
import time
from typing import Optional

from .nmea.engine import NmeaEngine
from .serial_manager import SerialManager
from .network.sender import NetworkSender
from .network.foreflight import EFBSender
from .config import get_settings

logger = logging.getLogger(__name__)


class EmulatorRunner:
    """Runs the GPS emulator output loop in a background thread.

    Generates NMEA sentences at 1Hz and writes them to the serial port.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._engine: Optional[NmeaEngine] = None
        self._serial: Optional[SerialManager] = None
        self._sender: Optional[NetworkSender] = None
        self._foreflight_sender: Optional[EFBSender] = None
        self._running = False
        self._ws_manager = None
        self._event_loop = None
        self._serial_device = None

    @property
    def is_running(self) -> bool:
        return self._running

    def set_ws_manager(self, ws_manager, event_loop):
        """Set the WebSocket manager for broadcasting output."""
        self._ws_manager = ws_manager
        self._event_loop = event_loop

    def start(
        self,
        lat: float,
        lon: float,
        altitude_ft: float,
        speed_kts: float,
        heading: float,
        serial_device: Optional[str],
        enabled_sentences: set[str],
        sender_config: Optional[dict] = None,
        foreflight_config: Optional[dict] = None,
        baudrate: int = 115200,
    ) -> None:
        """Start the emulator output loop.

        Args:
            sender_config: Optional dict with target_ip, port, protocol for sender mode
            foreflight_config: Optional dict with enabled, sim_name for ForeFlight output
        """
        if self._running:
            logger.warning("Emulator already running")
            return

        settings = get_settings()
        self._serial_device = serial_device

        logger.info(
            f"Starting emulator with: lat={lat}, lon={lon}, alt={altitude_ft}ft, speed={speed_kts}kts, heading={heading}"
        )
        logger.info(f"Serial device: {serial_device}")
        logger.info(f"Enabled sentences: {enabled_sentences}")
        logger.info(f"Sender config: {sender_config}")

        # Create NMEA engine
        self._engine = NmeaEngine(
            lat=lat,
            lon=lon,
            altitude_ft=altitude_ft,
            speed_kts=speed_kts,
            heading=heading,
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
        else:
            logger.warning(
                "No serial device specified - NMEA output will only be shown in UI"
            )

        # Create network sender if in sender mode with NMEA output enabled
        if (
            sender_config
            and sender_config.get("target_ip")
            and sender_config.get("nmea_output", True)
        ):
            self._sender = NetworkSender(
                target_ip=sender_config["target_ip"],
                port=sender_config.get("port", 12000),
                protocol=sender_config.get("protocol", "udp"),
            )
            logger.info(
                f"Network sender configured: {sender_config['target_ip']}:{sender_config.get('port', 12000)} ({sender_config.get('protocol', 'udp')})"
            )

        # Create EFB (ForeFlight/Garmin Pilot) sender if enabled
        if foreflight_config and (
            foreflight_config.get("broadcast") or foreflight_config.get("target_ips")
        ):
            sim_name = foreflight_config.get("sim_name", "LOFT GPS")
            broadcast = foreflight_config.get("broadcast", False)
            target_ips = foreflight_config.get("target_ips", [])
            self._foreflight_sender = EFBSender(
                sim_name=sim_name,
                broadcast=broadcast,
                target_ips=target_ips,
            )
            destinations = []
            if broadcast:
                destinations.append("broadcast (ForeFlight)")
            for ip in target_ips:
                destinations.append(f"{ip} (Garmin Pilot)")
            logger.info(
                f"EFB sender configured: sim_name='{sim_name}', destinations={destinations}"
            )

        self._stop_event.clear()
        self._running = True

        # Start background thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Emulator background thread started")

    def stop(self) -> None:
        """Stop the emulator output loop."""
        if not self._running:
            return

        logger.info("Stopping emulator...")
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._serial:
            try:
                self._serial.close()
                logger.info(f"Serial port closed: {self._serial_device}")
            except Exception as e:
                logger.warning(f"Error closing serial port: {e}")
            self._serial = None

        if self._sender:
            try:
                self._sender.close()
                logger.info("Network sender closed")
            except Exception as e:
                logger.warning(f"Error closing network sender: {e}")
            self._sender = None

        if self._foreflight_sender:
            try:
                self._foreflight_sender.close()
                logger.info("ForeFlight sender closed")
            except Exception as e:
                logger.warning(f"Error closing ForeFlight sender: {e}")
            self._foreflight_sender = None

        self._engine = None
        self._running = False
        self._serial_device = None
        logger.info("Emulator stopped")

    def set_target_altitude(self, altitude_ft: float) -> None:
        """Set target altitude for gradual transition."""
        if self._engine:
            self._engine.set_target_altitude(altitude_ft)

    def set_target_speed(self, speed_kts: float) -> None:
        """Set target speed for gradual transition."""
        if self._engine:
            self._engine.set_target_speed(speed_kts)

    def set_target_heading(self, heading: float) -> None:
        """Set target heading for gradual transition."""
        if self._engine:
            self._engine.set_target_heading(heading)

    def get_current_state(self) -> Optional[dict]:
        """Get current position/speed/heading state."""
        if self._engine:
            return self._engine.get_state()
        return None

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

    def _run_loop(self) -> None:
        """Main output loop - runs at 1Hz."""
        last_time = time.time()
        loop_count = 0

        logger.info("Emulator loop starting...")

        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - last_time
                last_time = current_time
                loop_count += 1

                # Update position based on speed and heading
                self._engine.tick(elapsed)

                # Generate NMEA sentences
                sentences = self._engine.generate()

                # Log first few iterations to verify output
                if loop_count <= 3:
                    logger.info(
                        f"Loop {loop_count}: Generated {len(sentences)} sentences"
                    )
                    for s in sentences:
                        logger.info(f"  {s.strip()}")

                # Write to serial port
                if self._serial:
                    if self._serial.is_open:
                        bytes_written = 0
                        for sentence in sentences:
                            bytes_written += self._serial.write(sentence)
                        if loop_count <= 3:
                            logger.info(f"Wrote {bytes_written} bytes to serial port")
                    else:
                        logger.warning("Serial port is not open!")
                else:
                    if loop_count <= 3:
                        logger.info("No serial port configured")

                # Send via network if sender is configured
                if self._sender:
                    state = self._engine.get_state()
                    # Round to whole numbers for network packet
                    heading_rounded = round(state["heading"])
                    if heading_rounded == 0:
                        heading_rounded = 360
                    packet = self._sender.create_packet(
                        lat=state["lat"],
                        lon=state["lon"],
                        alt_ft=round(state["altitude_ft"]),
                        speed_kts=round(state["speed_kts"]),
                        heading=heading_rounded,
                    )
                    self._sender.send(packet)
                    if loop_count <= 3:
                        logger.info(f"Sent network packet: {packet[:80]}...")

                # Send ForeFlight XGPS if configured
                if self._foreflight_sender:
                    state = self._engine.get_state()
                    self._foreflight_sender.send(
                        lat=state["lat"],
                        lon=state["lon"],
                        altitude_ft=state["altitude_ft"],
                        heading=state["heading"],
                        speed_kts=state["speed_kts"],
                    )
                    if loop_count <= 3:
                        msg = self._foreflight_sender.create_xgps_message(
                            lat=state["lat"],
                            lon=state["lon"],
                            altitude_ft=state["altitude_ft"],
                            heading=state["heading"],
                            speed_kts=state["speed_kts"],
                        )
                        logger.info(f"Sent ForeFlight XGPS: {msg}")

                # Broadcast via WebSocket for UI display
                self._broadcast_nmea(sentences)

                # Sleep for remainder of 1 second interval
                sleep_time = 1.0 - (time.time() - current_time)
                if sleep_time > 0:
                    self._stop_event.wait(sleep_time)

            except Exception as e:
                logger.error(f"Error in emulator loop: {e}", exc_info=True)
                self._stop_event.wait(1.0)

        logger.info(f"Emulator loop ended after {loop_count} iterations")


# Singleton instance
_emulator: Optional[EmulatorRunner] = None
_emulator_lock = threading.Lock()


def get_emulator() -> EmulatorRunner:
    """Get singleton emulator instance."""
    global _emulator
    if _emulator is None:
        with _emulator_lock:
            if _emulator is None:
                _emulator = EmulatorRunner()
    return _emulator
