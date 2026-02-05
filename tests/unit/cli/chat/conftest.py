"""Pytest fixtures for cli.chat tests.

Provides mock fixtures for testing CLI Chat components:
- mock_console: Mock Rich Console for testing output
- mock_websocket: Mock WebSocket connection for testing client
- chat_session: Fresh ChatSession instance for each test
- sample_interpretation: Example InterpretationResponse for testing
- sample_query: Example QueryResponse for testing
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.schemas.interpreter import (
    EntityResponse,
    FilterOperator,
    FilterResponse,
    InterpretationResponse,
    InterpretationStatus,
    QueryResponse,
)


@pytest.fixture
def mock_console() -> Generator[MagicMock, None, None]:
    """Mock Rich Console for testing output without terminal.

    Yields:
        MagicMock: A mock Console instance with common methods stubbed.

    Example:
        >>> def test_render(mock_console: MagicMock) -> None:
        ...     renderer.render_welcome(console=mock_console)
        ...     mock_console.print.assert_called()
    """
    console = MagicMock()
    console.width = 80
    console.height = 24
    console.is_terminal = True
    console.encoding = "utf-8"
    console.print = MagicMock()
    console.clear = MagicMock()
    yield console


@pytest.fixture
def mock_websocket() -> Generator[AsyncMock, None, None]:
    """Mock WebSocket connection for testing client without network.

    Yields:
        AsyncMock: A mock WebSocket with async methods for connect/send/recv.

    Example:
        >>> async def test_client(mock_websocket: AsyncMock) -> None:
        ...     mock_websocket.recv.return_value = '{"type": "status"}'
        ...     async with client.connect():
        ...         message = await client.receive()
    """
    ws = AsyncMock()
    ws.open = True
    ws.close = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value='{"type": "status", "data": {}}')
    ws.__aenter__ = AsyncMock(return_value=ws)
    ws.__aexit__ = AsyncMock(return_value=None)
    yield ws


@pytest.fixture
def chat_session() -> Generator[dict[str, Any], None, None]:
    """Fresh ChatSession-like dict for testing session state.

    Note: Returns dict since ChatSession will be implemented in T013-T016.
    This fixture will be updated to return actual ChatSession once implemented.

    Yields:
        dict: A session-like dict with default state.

    Example:
        >>> def test_session(chat_session: dict) -> None:
        ...     assert chat_session["is_mock_mode"] is False
        ...     assert len(chat_session["history"]) == 0
    """
    session: dict[str, Any] = {
        "history": [],
        "last_interpretation": None,
        "last_query": None,
        "is_mock_mode": False,
        "_max_history": 10,
    }
    yield session


@pytest.fixture
def sample_interpretation() -> Generator[InterpretationResponse, None, None]:
    """Example InterpretationResponse for testing rendering and handling.

    Yields:
        InterpretationResponse: A complete interpretation with entities and filters.

    Example:
        >>> def test_render_interpretation(
        ...     sample_interpretation: InterpretationResponse
        ... ) -> None:
        ...     panel = render_interpretation(sample_interpretation)
        ...     assert "credit.users" in str(panel)
    """
    interpretation = InterpretationResponse(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        status=InterpretationStatus.READY,
        summary="Buscar usuários com cartão de crédito ativo nos últimos 30 dias",
        entities=[
            EntityResponse(name="users", table_name="credit.users", alias="u"),
            EntityResponse(name="cards", table_name="credit.cards", alias="c"),
        ],
        filters=[
            FilterResponse(
                field="card_status",
                operator=FilterOperator.EQUALS,
                value="active",
                is_temporal=False,
            ),
            FilterResponse(
                field="created_at",
                operator=FilterOperator.GREATER_EQUAL,
                value="2026-01-05",
                is_temporal=True,
            ),
        ],
        confidence=0.85,
    )
    yield interpretation


@pytest.fixture
def sample_query() -> Generator[QueryResponse, None, None]:
    """Example QueryResponse for testing rendering and handling.

    Yields:
        QueryResponse: A valid generated query with SQL.

    Example:
        >>> def test_render_query(sample_query: QueryResponse) -> None:
        ...     panel = render_query(sample_query)
        ...     assert "SELECT" in str(panel)
    """
    query = QueryResponse(
        id=UUID("87654321-4321-8765-4321-876543218765"),
        sql="""SELECT u.id, u.name, u.email, c.card_number, c.card_status
FROM credit.users u
JOIN credit.cards c ON u.id = c.user_id
WHERE c.card_status = 'active'
  AND c.created_at >= '2026-01-05'
ORDER BY u.name
LIMIT 100;""",
        is_valid=True,
        validation_errors=[],
    )
    yield query


@pytest.fixture
def sample_interpretation_with_ambiguities() -> (
    Generator[InterpretationResponse, None, None]
):
    """Example InterpretationResponse with ambiguities for testing suggestions.

    Yields:
        InterpretationResponse: An interpretation with ambiguities field populated.

    Note: The base InterpretationResponse doesn't have ambiguities field.
    This fixture can be extended when ambiguity handling is implemented.

    Example:
        >>> def test_handle_ambiguity(
        ...     sample_interpretation_with_ambiguities: InterpretationResponse
        ... ) -> None:
        ...     assert interpretation.confidence < 0.7
    """
    interpretation = InterpretationResponse(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        status=InterpretationStatus.READY,
        summary="Buscar usuários ativos (ambíguo: conta ou cartão?)",
        entities=[
            EntityResponse(name="users", table_name="credit.users", alias="u"),
        ],
        filters=[
            FilterResponse(
                field="status",
                operator=FilterOperator.EQUALS,
                value="active",
                is_temporal=False,
            ),
        ],
        confidence=0.5,
    )
    yield interpretation


@pytest.fixture
def sample_error_response() -> Generator[dict[str, Any], None, None]:
    """Example error response dict for testing error handling.

    Yields:
        dict: Error response structure matching ErrorResponse schema.

    Example:
        >>> def test_render_error(sample_error_response: dict) -> None:
        ...     panel = render_error(sample_error_response)
        ...     assert "ERR_001" in str(panel)
    """
    error: dict[str, Any] = {
        "code": "ERR_001",
        "message": "Não foi possível interpretar o prompt",
        "details": {"reason": "Nenhuma tabela encontrada para 'xyz'"},
        "suggestions": [
            "Verifique a ortografia dos termos",
            "Use termos mais específicos como 'usuário', 'cartão', 'conta'",
        ],
    }
    yield error
