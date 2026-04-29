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

"""NMEA sentence generation package."""

from .checksum import calculate_checksum, format_sentence
from .engine import NmeaEngine
from .geodesic import update_position
from .sentences import GPGGA, GPGLL, GPGSA, GPGSV, GPHDT, GPRMC, GPVTG, GPZDA
from .transitions import GradualTransition, HeadingTransition

__all__ = [
    "calculate_checksum",
    "format_sentence",
    "NmeaEngine",
    "update_position",
    "GPGGA",
    "GPGLL",
    "GPGSA",
    "GPGSV",
    "GPHDT",
    "GPRMC",
    "GPVTG",
    "GPZDA",
    "GradualTransition",
    "HeadingTransition",
]
