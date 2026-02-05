"""Mock Chat Client for offline development and testing.

This module provides MockChatClient, a fully offline implementation that
simulates the WebSocket chat server responses. It's useful for:
- Development without running the backend server
- Testing CLI components in isolation
- Demonstrating the chat flow without network dependencies

The mock client implements the same protocol as WSChatClient (ChatClientProtocol)
and can be used interchangeably.

Example:
    >>> from src.cli.chat.mock_client import MockChatClient
    >>> client = MockChatClient()
    >>> await client.connect()
    >>> async for msg in client.send_prompt("buscar usuários ativos"):
    ...     print(f"{msg.type}: {msg.data}")
"""

import asyncio
import random
import re
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable
from uuid import uuid4

from src.schemas.interpreter import (
    EntityResponse,
    FilterOperator,
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


# Keywords that trigger special mock behaviors
_ERROR_KEYWORDS = re.compile(r"\b(erro|error)\b", re.IGNORECASE)
_AMBIGUITY_KEYWORDS = re.compile(r"\b(ambiguidade|ambiguous|ambíguo)\b", re.IGNORECASE)


class MockChatClient:
    """Mock implementation of chat client for offline development.

    Simulates server responses based on keywords in the prompt:
    - Normal queries: Full success flow (status → interpretation → query)
    - 'erro'/'error': Returns WSErrorMessage
    - 'ambiguidade'/'ambiguous': Returns interpretation with low confidence

    Attributes:
        min_delay_ms: Minimum delay between messages in milliseconds.
        max_delay_ms: Maximum delay between messages in milliseconds.

    Example:
        >>> client = MockChatClient(min_delay_ms=100, max_delay_ms=500)
        >>> await client.connect()
        >>> async for msg in client.send_prompt("buscar usuários"):
        ...     handle_message(msg)
    """

    def __init__(
        self,
        min_delay_ms: int = 500,
        max_delay_ms: int = 2000,
    ) -> None:
        """Initialize the mock client.

        Args:
            min_delay_ms: Minimum delay between messages (default 500ms).
            max_delay_ms: Maximum delay between messages (default 2000ms).
        """
        self._connected = False
        self._min_delay_ms = min_delay_ms
        self._max_delay_ms = max_delay_ms

    @property
    def is_connected(self) -> bool:
        """Return whether the client is connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected

    async def connect(self) -> None:
        """Establish mock connection (always succeeds).

        Since this is a mock, no actual network connection is made.
        This method simply sets the connected state to True.
        """
        self._connected = True

    async def disconnect(self) -> None:
        """Close the mock connection.

        Sets the connected state to False.
        """
        self._connected = False

    async def _delay(self) -> None:
        """Wait for a random delay between min and max delay.

        Used to simulate realistic server processing time.
        """
        delay_ms = random.randint(self._min_delay_ms, self._max_delay_ms)
        await asyncio.sleep(delay_ms / 1000.0)

    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Send a prompt and yield simulated response messages.

        The response behavior depends on keywords in the prompt:
        - Contains 'erro' or 'error': Yields error message
        - Contains 'ambiguidade' or 'ambiguous': Yields low confidence interpretation
        - Otherwise: Yields normal success flow

        Args:
            prompt: The natural language query to interpret.

        Yields:
            WSMessageType: Status, interpretation, query, or error messages.

        Example:
            >>> async for msg in client.send_prompt("buscar usuários"):
            ...     if msg.type == "interpretation":
            ...         print(f"Confidence: {msg.data.confidence}")
        """
        # Auto-connect if not connected
        if not self._connected:
            await self.connect()

        # Check for error keyword
        if _ERROR_KEYWORDS.search(prompt):
            async for msg in self._yield_error_flow(prompt):
                yield msg
            return

        # Check for ambiguity keyword
        is_ambiguous = bool(_AMBIGUITY_KEYWORDS.search(prompt))

        # Normal flow with optional ambiguity flag
        async for msg in self._yield_normal_flow(prompt, is_ambiguous):
            yield msg

    async def _yield_error_flow(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Yield messages for error scenario.

        Args:
            prompt: The original prompt (for context in error message).

        Yields:
            WSStatusMessage followed by WSErrorMessage.
        """
        # Status: processing
        await self._delay()
        yield WSStatusMessage.create(
            status="processing",
            message="Analisando prompt...",
        )

        # Error message
        await self._delay()
        yield WSErrorMessage.create(
            code="MOCK_ERROR",
            message="Erro simulado para demonstração",
            details={"original_prompt": prompt},
            suggestions=[
                "Este é um erro simulado pelo modo mock",
                "Remova 'erro' ou 'error' do prompt para ver o fluxo normal",
            ],
        )

    async def _yield_normal_flow(
        self, prompt: str, is_ambiguous: bool
    ) -> AsyncIterator[WSMessageType]:
        """Yield messages for normal success flow.

        Args:
            prompt: The original prompt.
            is_ambiguous: Whether to simulate an ambiguous interpretation.

        Yields:
            Status, interpretation, status, and query messages.
        """
        # Status: processing
        await self._delay()
        yield WSStatusMessage.create(
            status="processing",
            message="Interpretando consulta...",
        )

        # Interpretation
        await self._delay()
        interpretation = self._create_mock_interpretation(prompt, is_ambiguous)
        yield WSInterpretationMessage(data=interpretation)

        # Status: generating query
        await self._delay()
        yield WSStatusMessage.create(
            status="generating",
            message="Gerando query SQL...",
        )

        # Query
        await self._delay()
        query = self._create_mock_query(interpretation)
        yield WSQueryMessage(data=query)

    def _create_mock_interpretation(
        self, prompt: str, is_ambiguous: bool
    ) -> InterpretationResponse:
        """Create a mock interpretation response.

        Args:
            prompt: The original prompt.
            is_ambiguous: Whether to create an ambiguous interpretation.

        Returns:
            InterpretationResponse with mock data based on the prompt.
        """
        # Set confidence based on ambiguity
        confidence = 0.45 if is_ambiguous else 0.85

        # Create summary from prompt
        summary = f"Interpretação de: {prompt[:100]}"
        if is_ambiguous:
            summary = (
                f"Interpretação ambígua: {prompt[:80]}... (múltiplas possibilidades)"
            )

        # Mock entities
        entities = [
            EntityResponse(
                name="users",
                table_name="qa.users",
                alias="u",
            ),
        ]

        # Mock filters based on simple keyword detection
        filters: list[FilterResponse] = []
        if "ativo" in prompt.lower() or "active" in prompt.lower():
            filters.append(
                FilterResponse(
                    field="status",
                    operator=FilterOperator.EQUALS,
                    value="active",
                    is_temporal=False,
                )
            )

        return InterpretationResponse(
            id=uuid4(),
            status=InterpretationStatus.READY,
            summary=summary,
            entities=entities,
            filters=filters,
            confidence=confidence,
        )

    def _create_mock_query(
        self, interpretation: InterpretationResponse
    ) -> QueryResponse:
        """Create a mock query response based on interpretation.

        Args:
            interpretation: The interpretation to base the query on.

        Returns:
            QueryResponse with mock SQL.
        """
        # Build simple SELECT from interpretation
        table_names = [e.table_name for e in interpretation.entities]
        table = table_names[0] if table_names else "qa.users"

        # Build WHERE clause from filters
        where_clauses = []
        for f in interpretation.filters:
            if f.operator == FilterOperator.EQUALS:
                where_clauses.append(f"{f.field} = '{f.value}'")
            else:
                where_clauses.append(f"{f.field} {f.operator.value} '{f.value}'")

        where_sql = ""
        if where_clauses:
            where_sql = f"\nWHERE {' AND '.join(where_clauses)}"

        sql = f"""SELECT *
FROM {table}{where_sql}
LIMIT 100;"""

        return QueryResponse(
            id=uuid4(),
            sql=sql,
            is_valid=True,
            validation_errors=[],
        )
