# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_websocket.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for WebSocket manager."""

import pytest
from unittest.mock import AsyncMock

from backend.websocket_manager import WebSocketManager


class TestWebSocketManager:
    """Tests for WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connect(self):
        manager = WebSocketManager()
        ws = AsyncMock()

        await manager.connect(ws)

        assert ws in manager.active_connections
        ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        manager = WebSocketManager()
        ws = AsyncMock()

        await manager.connect(ws)
        manager.disconnect(ws)

        assert ws not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self):
        manager = WebSocketManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.broadcast({"test": "data"})

        ws1.send_json.assert_called_once_with({"test": "data"})
        ws2.send_json.assert_called_once_with({"test": "data"})

    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected(self):
        manager = WebSocketManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.send_json.side_effect = Exception("Disconnected")

        await manager.connect(ws1)
        await manager.connect(ws2)

        # Should not raise, and ws1 should be removed
        await manager.broadcast({"test": "data"})

        assert ws1 not in manager.active_connections
        assert ws2 in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal(self):
        manager = WebSocketManager()
        ws = AsyncMock()

        await manager.connect(ws)
        await manager.send_personal(ws, {"msg": "hello"})

        ws.send_json.assert_called_with({"msg": "hello"})

    def test_connection_count(self):
        manager = WebSocketManager()
        assert manager.connection_count == 0
