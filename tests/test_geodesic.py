# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_geodesic.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for geodesic calculations."""

import pytest
from backend.nmea.geodesic import update_position


class TestUpdatePosition:
    def test_stationary(self):
        """No movement when speed is zero."""
        new_lat, new_lon = update_position(
            lat=33.1283, lon=-117.2803, speed_kts=0, heading=90, elapsed_sec=1.0
        )
        assert new_lat == pytest.approx(33.1283, abs=0.0001)
        assert new_lon == pytest.approx(-117.2803, abs=0.0001)

    def test_movement_east(self):
        """Moving east should increase longitude."""
        new_lat, new_lon = update_position(
            lat=33.0, lon=-117.0, speed_kts=60, heading=90, elapsed_sec=60
        )
        assert new_lat == pytest.approx(33.0, abs=0.01)
        assert new_lon > -117.0

    def test_movement_north(self):
        """Moving north should increase latitude."""
        new_lat, new_lon = update_position(
            lat=33.0, lon=-117.0, speed_kts=60, heading=0, elapsed_sec=60
        )
        assert new_lat > 33.0
        assert new_lon == pytest.approx(-117.0, abs=0.01)
