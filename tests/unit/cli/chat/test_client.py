"""Tests for WSChatClient - WebSocket Client for real server connection.

Following TDD strictly: tests written first (RED), then implementation (GREEN).
Tests T106-T115 for Phase 7: US6 WebSocket Client.
"""

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.websocket import (
    WSErrorMessage,
    WSInterpretationMessage,
    WSQueryMessage,
    WSStatusMessage,
)


class TestWSChatClientInit:
    """Tests for WSChatClient initialization."""

    def test_ws_client_init_default_url(self) -> None:
        """T106: WSChatClient should use default WebSocket URL.

        Default URL should be ws://localhost:8000/ws/query/interpret.
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        assert client.url == "ws://localhost:8000/ws/query/interpret"

    def test_ws_client_init_custom_url(self) -> None:
        """T107: WSChatClient should accept custom WebSocket URL.

        Users should be able to specify a different server URL.
        """
        from src.cli.chat.client import WSChatClient

        custom_url = "ws://custom-server:9000/ws/chat"
        client = WSChatClient(url=custom_url)

        assert client.url == custom_url


class TestWSChatClientConnection:
    """Tests for WSChatClient connect/disconnect methods."""

    @pytest.mark.asyncio
    async def test_ws_client_connect(self) -> None:
        """T108: WSChatClient.connect() should establish WebSocket connection.

        The client should use the websockets library to connect.
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        # Mock the websockets.connect function
        mock_ws = AsyncMock()
        mock_ws.open = True

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()

            mock_connect.assert_called_once_with(client.url)
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_ws_client_disconnect(self) -> None:
        """T109: WSChatClient.disconnect() should close WebSocket connection.

        After disconnecting, is_connected should be False.
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.close = AsyncMock()

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()
            assert client.is_connected is True

            await client.disconnect()

            mock_ws.close.assert_called_once()
            assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_ws_client_is_connected(self) -> None:
        """T110: is_connected should return correct connection state.

        Should be False initially, True after connect, False after disconnect.
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        # Initially not connected
        assert client.is_connected is False

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.close = AsyncMock()

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()
            assert client.is_connected is True

            await client.disconnect()
            assert client.is_connected is False


