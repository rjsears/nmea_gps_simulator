# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_airport_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for airport API routes."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.state import reset_app_state


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


class TestAirportLookup:
    """Tests for airport lookup endpoint."""

    def test_lookup_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/airports/lookup/KLAX")
        assert response.status_code == 401

    def test_lookup_valid_airport(self, auth_client):
        """Should return airport data for valid ICAO."""
        response = auth_client.get("/api/airports/lookup/KLAX")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["airport"]["icao"] == "KLAX"
        assert "lat" in data["airport"]
        assert "lon" in data["airport"]

    def test_lookup_invalid_airport(self, auth_client):
        """Should return error for invalid ICAO."""
        response = auth_client.get("/api/airports/lookup/XXXX")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]


class TestAirportSearch:
    """Tests for airport search endpoint."""

    def test_search_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/airports/search?q=LAX")
        assert response.status_code == 401

    def test_search_by_icao(self, auth_client):
        """Should find airports by ICAO code."""
        response = auth_client.get("/api/airports/search?q=LAX")
        assert response.status_code == 200
        data = response.json()
        assert "airports" in data
        assert len(data["airports"]) > 0

    def test_search_by_name(self, auth_client):
        """Should find airports by name."""
        response = auth_client.get("/api/airports/search?q=Los%20Angeles")
        assert response.status_code == 200
        data = response.json()
        assert len(data["airports"]) > 0

    def test_search_with_limit(self, auth_client):
        """Should respect limit parameter."""
        response = auth_client.get("/api/airports/search?q=International&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["airports"]) <= 5


class TestAirportList:
    """Tests for airport list endpoint."""

    def test_list_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/airports/list")
        assert response.status_code == 401

    def test_list_airports(self, auth_client):
        """Should return all airports."""
        response = auth_client.get("/api/airports/list")
        assert response.status_code == 200
        data = response.json()
        assert "airports" in data
        assert len(data["airports"]) > 50
