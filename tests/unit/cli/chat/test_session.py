"""Tests for ChatSession and QueryRecord - Phase 2: Session State Management.

TDD Tests for:
- T005: test_query_record_dataclass
- T006: test_query_record_was_successful_true
- T007: test_query_record_was_successful_false
- T008: test_chat_session_initial_state
- T009: test_chat_session_add_query
- T010: test_chat_session_history_max_10
- T011: test_chat_session_clear
- T012: test_chat_session_toggle_mock_mode
"""

from datetime import UTC, datetime

# These imports will fail until implementation (RED phase)
from src.cli.chat.session import ChatSession, QueryRecord
from src.schemas.interpreter import (
    InterpretationResponse,
    QueryResponse,
)


class TestQueryRecord:
    """Tests for QueryRecord dataclass."""

    def test_query_record_dataclass(self) -> None:
        """T005: QueryRecord is a dataclass with prompt, timestamp, interpretation, query."""
        # Arrange
        prompt = "buscar usuários ativos"
        timestamp = datetime.now(UTC)

        # Act
        record = QueryRecord(
            prompt=prompt,
            timestamp=timestamp,
            interpretation=None,
            query=None,
        )

        # Assert
        assert record.prompt == prompt
        assert record.timestamp == timestamp
        assert record.interpretation is None
        assert record.query is None

    def test_query_record_was_successful_true(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T006: was_successful returns True when both interpretation and query exist."""
        # Arrange
        record = QueryRecord(
            prompt="buscar usuários ativos",
            timestamp=datetime.now(UTC),
            interpretation=sample_interpretation,
            query=sample_query,
        )

        # Act & Assert
        assert record.was_successful is True

    def test_query_record_was_successful_false_no_interpretation(
        self,
        sample_query: QueryResponse,
    ) -> None:
        """T007a: was_successful returns False when interpretation is None."""
        # Arrange
        record = QueryRecord(
            prompt="buscar usuários ativos",
            timestamp=datetime.now(UTC),
            interpretation=None,
            query=sample_query,
        )

        # Act & Assert
        assert record.was_successful is False

    def test_query_record_was_successful_false_no_query(
        self,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """T007b: was_successful returns False when query is None."""
        # Arrange
        record = QueryRecord(
            prompt="buscar usuários ativos",
            timestamp=datetime.now(UTC),
            interpretation=sample_interpretation,
            query=None,
        )

        # Act & Assert
        assert record.was_successful is False

    def test_query_record_was_successful_false_both_none(self) -> None:
        """T007c: was_successful returns False when both are None."""
        # Arrange
        record = QueryRecord(
            prompt="buscar usuários ativos",
            timestamp=datetime.now(UTC),
            interpretation=None,
            query=None,
        )

        # Act & Assert
        assert record.was_successful is False


class TestChatSession:
    """Tests for ChatSession dataclass."""

    def test_chat_session_initial_state(self) -> None:
        """T008: ChatSession initial state has empty history and mock_mode=False."""
        # Act
        session = ChatSession()

        # Assert
        assert session.history == []
        assert session.mock_mode is False
        assert session.last_interpretation is None

    def test_chat_session_add_query(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T009: add_query adds a QueryRecord to history."""
        # Arrange
        session = ChatSession()
        prompt = "buscar usuários ativos"

        # Act
        session.add_query(
            prompt=prompt,
            interpretation=sample_interpretation,
            query=sample_query,
        )

        # Assert
        assert len(session.history) == 1
        record = session.history[0]
        assert record.prompt == prompt
        assert record.interpretation == sample_interpretation
        assert record.query == sample_query
        assert isinstance(record.timestamp, datetime)

    def test_chat_session_history_max_10(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T010: history is limited to 10 items (FIFO - oldest removed first)."""
        # Arrange
        session = ChatSession()

        # Act - Add 12 queries
        for i in range(12):
            session.add_query(
                prompt=f"query {i}",
                interpretation=sample_interpretation,
                query=sample_query,
            )

        # Assert - Only 10 items, oldest removed
        assert len(session.history) == 10
        # First item should be "query 2" (0 and 1 were removed)
        assert session.history[0].prompt == "query 2"
        # Last item should be "query 11"
        assert session.history[-1].prompt == "query 11"

    def test_chat_session_clear(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T011: clear() empties history and resets last_interpretation."""
        # Arrange
        session = ChatSession()
        session.add_query(
            prompt="query 1",
            interpretation=sample_interpretation,
            query=sample_query,
        )
        session.last_interpretation = sample_interpretation

        # Act
        session.clear()

        # Assert
        assert session.history == []
        assert session.last_interpretation is None
        # mock_mode should NOT be reset
        assert session.mock_mode is False

    def test_chat_session_toggle_mock_mode(self) -> None:
        """T012: toggle_mock_mode() toggles mock_mode and returns new value."""
        # Arrange
        session = ChatSession()
        assert session.mock_mode is False

        # Act & Assert - Toggle on
        result = session.toggle_mock_mode()
        assert result is True
        assert session.mock_mode is True

        # Act & Assert - Toggle off
        result = session.toggle_mock_mode()
        assert result is False
        assert session.mock_mode is False

    def test_chat_session_get_history(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """Test get_history returns a copy of the history list."""
        # Arrange
        session = ChatSession()
        session.add_query(
            prompt="query 1",
            interpretation=sample_interpretation,
            query=sample_query,
        )

        # Act
        history = session.get_history()

        # Assert
        assert len(history) == 1
        assert history[0].prompt == "query 1"
        # Verify it's a copy (modifying returned list doesn't affect session)
        history.clear()
        assert len(session.history) == 1
