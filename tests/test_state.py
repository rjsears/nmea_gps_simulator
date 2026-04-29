# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_state.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for application state manager."""

import pytest
from unittest.mock import patch
from backend.state import AppState


class TestAppState:
    """Tests for AppState class."""

    @pytest.fixture
    def mock_settings(self):
        with patch("backend.state.get_settings") as mock:
            mock.return_value.default_lat = 33.1283
            mock.return_value.default_lon = -117.2803
            mock.return_value.default_alt_ft = 0
            mock.return_value.default_airspeed_kts = 0
            mock.return_value.default_heading = 360
            mock.return_value.altitude_rate_ft_per_2sec = 1000
            mock.return_value.airspeed_rate_kts_per_sec = 30
            mock.return_value.heading_rate_deg_per_sec = 3
            mock.return_value.serial_baudrate = 115200
            mock.return_value.foreflight_sim_name = "LOFT GPS"
            yield mock

    def test_initial_state(self, mock_settings):
        state = AppState()
        assert state.is_running is False
        assert state.modes.standalone is False
        assert state.lat == 33.1283
        assert state.lon == -117.2803

    def test_set_position(self, mock_settings):
        state = AppState()
        state.set_position(lat=40.0, lon=-74.0)
        assert state.lat == 40.0
        assert state.lon == -74.0

    def test_set_targets(self, mock_settings):
        state = AppState()
        state.set_targets(altitude_ft=10000, speed_kts=200)
        assert state.target_altitude_ft == 10000
        assert state.target_speed_kts == 200

    def test_update_modes(self, mock_settings):
        state = AppState()
        state.update_modes(standalone=True, sender=True)
        assert state.modes.standalone is True
        assert state.modes.sender is True
        assert state.modes.receiver is False

    def test_to_gps_state(self, mock_settings):
        state = AppState()
        state.set_position(lat=35.0, lon=-118.0)
        gps_state = state.to_gps_state()
        assert gps_state.lat == 35.0
        assert gps_state.lon == -118.0
        assert gps_state.is_running is False

    def test_to_status_response(self, mock_settings):
        state = AppState()
        resp = state.to_status_response()
        assert resp.gps.lat == state.lat
        assert resp.modes.standalone == state.modes.standalone
        assert resp.serial_connected is False
