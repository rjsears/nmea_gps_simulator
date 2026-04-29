# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_models.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for API models."""

import pytest
from pydantic import ValidationError

from backend.models import (
    LoginRequest,
    LoginResponse,
    GpsState,
    ModeConfig,
    NetworkConfig,
)


class TestLoginModels:
    """Tests for login request/response models."""

    def test_login_request_valid(self):
        req = LoginRequest(username="admin", password="pass")
        assert req.username == "admin"
        assert req.password == "pass"

    def test_login_response(self):
        resp = LoginResponse(success=True, message="OK")
        assert resp.success is True


class TestGpsState:
    """Tests for GPS state model."""

    def test_gps_state_defaults(self):
        state = GpsState(
            lat=33.1283,
            lon=-117.2803,
            altitude_ft=0,
            speed_kts=0,
            heading=360,
        )
        assert state.lat == 33.1283
        assert state.is_running is False

    def test_gps_state_target_values(self):
        state = GpsState(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=90,
            target_altitude_ft=10000,
            target_speed_kts=150,
            target_heading=180,
        )
        assert state.target_altitude_ft == 10000


class TestModeConfig:
    """Tests for mode configuration."""

    def test_mode_config_defaults(self):
        cfg = ModeConfig()
        assert cfg.standalone is False
        assert cfg.sender is False
        assert cfg.receiver is False

    def test_mode_config_multiple(self):
        cfg = ModeConfig(standalone=True, sender=True)
        assert cfg.standalone is True
        assert cfg.sender is True


class TestNetworkConfig:
    """Tests for network configuration."""

    def test_network_config_sender(self):
        cfg = NetworkConfig(protocol="udp", target_ip="192.168.1.100")
        assert cfg.protocol == "udp"
        assert cfg.target_ip == "192.168.1.100"

    def test_network_config_invalid_protocol(self):
        with pytest.raises(ValidationError):
            NetworkConfig(protocol="http", target_ip="192.168.1.100")
