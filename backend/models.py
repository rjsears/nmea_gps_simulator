# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# models.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Pydantic models for API requests/responses."""

from typing import Optional, Literal
from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response payload."""

    success: bool
    message: str = ""


class GpsState(BaseModel):
    """Current GPS emulator state."""

    lat: float
    lon: float
    altitude_ft: float
    speed_kts: float
    heading: float

    # Target values for gradual transitions
    target_altitude_ft: Optional[float] = None
    target_speed_kts: Optional[float] = None
    target_heading: Optional[float] = None

    # Selected airport (for syncing across browsers)
    airport_icao: Optional[str] = None

    # Status
    is_running: bool = False
    error_message: Optional[str] = None


class ModeConfig(BaseModel):
    """Operating mode configuration."""

    standalone: bool = False
    sender: bool = False
    receiver: bool = False
    rebroadcaster: bool = False

    # USB output enabled (for standalone or receiver+USB)
    usb_output: bool = False


class NetworkConfig(BaseModel):
    """Network configuration for sender/receiver."""

    protocol: Literal["udp", "tcp"] = "udp"
    target_ip: Optional[str] = None  # For sender mode
    port: int = 12000

    # NMEA output enabled (for sender mode)
    nmea_output: bool = False

    # EFB (ForeFlight/Garmin Pilot) integration
    efb_enabled: bool = False  # Master EFB toggle
    foreflight_sim_name: Optional[str] = None  # Required when EFB enabled
    foreflight_broadcast: bool = False  # Broadcast mode
    efb_ip_enabled: bool = False  # Send to specific IP addresses
    efb_target_ips: Optional[str] = (
        None  # Comma-separated IPs or ranges (e.g., 10.0.0.5, 10.0.0.10-10.0.0.20)
    )
    # Legacy fields (kept for backward compatibility)
    garmin_enabled: bool = False
    garmin_ips: Optional[str] = None

    # Rebroadcaster settings
    rebroadcast_usb: bool = False  # Output to USB serial
    rebroadcast_udp: bool = False  # Retransmit via UDP
    rebroadcast_udp_ip: Optional[str] = None  # Target IP for UDP retransmit
    rebroadcast_udp_port: int = (
        12001  # Port for UDP retransmit (must differ from listen port)
    )

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        return v.lower()


class SerialConfig(BaseModel):
    """Serial port configuration."""

    device: Optional[str] = None
    baudrate: int = 115200


class NmeaConfig(BaseModel):
    """NMEA sentence configuration."""

    # Required (always true)
    gpgga: bool = True
    gprmc: bool = True

    # Optional
    gpgll: bool = False
    gpgsa: bool = False
    gpgsv: bool = False
    gphdt: bool = False
    gpvtg: bool = False
    gpzda: bool = False

    def get_enabled_sentences(self) -> set[str]:
        """Get set of enabled sentence types."""
        sentences = {"GPGGA", "GPRMC"}  # Always required
        if self.gpgll:
            sentences.add("GPGLL")
        if self.gpgsa:
            sentences.add("GPGSA")
        if self.gpgsv:
            sentences.add("GPGSV")
        if self.gphdt:
            sentences.add("GPHDT")
        if self.gpvtg:
            sentences.add("GPVTG")
        if self.gpzda:
            sentences.add("GPZDA")
        return sentences


class ControlRequest(BaseModel):
    """Request to start/stop emulator."""

    action: Literal["start", "stop"]


class StatusResponse(BaseModel):
    """Full status response."""

    gps: GpsState
    modes: ModeConfig
    network: NetworkConfig
    serial: SerialConfig
    nmea: NmeaConfig

    # Connection status
    serial_connected: bool = False
    network_connected: bool = False
    packets_sent: int = 0
    packets_received: int = 0


class PositionUpdate(BaseModel):
    """Position update request."""

    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude_ft: Optional[float] = None
    speed_kts: Optional[float] = None
    heading: Optional[float] = None

    # Selected airport ICAO code
    airport_icao: Optional[str] = None

    # Format for position input
    position_format: Literal["decimal", "degrees_minutes"] = "decimal"
