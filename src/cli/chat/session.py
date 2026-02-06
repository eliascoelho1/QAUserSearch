"""Chat session state management for CLI Chat.

This module provides:
- QueryRecord: Immutable record of a query and its results
- ChatSession: Mutable session state (history, mock_mode, last_interpretation)

Example:
    >>> from src.cli.chat.session import ChatSession, QueryRecord
    >>> session = ChatSession()
    >>> session.add_query("buscar usuários", interpretation, query)
    >>> print(len(session.get_history()))
    1
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.interpreter import InterpretationResponse, QueryResponse


@dataclass(frozen=True)
class QueryRecord:
    """Immutable record of a single query in the chat history.

    Attributes:
        prompt: The original natural language query from the user.
        timestamp: When the query was made (UTC).
        interpretation: The LLM interpretation of the prompt, or None if failed.
        query: The generated SQL query, or None if failed.

    Example:
        >>> record = QueryRecord(
        ...     prompt="buscar usuários ativos",
        ...     timestamp=datetime.now(timezone.utc),
        ...     interpretation=interpretation_response,
        ...     query=query_response,
        ... )
        >>> if record.was_successful:
        ...     print(f"Query: {record.query.sql}")
    """

    prompt: str
    timestamp: datetime
    interpretation: "InterpretationResponse | None"
    query: "QueryResponse | None"

    @property
    def was_successful(self) -> bool:
        """Check if the query was successfully interpreted and generated.

        Returns:
            True if both interpretation and query exist, False otherwise.
        """
        return self.interpretation is not None and self.query is not None


@dataclass
class ChatSession:
    """Mutable session state for the chat CLI.

    Manages query history, mock mode toggle, and last interpretation reference.
    History is limited to 10 items (FIFO - oldest removed first).

    Attributes:
        history: List of QueryRecord, max 10 items.
        mock_mode: Whether to use mock client (offline mode).
        last_interpretation: Most recent interpretation for /execute command.

    Example:
        >>> session = ChatSession()
        >>> session.add_query("query", interpretation, query)
        >>> session.toggle_mock_mode()
        True
        >>> session.clear()
    """

    history: list[QueryRecord] = field(default_factory=list)
    mock_mode: bool = False
    last_interpretation: "InterpretationResponse | None" = None

    _MAX_HISTORY: int = field(default=10, repr=False)

    def add_query(
        self,
        prompt: str,
        interpretation: "InterpretationResponse | None",
        query: "QueryResponse | None",
    ) -> None:
        """Add a query record to the session history.

        Maintains a maximum of 10 items (FIFO - oldest removed first).

        Args:
            prompt: The original natural language query.
            interpretation: The LLM interpretation response.
            query: The generated SQL query response.
        """
        record = QueryRecord(
            prompt=prompt,
            timestamp=datetime.now(UTC),
            interpretation=interpretation,
            query=query,
        )
        self.history.append(record)

        # Enforce max history limit (FIFO)
        if len(self.history) > self._MAX_HISTORY:
            self.history = self.history[-self._MAX_HISTORY :]

    def get_history(self) -> list[QueryRecord]:
        """Get a copy of the query history.

        Returns:
            A copy of the history list (modifications don't affect session).
        """
        return self.history.copy()

    def clear(self) -> None:
        """Clear the session history and last interpretation.

        Note: mock_mode is NOT reset by clear().
        """
        self.history = []
        self.last_interpretation = None

    def toggle_mock_mode(self) -> bool:
        """Toggle mock mode on/off.

        Returns:
            The new mock_mode value after toggling.
        """
        self.mock_mode = not self.mock_mode
        return self.mock_mode
