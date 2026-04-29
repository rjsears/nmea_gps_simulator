# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# airport_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Airport lookup API routes."""

import logging
from fastapi import APIRouter, Depends, Query

from ..auth import get_current_user
from ..airports import lookup_airport, search_airports, list_all_airports

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/airports", tags=["airports"])


@router.get("/lookup/{icao}")
async def get_airport(icao: str, user: str = Depends(get_current_user)) -> dict:
    """Look up airport by ICAO code."""
    airport = lookup_airport(icao)
    if airport:
        return {"success": True, "airport": airport}
    return {"success": False, "error": f"Airport '{icao}' not found"}


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    user: str = Depends(get_current_user),
) -> dict:
    """Search airports by ICAO code or name."""
    results = search_airports(q, limit=limit)
    return {"airports": results}


@router.get("/list")
async def list_airports(user: str = Depends(get_current_user)) -> dict:
    """Get list of all available airports."""
    airports = list_all_airports()
    return {"airports": airports}