class TestWSChatClientSendPrompt:
    """Tests for WSChatClient.send_prompt() async generator."""

    @pytest.mark.asyncio
    async def test_ws_client_send_prompt_sends_message(self) -> None:
        """T111: send_prompt() should send JSON message with prompt.

        The message format should be: {"prompt": "user query"}
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.send = AsyncMock()

        # Create an async iterator for the mock
        async def mock_recv_iter() -> AsyncIterator[str]:
            yield json.dumps(
                {"type": "status", "data": {"status": "done", "message": "Done"}}
            )

        mock_ws.__aiter__ = lambda _: mock_recv_iter()

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()

            # Consume the generator
            messages = []
            async for msg in client.send_prompt("buscar usuários"):
                messages.append(msg)

            # Verify send was called with correct JSON
            mock_ws.send.assert_called_once()
            sent_data = json.loads(mock_ws.send.call_args[0][0])
            assert sent_data == {"prompt": "buscar usuários"}

    @pytest.mark.asyncio
    async def test_ws_client_send_prompt_yields_responses(self) -> None:
        """T112: send_prompt() should yield typed response messages.

        Should yield WSStatusMessage, WSInterpretationMessage, WSQueryMessage
        based on server responses.
        """
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        # Prepare mock server responses
        status_response = {
            "type": "status",
            "data": {"status": "processing", "message": "Analisando..."},
        }
        interpretation_response = {
            "type": "interpretation",
            "data": {
                "id": "12345678-1234-5678-1234-567812345678",
                "status": "ready",
                "summary": "Buscar usuários",
                "entities": [],
                "filters": [],
                "confidence": 0.85,
            },
        }
        query_response = {
            "type": "query",
            "data": {
                "id": "87654321-4321-8765-4321-876543218765",
                "sql": "SELECT * FROM users",
                "is_valid": True,
                "validation_errors": [],
            },
        }

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.send = AsyncMock()

        # Create an async iterator for the mock
        async def mock_recv_iter() -> AsyncIterator[str]:
            yield json.dumps(status_response)
            yield json.dumps(interpretation_response)
            yield json.dumps(query_response)

        mock_ws.__aiter__ = lambda _: mock_recv_iter()

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()

            messages = []
            async for msg in client.send_prompt("buscar usuários"):
                messages.append(msg)

            # Verify we got the correct message types
            assert len(messages) == 3
            assert isinstance(messages[0], WSStatusMessage)
            assert isinstance(messages[1], WSInterpretationMessage)
            assert isinstance(messages[2], WSQueryMessage)

            # Verify message content
            assert messages[0].data["status"] == "processing"
            assert messages[1].data.confidence == 0.85
            assert "SELECT" in messages[2].data.sql


class TestWSChatClientReconnection:
    """Tests for WSChatClient automatic reconnection."""

    @pytest.mark.asyncio
    async def test_ws_client_reconnect_on_disconnect(self) -> None:
        """T113: Client should automatically reconnect on unexpected disconnect.

        If connection is lost during send_prompt, client should attempt
        to reconnect before raising an error.
        """
        from websockets.exceptions import ConnectionClosed

        from src.cli.chat.client import WSChatClient

        client = WSChatClient(base_backoff_seconds=0.001)

        # First connection will fail on send, second will succeed
        mock_ws_failed = AsyncMock()
        mock_ws_failed.open = True
        mock_ws_failed.send = AsyncMock(side_effect=ConnectionClosed(None, None))
        mock_ws_failed.close = AsyncMock()

        mock_ws_success = AsyncMock()
        mock_ws_success.open = True
        mock_ws_success.send = AsyncMock()
        mock_ws_success.close = AsyncMock()

        async def mock_recv_iter() -> AsyncIterator[str]:
            yield json.dumps(
                {"type": "status", "data": {"status": "done", "message": "OK"}}
            )

        mock_ws_success.__aiter__ = lambda _: mock_recv_iter()

        call_count = 0

        def make_mock_context(ws: AsyncMock) -> MagicMock:
            """Create a mock context manager that returns ws on __aenter__."""
            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            return mock_context

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            # Set up side effect that returns different mocks
            def connect_side_effect(_url: str) -> MagicMock:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return make_mock_context(mock_ws_failed)
                else:
                    return make_mock_context(mock_ws_success)

            mock_connect.side_effect = connect_side_effect

            await client.connect()

            # This should trigger reconnection
            messages = []
            async for msg in client.send_prompt("test query"):
                messages.append(msg)

            # Should have reconnected (2 connect calls: initial + reconnect)
            assert call_count == 2
            assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_ws_client_max_retries_exceeded(self) -> None:
        """T114: Client should raise ConnectionError after max retries.

        After 3 failed reconnection attempts, should raise ConnectionError.
        """
        from websockets.exceptions import ConnectionClosed

        from src.cli.chat.client import WSChatClient

        client = WSChatClient(max_retries=3)

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.send = AsyncMock(side_effect=ConnectionClosed(None, None))

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_ws
            mock_connect.return_value = mock_context

            await client.connect()

            # Should raise ConnectionError after max retries
            with pytest.raises(ConnectionError, match="max retries"):
                async for _ in client.send_prompt("test query"):
                    pass

    @pytest.mark.asyncio
    async def test_ws_client_backoff_exponential(self) -> None:
        """T115: Reconnection should use exponential backoff.

        Delays should be: 1s, 2s, 4s (base_delay * 2^attempt).
        """
        from websockets.exceptions import ConnectionClosed

        from src.cli.chat.client import WSChatClient

        client = WSChatClient(max_retries=3, base_backoff_seconds=0.01)

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.send = AsyncMock(side_effect=ConnectionClosed(None, None))

        delays_observed: list[float] = []

        async def mock_sleep(seconds: float) -> None:
            delays_observed.append(seconds)

        with (
            patch("src.cli.chat.client.websockets.connect") as mock_connect,
            patch("src.cli.chat.client.asyncio.sleep", side_effect=mock_sleep),
        ):
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_ws
            mock_connect.return_value = mock_context

            await client.connect()

            # Should raise after retries
            with pytest.raises(ConnectionError):
                async for _ in client.send_prompt("test"):
                    pass

            # Verify exponential backoff pattern
            # With base 0.01: 0.01, 0.02, 0.04
            assert len(delays_observed) == 3
            assert delays_observed[0] == pytest.approx(0.01, rel=0.1)
            assert delays_observed[1] == pytest.approx(0.02, rel=0.1)
            assert delays_observed[2] == pytest.approx(0.04, rel=0.1)


class TestWSChatClientErrorHandling:
    """Tests for error message handling."""

    @pytest.mark.asyncio
    async def test_ws_client_yields_error_messages(self) -> None:
        """send_prompt() should yield WSErrorMessage from server errors."""
        from src.cli.chat.client import WSChatClient

        client = WSChatClient()

        error_response = {
            "type": "error",
            "data": {
                "code": "ERR_001",
                "message": "Server error",
                "details": None,
                "suggestions": [],
            },
        }

        mock_ws = AsyncMock()
        mock_ws.open = True
        mock_ws.send = AsyncMock()

        async def mock_recv_iter() -> AsyncIterator[str]:
            yield json.dumps(error_response)

        mock_ws.__aiter__ = lambda _: mock_recv_iter()

        with patch("src.cli.chat.client.websockets.connect") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_ws

            await client.connect()

            messages = []
            async for msg in client.send_prompt("cause error"):
                messages.append(msg)

            assert len(messages) == 1
            assert isinstance(messages[0], WSErrorMessage)
            assert messages[0].data.code == "ERR_001"


class TestWSChatClientProtocol:
    """Tests verifying WSChatClient implements ChatClientProtocol."""

    def test_ws_client_implements_protocol(self) -> None:
        """WSChatClient should implement ChatClientProtocol."""
        from src.cli.chat.client import ChatClientProtocol, WSChatClient

        client = WSChatClient()

        # Verify it's an instance of the protocol
        assert isinstance(client, ChatClientProtocol)
