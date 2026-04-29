# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# serial_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Serial device API routes."""

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_current_user
from ..serial_manager import list_serial_ports
from ..state import get_app_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/serial", tags=["serial"])


class SelectDeviceRequest(BaseModel):
    device: str


@router.get("/devices")
async def list_devices(user: str = Depends(get_current_user)) -> dict:
    """List available serial devices."""
    devices = list_serial_ports()
    logger.info(f"Found {len(devices)} USB serial devices: {devices}")
    return {"devices": devices}


@router.post("/select")
async def select_device(
    request: SelectDeviceRequest,
    user: str = Depends(get_current_user),
) -> dict:
    """Select serial device to use."""
    state = get_app_state()
    state.serial.device = request.device
    logger.info(f"Selected serial device: {request.device}")
    return {"success": True, "device": request.device}
