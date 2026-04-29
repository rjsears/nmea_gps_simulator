# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# geodesic.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""WGS84 geodesic calculations for position updates."""

from pyproj import Geod

_geod = Geod(ellps="WGS84")

KNOTS_TO_MS = 0.514444


def update_position(
    lat: float,
    lon: float,
    speed_kts: float,
    heading: float,
    elapsed_sec: float,
) -> tuple[float, float]:
    """Calculate new position based on speed and heading.

    Uses WGS84 geodesic forward calculation.

    Args:
        lat: Current latitude in decimal degrees
        lon: Current longitude in decimal degrees
        speed_kts: Ground speed in knots
        heading: True heading in degrees (0-360)
        elapsed_sec: Time elapsed in seconds

    Returns:
        Tuple of (new_lat, new_lon) in decimal degrees
    """
    if speed_kts <= 0:
        return lat, lon

    speed_ms = speed_kts * KNOTS_TO_MS
    distance_m = speed_ms * elapsed_sec

    new_lon, new_lat, _ = _geod.fwd(lon, lat, heading, distance_m)

    return new_lat, new_lon
