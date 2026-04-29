# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_api.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.auth import SESSION_COOKIE_NAME
from backend.state import reset_app_state


@pytest.fixture
def client():
    reset_app_state()
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """Client with authenticated session."""
    with patch("backend.auth.get_settings") as mock:
        mock.return_value.username = "admin"
        mock.return_value.password = "test"

        response = client.post(
            "/api/auth/login", json={"username": "admin", "password": "test"}
        )
        assert response.status_code == 200

    return client


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAuthRoutes:
    """Tests for authentication endpoints."""

    def test_login_success(self, client):
        with patch("backend.auth.get_settings") as mock:
            mock.return_value.username = "admin"
            mock.return_value.password = "test"

            response = client.post(
                "/api/auth/login", json={"username": "admin", "password": "test"}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True
            assert SESSION_COOKIE_NAME in response.cookies

    def test_login_failure(self, client):
        with patch("backend.auth.get_settings") as mock:
            mock.return_value.username = "admin"
            mock.return_value.password = "test"

            response = client.post(
                "/api/auth/login", json={"username": "admin", "password": "wrong"}
            )

            assert response.status_code == 200
            assert response.json()["success"] is False

    def test_logout(self, auth_client):
        response = auth_client.post("/api/auth/logout")
        assert response.status_code == 200

    def test_check_auth_authenticated(self, auth_client):
        response = auth_client.get("/api/auth/check")
        assert response.status_code == 200
        assert response.json()["authenticated"] is True

    def test_check_auth_unauthenticated(self, client):
        response = client.get("/api/auth/check")
        assert response.status_code == 200
        assert response.json()["authenticated"] is False


class TestStatusRoutes:
    """Tests for status endpoints."""

    def test_get_status_unauthorized(self, client):
        response = client.get("/api/status")
        assert response.status_code == 401

    def test_get_status(self, auth_client):
        with patch("backend.state.get_settings") as mock:
            mock.return_value.default_lat = 33.1283
            mock.return_value.default_lon = -117.2803
            mock.return_value.default_alt_ft = 0
            mock.return_value.default_airspeed_kts = 0
            mock.return_value.default_heading = 360
            mock.return_value.serial_baudrate = 115200
            mock.return_value.foreflight_sim_name = "LOFT GPS"

            response = auth_client.get("/api/status")
            assert response.status_code == 200
            data = response.json()
            assert "gps" in data
            assert "modes" in data


class TestSerialRoutes:
    """Tests for serial device endpoints."""

    def test_list_devices(self, auth_client):
        with patch("backend.api.serial_routes.list_serial_ports") as mock:
            mock.return_value = ["/dev/ttyUSB0", "/dev/ttyACM0"]

            response = auth_client.get("/api/serial/devices")

            assert response.status_code == 200
            assert response.json()["devices"] == ["/dev/ttyUSB0", "/dev/ttyACM0"]
