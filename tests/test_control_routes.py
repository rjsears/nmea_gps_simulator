# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_control_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for control API routes."""

import pytest
from unittest.mock import Mock, patch
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


@pytest.fixture
def reset_state():
    """Reset app state after each test."""
    yield
    reset_app_state()


class TestControlStart:
    """Tests for starting the emulator."""

    def test_start_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/control", json={"action": "start"})
        assert response.status_code == 401

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_start_standalone(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should start emulator in standalone mode."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        state = get_app_state()
        state.modes.standalone = True

        response = auth_client.post("/api/control", json={"action": "start"})
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_emu.start.assert_called_once()

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_start_already_running(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should return success if already running."""
        mock_emu = Mock()
        mock_emu.is_running = True
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        response = auth_client.post("/api/control", json={"action": "start"})
        assert response.status_code == 200
        assert "Already running" in response.json()["message"]

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_start_receiver_mode(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should start receiver in receiver mode."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        state = get_app_state()
        state.modes.receiver = True
        state.network.port = 12000
        state.network.protocol = "udp"

        response = auth_client.post("/api/control", json={"action": "start"})
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_recv.start.assert_called_once()

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_start_sender_mode(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should start emulator with sender config."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        state = get_app_state()
        state.modes.sender = True
        state.network.target_ip = "192.168.1.100"
        state.network.port = 12000
        state.network.protocol = "udp"

        response = auth_client.post("/api/control", json={"action": "start"})
        assert response.status_code == 200
        mock_emu.start.assert_called_once()


class TestControlStop:
    """Tests for stopping the emulator."""

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_stop(self, mock_receiver, mock_emulator, auth_client, reset_state):
        """Should stop emulator."""
        mock_emu = Mock()
        mock_emu.is_running = True
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        response = auth_client.post("/api/control", json={"action": "stop"})
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_emu.stop.assert_called_once()

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_stop_receiver(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should stop receiver when running."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = True
        mock_receiver.return_value = mock_recv

        response = auth_client.post("/api/control", json={"action": "stop"})
        assert response.status_code == 200
        mock_recv.stop.assert_called_once()


class TestPositionUpdate:
    """Tests for position updates."""

    def test_position_requires_auth(self, client):
        """Should require authentication."""
        response = client.post("/api/position", json={"lat": 33.0})
        assert response.status_code == 401

    @patch("backend.api.control_routes.get_emulator")
    def test_update_position(self, mock_emulator, auth_client, reset_state):
        """Should update position values."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        response = auth_client.post(
            "/api/position",
            json={
                "lat": 33.1234,
                "lon": -117.5678,
                "altitude_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        state = get_app_state()
        assert state.lat == 33.1234
        assert state.lon == -117.5678

    @patch("backend.api.control_routes.get_emulator")
    def test_update_position_while_running(
        self, mock_emulator, auth_client, reset_state
    ):
        """Should update emulator targets while running."""
        mock_emu = Mock()
        mock_emu.is_running = True
        mock_emulator.return_value = mock_emu

        response = auth_client.post(
            "/api/position",
            json={
                "altitude_ft": 10000,
                "speed_kts": 200,
                "heading": 90,
            },
        )
        assert response.status_code == 200
        mock_emu.set_target_altitude.assert_called_with(10000)
        mock_emu.set_target_speed.assert_called_with(200)
        mock_emu.set_target_heading.assert_called_with(90)

    @patch("backend.api.control_routes.get_emulator")
    def test_update_airport_icao(self, mock_emulator, auth_client, reset_state):
        """Should update airport ICAO code."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        response = auth_client.post(
            "/api/position",
            json={"airport_icao": "KLAX"},
        )
        assert response.status_code == 200

        state = get_app_state()
        assert state.airport_icao == "KLAX"


class TestRebroadcasterMode:
    """Tests for rebroadcaster mode."""

    @patch("backend.api.control_routes.get_rebroadcaster_runner")
    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_start_rebroadcaster_mode(
        self, mock_receiver, mock_emulator, mock_rebroadcaster, auth_client, reset_state
    ):
        """Should start rebroadcaster in rebroadcaster mode."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        mock_rebroad = Mock()
        mock_rebroad.is_running = False
        mock_rebroadcaster.return_value = mock_rebroad

        state = get_app_state()
        state.modes.rebroadcaster = True
        state.modes.receiver = True
        state.network.port = 12000
        state.network.efb_enabled = True
        state.network.foreflight_broadcast = True
        state.network.foreflight_sim_name = "TestSim"

        response = auth_client.post("/api/control", json={"action": "start"})
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_rebroad.start.assert_called_once()

    @patch("backend.api.control_routes.get_rebroadcaster_runner")
    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_stop_rebroadcaster(
        self, mock_receiver, mock_emulator, mock_rebroadcaster, auth_client, reset_state
    ):
        """Should stop rebroadcaster when running."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        mock_rebroad = Mock()
        mock_rebroad.is_running = True
        mock_rebroadcaster.return_value = mock_rebroad

        response = auth_client.post("/api/control", json={"action": "stop"})
        assert response.status_code == 200
        mock_rebroad.stop.assert_called_once()

    @patch("backend.api.control_routes.get_rebroadcaster_runner")
    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_status_with_rebroadcaster_running(
        self, mock_receiver, mock_emulator, mock_rebroadcaster, auth_client, reset_state
    ):
        """Should update state from running rebroadcaster."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        mock_engine = Mock()
        mock_engine.get_state.return_value = {
            "lat": 35.0,
            "lon": -119.0,
            "altitude_ft": 8000,
            "speed_kts": 180,
            "heading": 45,
            "target_altitude_ft": 10000,
            "target_speed_kts": 200,
            "target_heading": 90,
        }

        mock_rebroad = Mock()
        mock_rebroad.is_running = True
        mock_rebroad._engine = mock_engine
        mock_rebroad._receiver = Mock()
        mock_rebroad._receiver.state.is_connected = True
        mock_rebroadcaster.return_value = mock_rebroad

        response = auth_client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["gps"]["lat"] == 35.0
        assert data["gps"]["speed_kts"] == 180

    @patch("backend.api.control_routes.get_rebroadcaster_runner")
    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_status_with_receiver_running(
        self, mock_receiver, mock_emulator, mock_rebroadcaster, auth_client, reset_state
    ):
        """Should update state from running receiver."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_rebroad = Mock()
        mock_rebroad.is_running = False
        mock_rebroadcaster.return_value = mock_rebroad

        mock_engine = Mock()
        mock_engine.get_state.return_value = {
            "lat": 36.0,
            "lon": -120.0,
            "altitude_ft": 7000,
            "speed_kts": 160,
            "heading": 270,
        }

        mock_recv = Mock()
        mock_recv.is_running = True
        mock_recv._engine = mock_engine
        mock_recv._receiver = Mock()
        mock_recv._receiver.state.is_connected = True
        mock_receiver.return_value = mock_recv

        response = auth_client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["gps"]["lat"] == 36.0


class TestGetStatus:
    """Tests for status endpoint."""

    def test_status_requires_auth(self, client):
        """Should require authentication."""
        response = client.get("/api/status")
        assert response.status_code == 401

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_get_status(self, mock_receiver, mock_emulator, auth_client, reset_state):
        """Should return current status."""
        mock_emu = Mock()
        mock_emu.is_running = False
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        response = auth_client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "gps" in data
        assert "modes" in data
        assert "network" in data

    @patch("backend.api.control_routes.get_emulator")
    @patch("backend.api.control_routes.get_receiver_runner")
    def test_get_status_with_emulator_running(
        self, mock_receiver, mock_emulator, auth_client, reset_state
    ):
        """Should update state from running emulator."""
        mock_emu = Mock()
        mock_emu.is_running = True
        mock_emu.get_current_state.return_value = {
            "lat": 34.0,
            "lon": -118.0,
            "altitude_ft": 3000,
            "speed_kts": 150,
            "heading": 180,
        }
        mock_emulator.return_value = mock_emu

        mock_recv = Mock()
        mock_recv.is_running = False
        mock_receiver.return_value = mock_recv

        response = auth_client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert data["gps"]["lat"] == 34.0
        assert data["gps"]["speed_kts"] == 150
