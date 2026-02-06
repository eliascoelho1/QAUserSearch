"""Tests for MockChatClient - TDD RED phase.

Tests the mock client that works 100% offline with simulated responses.
Following TDD strictly: tests written first, then implementation.
"""

import asyncio

import pytest

from src.schemas.websocket import (
    WSErrorMessage,
    WSInterpretationMessage,
    WSQueryMessage,
    WSStatusMessage,
)


class TestMockClientConnection:
    """Tests for MockChatClient connection management."""

    @pytest.mark.asyncio
    async def test_mock_client_connect_succeeds(self) -> None:
        """T064: MockChatClient.connect() should succeed without network.

        The mock client should always connect successfully since it
        doesn't use any real network resources.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        # Should not raise and should be connected after
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_mock_client_is_connected(self) -> None:
        """T065: is_connected should return False before connect, True after.

        Tests the is_connected property state transitions.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()

        # Initially not connected
        assert client.is_connected is False

        # After connect
        await client.connect()
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_mock_client_disconnect(self) -> None:
        """T066: disconnect() should set is_connected to False.

        Tests that disconnecting properly updates the connection state.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()
        assert client.is_connected is True

        await client.disconnect()
        assert client.is_connected is False


class TestMockClientSendPrompt:
    """Tests for MockChatClient.send_prompt() async generator."""

    @pytest.mark.asyncio
    async def test_mock_client_send_prompt_normal(self) -> None:
        """T067: send_prompt() should yield messages for normal queries.

        Normal queries (without error/ambiguity keywords) should yield
        a complete flow of status, interpretation, and query messages.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        messages = []
        async for msg in client.send_prompt("buscar usuários ativos"):
            messages.append(msg)

        # Should have at least 4 messages: status, interpretation, status, query
        assert len(messages) >= 4

        # Verify message types in order
        message_types = [msg.type for msg in messages]
        assert "status" in message_types
        assert "interpretation" in message_types
        assert "query" in message_types

    @pytest.mark.asyncio
    async def test_mock_client_send_prompt_returns_status_messages(self) -> None:
        """T068: send_prompt() should yield WSStatusMessage during processing.

        The client should emit status updates to show progress.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        status_messages = []
        async for msg in client.send_prompt("buscar usuários"):
            if isinstance(msg, WSStatusMessage):
                status_messages.append(msg)

        # Should have at least 2 status messages (processing, generating)
        assert len(status_messages) >= 2

        # Verify status message structure
        for status_msg in status_messages:
            assert status_msg.type == "status"
            assert "status" in status_msg.data
            assert "message" in status_msg.data

    @pytest.mark.asyncio
    async def test_mock_client_send_prompt_returns_interpretation(self) -> None:
        """T069: send_prompt() should yield WSInterpretationMessage.

        Normal flow should include an interpretation response.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        interpretation_msg = None
        async for msg in client.send_prompt("buscar cartões de crédito"):
            if isinstance(msg, WSInterpretationMessage):
                interpretation_msg = msg
                break

        assert interpretation_msg is not None
        assert interpretation_msg.type == "interpretation"
        assert interpretation_msg.data is not None
        assert interpretation_msg.data.summary != ""
        assert 0.0 <= interpretation_msg.data.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_mock_client_send_prompt_returns_query(self) -> None:
        """T070: send_prompt() should yield WSQueryMessage at the end.

        Normal flow should end with a generated query.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        query_msg = None
        async for msg in client.send_prompt("buscar contas bancárias"):
            if isinstance(msg, WSQueryMessage):
                query_msg = msg

        assert query_msg is not None
        assert query_msg.type == "query"
        assert query_msg.data is not None
        assert "SELECT" in query_msg.data.sql.upper()
        assert query_msg.data.is_valid is True

    @pytest.mark.asyncio
    async def test_mock_client_error_keyword(self) -> None:
        """T071: send_prompt() with 'erro' keyword should yield WSErrorMessage.

        When the prompt contains 'erro' or 'error', the mock should
        simulate an error response.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        # Test with 'erro' keyword
        messages = []
        async for msg in client.send_prompt("buscar usuários com erro"):
            messages.append(msg)

        # Should contain an error message
        error_messages = [m for m in messages if isinstance(m, WSErrorMessage)]
        assert len(error_messages) >= 1

        error_msg = error_messages[0]
        assert error_msg.type == "error"
        assert error_msg.data.code != ""
        assert error_msg.data.message != ""

    @pytest.mark.asyncio
    async def test_mock_client_error_keyword_english(self) -> None:
        """Test that 'error' keyword (English) also triggers error response."""
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        messages = []
        async for msg in client.send_prompt("find users with error"):
            messages.append(msg)

        error_messages = [m for m in messages if isinstance(m, WSErrorMessage)]
        assert len(error_messages) >= 1

    @pytest.mark.asyncio
    async def test_mock_client_ambiguity_keyword(self) -> None:
        """T072: send_prompt() with 'ambiguidade' should yield low confidence.

        When the prompt contains 'ambiguidade' or 'ambiguous', the mock
        should return an interpretation with low confidence and ambiguities.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        interpretation_msg = None
        async for msg in client.send_prompt("buscar algo com ambiguidade"):
            if isinstance(msg, WSInterpretationMessage):
                interpretation_msg = msg
                break

        assert interpretation_msg is not None
        # Low confidence for ambiguous queries
        assert interpretation_msg.data.confidence < 0.7

    @pytest.mark.asyncio
    async def test_mock_client_ambiguity_keyword_english(self) -> None:
        """Test that 'ambiguous' keyword (English) also triggers ambiguity."""
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        await client.connect()

        interpretation_msg = None
        async for msg in client.send_prompt("find something ambiguous"):
            if isinstance(msg, WSInterpretationMessage):
                interpretation_msg = msg
                break

        assert interpretation_msg is not None
        assert interpretation_msg.data.confidence < 0.7

    @pytest.mark.asyncio
    async def test_mock_client_simulates_delay(self) -> None:
        """T073: send_prompt() should simulate processing delays.

        The mock should include realistic delays to simulate server
        processing time (configurable, default 50-200ms for tests).
        """
        from src.cli.chat.mock_client import MockChatClient

        # Use short delays for testing
        client = MockChatClient(min_delay_ms=10, max_delay_ms=50)
        await client.connect()

        start_time = asyncio.get_event_loop().time()

        messages = []
        async for msg in client.send_prompt("buscar usuários"):
            messages.append(msg)

        elapsed_time = asyncio.get_event_loop().time() - start_time

        # Should take at least some time (delays between messages)
        # With at least 4 messages and min 10ms delay, should be >= 30ms
        assert elapsed_time >= 0.03  # 30ms minimum

        # But not too long (max 4 * 50ms * 2 = 400ms with some margin)
        assert elapsed_time < 1.0


class TestMockClientProtocol:
    """Tests verifying MockChatClient implements ChatClientProtocol."""

    @pytest.mark.asyncio
    async def test_mock_client_can_be_used_without_connect(self) -> None:
        """send_prompt() should work even without explicit connect.

        For convenience, the client auto-connects if not connected.
        """
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient()
        # Not calling connect()

        messages = []
        async for msg in client.send_prompt("buscar dados"):
            messages.append(msg)

        # Should still yield messages
        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_mock_client_multiple_prompts(self) -> None:
        """Client should handle multiple sequential prompts."""
        from src.cli.chat.mock_client import MockChatClient

        client = MockChatClient(min_delay_ms=1, max_delay_ms=5)
        await client.connect()

        # First prompt
        messages1 = []
        async for msg in client.send_prompt("primeira query"):
            messages1.append(msg)

        # Second prompt
        messages2 = []
        async for msg in client.send_prompt("segunda query"):
            messages2.append(msg)

        assert len(messages1) >= 4
        assert len(messages2) >= 4
