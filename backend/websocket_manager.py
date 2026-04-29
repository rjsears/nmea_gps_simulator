# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# websocket_manager.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""WebSocket connection manager."""

import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and track a new WebSocket connection.

        Args:
            websocket: The WebSocket to connect
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket disconnected. Total: {len(self.active_connections)}"
            )

    async def send_personal(self, websocket: WebSocket, data: dict[str, Any]) -> None:
        """Send data to a specific WebSocket.

        Args:
            websocket: The target WebSocket
            data: Data to send as JSON
        """
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Broadcast data to all connected WebSockets.

        Args:
            data: Data to send as JSON
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to broadcast to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for ws in disconnected:
            self.disconnect(ws)


# Singleton instance
ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    """Get singleton WebSocket manager instance."""
    return ws_manager
