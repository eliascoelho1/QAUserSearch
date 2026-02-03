"""WebSocket Connection Manager for real-time communication.

Manages WebSocket connections and provides methods for sending
messages to connected clients.
"""

from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with session-based tracking."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._active_connections: dict[str, WebSocket] = {}

    @property
    def active_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._active_connections)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection.

        Args:
            session_id: Unique identifier for this connection/session.
            websocket: The WebSocket connection to register.
        """
        await websocket.accept()
        self._active_connections[session_id] = websocket
        logger.info(
            "WebSocket connected",
            session_id=session_id,
            total_connections=self.active_connection_count,
        )

    async def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection from the registry.

        Args:
            session_id: The session to disconnect.
        """
        if session_id in self._active_connections:
            del self._active_connections[session_id]
            logger.info(
                "WebSocket disconnected",
                session_id=session_id,
                total_connections=self.active_connection_count,
            )

    def get_connection(self, session_id: str) -> WebSocket | None:
        """Get a WebSocket connection by session ID.

        Args:
            session_id: The session to look up.

        Returns:
            The WebSocket connection or None if not found.
        """
        return self._active_connections.get(session_id)

    async def send_json(self, session_id: str, data: dict[str, Any]) -> bool:
        """Send JSON data to a specific session.

        Args:
            session_id: The target session.
            data: The data to send.

        Returns:
            True if sent successfully, False if connection not found.
        """
        websocket = self._active_connections.get(session_id)
        if websocket is None:
            logger.warning("Connection not found for send", session_id=session_id)
            return False

        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(
                "Failed to send WebSocket message",
                session_id=session_id,
                error=str(e),
            )
            # Remove dead connection
            await self.disconnect(session_id)
            return False

    async def send_message(self, session_id: str, message: Any) -> bool:
        """Send a Pydantic model as JSON to a specific session.

        Args:
            session_id: The target session.
            message: A Pydantic model with a model_dump() method.

        Returns:
            True if sent successfully, False otherwise.
        """
        if hasattr(message, "model_dump"):
            return await self.send_json(session_id, message.model_dump(mode="json"))
        return await self.send_json(session_id, dict(message))

    async def broadcast(self, data: dict[str, Any]) -> int:
        """Send JSON data to all connected sessions.

        Args:
            data: The data to broadcast.

        Returns:
            Number of sessions that received the message.
        """
        sent_count = 0
        for session_id in list(self._active_connections.keys()):
            if await self.send_json(session_id, data):
                sent_count += 1
        return sent_count

    async def close_all(self) -> None:
        """Close all active connections gracefully."""
        logger.info(
            "Closing all WebSocket connections",
            count=self.active_connection_count,
        )
        for session_id, websocket in list(self._active_connections.items()):
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(
                    "Error closing WebSocket",
                    session_id=session_id,
                    error=str(e),
                )
        self._active_connections.clear()


# Singleton instance for the application
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the global ConnectionManager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
