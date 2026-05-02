# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# airports.py
#
# Fleet Dashboard - Airport lookup
# Imports airport data from main emulator project
#
# Richard J. Sears
# richardjsears@protonmail.com
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Airport database and closest airport lookup."""

import math
from typing import Optional

# Import the full airport database
# This file should be copied from the main emulator project during Docker build
# or symlinked for local development
try:
    from .airports_data import AIRPORTS
except ImportError:
    # Fallback: minimal set of major airports
    AIRPORTS = {
        "KJFK": ("John F. Kennedy International", 40.6413, -73.7781, 13),
        "KLAX": ("Los Angeles International", 33.9425, -118.4081, 128),
        "KORD": ("O'Hare International", 41.9742, -87.9073, 672),
        "KDFW": ("Dallas/Fort Worth International", 32.8998, -97.0403, 607),
        "KDEN": ("Denver International", 39.8561, -104.6737, 5434),
        "KATL": ("Hartsfield-Jackson Atlanta", 33.6407, -84.4277, 1026),
        "KSFO": ("San Francisco International", 37.6213, -122.3790, 13),
        "KMIA": ("Miami International", 25.7959, -80.2870, 8),
        "KSEA": ("Seattle-Tacoma International", 47.4502, -122.3088, 433),
        "KBOS": ("Boston Logan International", 42.3656, -71.0096, 20),
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in nautical miles.

    Args:
        lat1, lon1: First point coordinates (decimal degrees)
        lat2, lon2: Second point coordinates (decimal degrees)

    Returns:
        Distance in nautical miles
    """
    R = 3440.065  # Earth radius in nautical miles

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def find_closest_airport(lat: float, lon: float) -> Optional[dict]:
    """Find the closest airport to a given position.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees

    Returns:
        Dict with airport info and distance, or None if no airports
    """
    if not AIRPORTS:
        return None

    closest = None
    min_distance = float("inf")

    for icao, (name, apt_lat, apt_lon, elev) in AIRPORTS.items():
        distance = haversine_distance(lat, lon, apt_lat, apt_lon)
        if distance < min_distance:
            min_distance = distance
            closest = {
                "airport": {
                    "icao": icao,
                    "name": name,
                    "lat": apt_lat,
                    "lon": apt_lon,
                    "elevation_ft": elev,
                },
                "distance_nm": distance,
            }

    return closest
