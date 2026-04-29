# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# config_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Configuration API routes."""

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..models import ModeConfig, NetworkConfig, NmeaConfig, SerialConfig
from ..state import get_app_state

router = APIRouter(prefix="/api/config", tags=["config"])


@router.post("/modes")
async def update_modes(
    config: ModeConfig,
    user: str = Depends(get_current_user),
) -> dict:
    """Update operating modes."""
    state = get_app_state()
    state.update_modes(
        standalone=config.standalone,
        sender=config.sender,
        receiver=config.receiver,
        rebroadcaster=config.rebroadcaster,
        usb_output=config.usb_output,
    )
    return {"success": True}


@router.post("/network")
async def update_network(
    config: NetworkConfig,
    user: str = Depends(get_current_user),
) -> dict:
    """Update network configuration."""
    state = get_app_state()
    state.network = config
    return {"success": True}


@router.post("/nmea")
async def update_nmea(
    config: NmeaConfig,
    user: str = Depends(get_current_user),
) -> dict:
    """Update NMEA sentence configuration."""
    state = get_app_state()
    state.nmea = config
    return {"success": True}


@router.post("/serial")
async def update_serial(
    config: SerialConfig,
    user: str = Depends(get_current_user),
) -> dict:
    """Update serial port configuration."""
    state = get_app_state()
    state.serial = config
    return {"success": True}
