# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_config_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for config API routes."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.state import get_app_state, reset_app_state


@pytest.fixture
def client():
    """Create test client."""
    reset_app_state()
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """Create authenticated test client."""
    with patch("backend.auth.get_settings") as mock:
        mock.return_value.username = "admin"
        mock.return_value.password = "test"

        response = client.post(
            "/api/auth/login", json={"username": "admin", "password": "test"}
        )
        assert response.status_code == 200

    return client


class TestModeConfig:
    """Tests for mode configuration endpoint."""

    def test_update_modes_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/config/modes", json={"standalone": True})
        assert response.status_code == 401

    def test_update_modes_standalone(self, auth_client):
        """Should update standalone mode."""
        response = auth_client.post(
            "/api/config/modes",
            json={"standalone": True, "sender": False, "receiver": False},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        state = get_app_state()
        assert state.modes.standalone is True

    def test_update_modes_sender(self, auth_client):
        """Should update sender mode."""
        response = auth_client.post(
            "/api/config/modes",
            json={"standalone": False, "sender": True, "receiver": False},
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.modes.sender is True

    def test_update_modes_receiver(self, auth_client):
        """Should update receiver mode."""
        response = auth_client.post(
            "/api/config/modes",
            json={"standalone": False, "sender": False, "receiver": True},
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.modes.receiver is True

    def test_update_modes_usb_output(self, auth_client):
        """Should update USB output flag."""
        response = auth_client.post(
            "/api/config/modes",
            json={
                "standalone": False,
                "sender": True,
                "receiver": False,
                "usb_output": True,
            },
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.modes.usb_output is True


class TestNetworkConfig:
    """Tests for network configuration endpoint."""

    def test_update_network_requires_auth(self, client):
        """Should require authentication."""
        response = client.post(
            "/api/config/network", json={"protocol": "udp", "port": 12000}
        )
        assert response.status_code == 401

    def test_update_network(self, auth_client):
        """Should update network configuration."""
        response = auth_client.post(
            "/api/config/network",
            json={
                "protocol": "tcp",
                "target_ip": "192.168.1.100",
                "port": 15000,
            },
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.network.protocol == "tcp"
        assert state.network.target_ip == "192.168.1.100"
        assert state.network.port == 15000


class TestNmeaConfig:
    """Tests for NMEA configuration endpoint."""

    def test_update_nmea_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/config/nmea", json={"gpgga": True, "gprmc": True})
        assert response.status_code == 401

    def test_update_nmea(self, auth_client):
        """Should update NMEA configuration."""
        response = auth_client.post(
            "/api/config/nmea",
            json={
                "gpgga": True,
                "gprmc": True,
                "gpgll": True,
                "gpgsa": True,
                "gpgsv": False,
                "gphdt": True,
                "gpvtg": False,
                "gpzda": True,
            },
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.nmea.gpgll is True
        assert state.nmea.gpgsa is True
        assert state.nmea.gphdt is True
        assert state.nmea.gpzda is True
