# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# config.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Authentication
    username: str = "admin"
    password: str = "changeme"
    bypass_auth: bool = False

    # Default position (KCRQ - McClellan-Palomar Airport)
    default_lat: float = 33.1283
    default_lon: float = -117.2803
    default_alt_ft: float = 0
    default_airspeed_kts: float = 0
    default_heading: float = 360

    # Gradual change rates
    altitude_rate_ft_per_2sec: float = 1000
    airspeed_rate_kts_per_sec: float = 30
    heading_rate_deg_per_sec: float = 3

    # Network
    network_port: int = 12000

    # Serial
    serial_baudrate: int = 115200

    # ForeFlight/EFB
    foreflight_sim_name: str = ""

    # Auto-start configuration
    # Set AUTO_START_MODE to enable automatic startup on container launch.
    # Valid values: "rebroadcaster", "sender", "receiver", "standalone"
    # To disable auto-start: don't set this variable, or set it to empty string (AUTO_START_MODE=)
    # Setting to "false" will NOT work - it must be empty or omitted to disable.
    auto_start_mode: Optional[str] = None

    # Auto-start network settings
    auto_start_listen_port: int = 12000
    auto_start_protocol: str = "udp"

    # Auto-start EFB settings
    auto_start_efb_enabled: bool = False
    auto_start_efb_broadcast: bool = False
    auto_start_efb_target_ips: Optional[str] = (
        None  # e.g., "10.200.50.10,10.200.50.20-10.200.50.30"
    )
    auto_start_efb_sim_name: Optional[str] = None

    # Auto-start USB output (for rebroadcaster)
    auto_start_usb_enabled: bool = False
    auto_start_usb_device: Optional[str] = None

    # Auto-start UDP retransmit (for rebroadcaster)
    auto_start_udp_retransmit: bool = False
    auto_start_udp_retransmit_ip: Optional[str] = None
    auto_start_udp_retransmit_port: int = 12001


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
