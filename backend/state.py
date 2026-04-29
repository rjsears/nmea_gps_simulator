# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# state.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Application state manager."""

import threading
from typing import Optional

from .config import get_settings
from .models import (
    GpsState,
    ModeConfig,
    NetworkConfig,
    SerialConfig,
    NmeaConfig,
    StatusResponse,
)


class AppState:
    """Central application state manager.

    Holds all configuration and runtime state for the GPS emulator.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        settings = get_settings()

        self._lock = threading.RLock()

        # Position state
        self.lat = settings.default_lat
        self.lon = settings.default_lon
        self.altitude_ft = settings.default_alt_ft
        self.speed_kts = settings.default_airspeed_kts
        self.heading = settings.default_heading

        # Targets for gradual transitions
        self.target_altitude_ft = self.altitude_ft
        self.target_speed_kts = self.speed_kts
        self.target_heading = self.heading

        # Selected airport (for syncing across browsers)
        self.airport_icao: Optional[str] = None

        # Running state
        self.is_running = False
        self.error_message: Optional[str] = None

        # Configuration
        self.modes = ModeConfig()
        self.network = NetworkConfig(foreflight_sim_name=settings.foreflight_sim_name)
        self.serial = SerialConfig(baudrate=settings.serial_baudrate)
        self.nmea = NmeaConfig()

        # Runtime components (created on start) - typed as Any to avoid circular imports
        self.engine = None
        self.serial_manager = None
        self.sender = None
        self.receiver = None

        # Statistics
        self.packets_sent = 0
        self.packets_received = 0

    def set_position(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        altitude_ft: Optional[float] = None,
        speed_kts: Optional[float] = None,
        heading: Optional[float] = None,
        airport_icao: Optional[str] = None,
    ) -> None:
        """Update position values."""
        with self._lock:
            if lat is not None:
                self.lat = lat
            if lon is not None:
                self.lon = lon
            if altitude_ft is not None:
                self.altitude_ft = altitude_ft
            if speed_kts is not None:
                self.speed_kts = speed_kts
            if heading is not None:
                self.heading = heading
            if airport_icao is not None:
                self.airport_icao = airport_icao

    def set_targets(
        self,
        altitude_ft: Optional[float] = None,
        speed_kts: Optional[float] = None,
        heading: Optional[float] = None,
    ) -> None:
        """Set target values for gradual transitions."""
        with self._lock:
            if altitude_ft is not None:
                self.target_altitude_ft = altitude_ft
                if self.engine:
                    self.engine.set_target_altitude(altitude_ft)
            if speed_kts is not None:
                self.target_speed_kts = speed_kts
                if self.engine:
                    self.engine.set_target_speed(speed_kts)
            if heading is not None:
                self.target_heading = heading % 360
                if self.engine:
                    self.engine.set_target_heading(heading)

    def update_modes(
        self,
        standalone: Optional[bool] = None,
        sender: Optional[bool] = None,
        receiver: Optional[bool] = None,
        rebroadcaster: Optional[bool] = None,
        usb_output: Optional[bool] = None,
    ) -> None:
        """Update operating modes."""
        with self._lock:
            if standalone is not None:
                self.modes.standalone = standalone
            if sender is not None:
                self.modes.sender = sender
            if receiver is not None:
                self.modes.receiver = receiver
            if rebroadcaster is not None:
                self.modes.rebroadcaster = rebroadcaster
            if usb_output is not None:
                self.modes.usb_output = usb_output

    def to_gps_state(self) -> GpsState:
        """Convert to GpsState model."""
        with self._lock:
            return GpsState(
                lat=self.lat,
                lon=self.lon,
                altitude_ft=self.altitude_ft,
                speed_kts=self.speed_kts,
                heading=self.heading,
                target_altitude_ft=self.target_altitude_ft,
                target_speed_kts=self.target_speed_kts,
                target_heading=self.target_heading,
                airport_icao=self.airport_icao,
                is_running=self.is_running,
                error_message=self.error_message,
            )

    def to_status_response(self) -> StatusResponse:
        """Convert to full status response."""
        with self._lock:
            serial_connected = False
            if self.serial_manager and hasattr(self.serial_manager, "is_connected"):
                serial_connected = self.serial_manager.is_connected

            network_connected = False
            # Check receiver connection status
            if self.receiver and hasattr(self.receiver, "state"):
                network_connected = self.receiver.state.is_connected
            # For sender mode, show connected if emulator is running with sender configured
            if self.modes.sender and self.is_running and self.sender:
                network_connected = True

            return StatusResponse(
                gps=self.to_gps_state(),
                modes=self.modes,
                network=self.network,
                serial=self.serial,
                nmea=self.nmea,
                serial_connected=serial_connected,
                network_connected=network_connected,
                packets_sent=self.packets_sent,
                packets_received=self.packets_received,
            )


# Singleton instance
_app_state: Optional[AppState] = None
_state_lock = threading.Lock()


def get_app_state() -> AppState:
    """Get singleton application state instance."""
    global _app_state
    if _app_state is None:
        with _state_lock:
            if _app_state is None:
                _app_state = AppState()
    return _app_state


def reset_app_state() -> None:
    """Reset app state (for testing)."""
    global _app_state
    with _state_lock:
        _app_state = None
