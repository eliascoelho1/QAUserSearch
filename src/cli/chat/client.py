"""WebSocket Chat Client for real server connection.

This module provides WSChatClient, a WebSocket-based implementation that
connects to the backend server for query interpretation. It handles:
- WebSocket connection management
- Automatic reconnection with exponential backoff
- Message parsing and type conversion

The client implements ChatClientProtocol, making it interchangeable with
MockChatClient.

Example:
    >>> from src.cli.chat.client import WSChatClient
    >>> client = WSChatClient()
    >>> await client.connect()
    >>> async for msg in client.send_prompt("buscar usuários ativos"):
    ...     print(f"{msg.type}: {msg.data}")
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from src.schemas.interpreter import (
    EntityResponse,
    FilterResponse,
    InterpretationResponse,
    InterpretationStatus,
    QueryResponse,
)
from src.schemas.websocket import (
    WSErrorMessage,
    WSInterpretationMessage,
    WSMessageType,
    WSQueryMessage,
    WSStatusMessage,
)

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection


# Default WebSocket server URL
DEFAULT_WS_URL = "ws://localhost:8000/ws/query/interpret"


@runtime_checkable
class ChatClientProtocol(Protocol):
    """Protocol defining the interface for chat clients.

    Both MockChatClient and WSChatClient implement this protocol,
    allowing them to be used interchangeably.
    """

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected."""
        ...

    async def connect(self) -> None:
        """Establish connection to the chat server."""
        ...

    async def disconnect(self) -> None:
        """Close the connection to the chat server."""
        ...

    def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Send a prompt and yield response messages.

        Args:
            prompt: The natural language query to interpret.

        Yields:
            WebSocket messages (status, interpretation, query, or error).
        """
        ...


class WSChatClient:
    """WebSocket client for connecting to the chat server.

    Connects to the backend server via WebSocket for real-time
    query interpretation. Includes automatic reconnection with
    exponential backoff.

    Attributes:
        url: WebSocket server URL.
        max_retries: Maximum number of reconnection attempts.
        base_backoff_seconds: Base delay for exponential backoff.

    Example:
        >>> client = WSChatClient(url="ws://server:8000/ws/query/interpret")
        >>> await client.connect()
        >>> async for msg in client.send_prompt("buscar usuários"):
        ...     handle_message(msg)
    """

    def __init__(
        self,
        url: str = DEFAULT_WS_URL,
        max_retries: int = 3,
        base_backoff_seconds: float = 1.0,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            url: WebSocket server URL (default: ws://localhost:8000/ws/query/interpret).
            max_retries: Maximum reconnection attempts (default: 3).
            base_backoff_seconds: Base delay for exponential backoff in seconds (default: 1.0).
        """
        self._url = url
        self._max_retries = max_retries
        self._base_backoff_seconds = base_backoff_seconds
        self._websocket: ClientConnection | None = None
        self._connected = False

    @property
    def url(self) -> str:
        """Return the WebSocket server URL.

        Returns:
            The configured WebSocket URL.
        """
        return self._url

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected and self._websocket is not None

    async def connect(self) -> None:
        """Establish WebSocket connection to the server.

        Uses the websockets library to connect to the configured URL.

        Raises:
            WebSocketException: If connection fails.
        """
        self._websocket = await websockets.connect(self._url).__aenter__()
        self._connected = True

    async def disconnect(self) -> None:
        """Close the WebSocket connection.

        Sets the connected state to False and closes the socket.
        """
        self._connected = False
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

    async def _reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff.

        Tries up to max_retries times with exponentially increasing delays.

        Returns:
            True if reconnection succeeded, False otherwise.
        """
        for attempt in range(self._max_retries):
            backoff = self._base_backoff_seconds * (2**attempt)
            await asyncio.sleep(backoff)

            try:
                # Close existing connection if any
                if self._websocket is not None:
                    with contextlib.suppress(Exception):
                        await self._websocket.close()
                    self._websocket = None

                # Attempt to reconnect
                self._websocket = await websockets.connect(self._url).__aenter__()
                self._connected = True
                return True
            except WebSocketException:
                continue

        return False

    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Send a prompt and yield response messages.

        Sends a JSON message to the server and yields typed response
        messages. Handles automatic reconnection on connection loss.

        Args:
            prompt: The natural language query to interpret.

        Yields:
            WSMessageType: Status, interpretation, query, or error messages.

        Raises:
            ConnectionError: If max retries exceeded and cannot reconnect.

        Example:
            >>> async for msg in client.send_prompt("buscar usuários"):
            ...     if msg.type == "interpretation":
            ...         print(f"Confidence: {msg.data.confidence}")
        """
        ws = self._websocket
        if ws is None:
            raise ConnectionError("Not connected. Call connect() first.")

        retries_used = 0

        while True:
            try:
                # Send the prompt as JSON
                message = json.dumps({"prompt": prompt})
                await ws.send(message)

                # Receive and yield messages
                async for raw_message in ws:
                    parsed = self._parse_message(raw_message)
                    if parsed is not None:
                        yield parsed

                # If we get here, the server closed the connection normally
                return

            except ConnectionClosed:
                # Connection lost, try to reconnect
                if retries_used >= self._max_retries:
                    self._connected = False
                    raise ConnectionError(
                        f"Connection lost and max retries ({self._max_retries}) exceeded"
                    ) from None

                backoff = self._base_backoff_seconds * (2**retries_used)
                await asyncio.sleep(backoff)
                retries_used += 1

                # Try to reconnect
                try:
                    with contextlib.suppress(Exception):
                        await ws.close()
                    ws = await websockets.connect(self._url).__aenter__()
                    self._websocket = ws
                    self._connected = True
                except WebSocketException:
                    continue

    def _parse_message(self, raw: str | bytes) -> WSMessageType | None:
        """Parse a raw WebSocket message into a typed message.

        Args:
            raw: Raw message string or bytes from the WebSocket.

        Returns:
            Typed message object, or None if parsing fails.
        """
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            data: dict[str, Any] = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "status":
                return WSStatusMessage(
                    data=data.get("data", {}),
                )

            elif msg_type == "interpretation":
                interpretation_data = data.get("data", {})
                # Parse entities
                entities = [
                    EntityResponse(
                        name=e.get("name", ""),
                        table_name=e.get("table_name", ""),
                        alias=e.get("alias"),
                    )
                    for e in interpretation_data.get("entities", [])
                ]
                # Parse filters
                filters = [
                    FilterResponse(
                        field=f.get("field", ""),
                        operator=f.get("operator", "equals"),
                        value=f.get("value", ""),
                        is_temporal=f.get("is_temporal", False),
                    )
                    for f in interpretation_data.get("filters", [])
                ]
                # Parse status
                status_str = interpretation_data.get("status", "ready")
                try:
                    status = InterpretationStatus(status_str)
                except ValueError:
                    status = InterpretationStatus.READY

                interpretation = InterpretationResponse(
                    id=interpretation_data.get("id"),
                    status=status,
                    summary=interpretation_data.get("summary", ""),
                    entities=entities,
                    filters=filters,
                    confidence=interpretation_data.get("confidence", 0.0),
                )
                return WSInterpretationMessage(data=interpretation)

            elif msg_type == "query":
                query_data = data.get("data", {})
                query = QueryResponse(
                    id=query_data.get("id"),
                    sql=query_data.get("sql", ""),
                    is_valid=query_data.get("is_valid", True),
                    validation_errors=query_data.get("validation_errors", []),
                )
                return WSQueryMessage(data=query)

            elif msg_type == "error":
                error_data = data.get("data", {})
                return WSErrorMessage.create(
                    code=error_data.get("code", "UNKNOWN"),
                    message=error_data.get("message", "Unknown error"),
                    details=error_data.get("details"),
                    suggestions=error_data.get("suggestions"),
                )

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

        return None
