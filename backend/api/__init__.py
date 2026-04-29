# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# __init__.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""API route modules."""

from .auth_routes import router as auth_router
from .control_routes import router as control_router
from .config_routes import router as config_router
from .serial_routes import router as serial_router
from .ws_routes import router as ws_router
from .airport_routes import router as airport_router

__all__ = [
    "auth_router",
    "control_router",
    "config_router",
    "serial_router",
    "ws_router",
    "airport_router",
]
