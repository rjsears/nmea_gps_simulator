# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_ws_routes.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for WebSocket routes."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.state import reset_app_state


@pytest.fixture
def client():
    """Create test client."""
    reset_app_state()
    return TestClient(app)


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint."""

    def test_websocket_connect(self, client):
        """Should accept WebSocket connection."""
        with client.websocket_connect("/ws") as websocket:
            # Connection should succeed
            assert websocket is not None

    def test_websocket_ping_pong(self, client):
        """Should respond to ping with pong."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            response = websocket.receive_text()
            assert response == "pong"

    def test_websocket_disconnect(self, client):
        """Should handle disconnect gracefully."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("ping")
            websocket.receive_text()
        # Context manager closes connection - should not raise
