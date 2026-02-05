"""Tests for MessageHandler and SuggestionHandler.

TDD Tests for Phase 5: US2 Feedback Visual:
- T082: test_message_handler_init
- T083: test_handle_status_updates_spinner
- T084: test_handle_chunk_appends_content
- T085: test_handle_interpretation_renders_panel
- T086: test_handle_interpretation_updates_session
- T087: test_handle_query_renders_panel
- T088: test_handle_query_updates_session
- T089: test_handle_error_renders_error_panel

TDD Tests for Phase 6: US5 Suggestion Handler:
- T097: test_has_critical_ambiguities_true
- T098: test_has_critical_ambiguities_false
- T099: test_prompt_for_clarification_shows_options
- T100: test_prompt_for_clarification_returns_selection
- T101: test_prompt_for_clarification_cancelled_returns_none
"""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from uuid import UUID

from src.cli.chat.handlers.message_handler import MessageHandler
from src.cli.chat.handlers.suggestion_handler import SuggestionHandler
from src.cli.chat.session import ChatSession
from src.schemas.interpreter import (
    AmbiguityResponse,
    ErrorResponse,
    InterpretationResponse,
    InterpretationStatus,
    QueryResponse,
)

if TYPE_CHECKING:
    pass


class TestMessageHandlerInit:
    """Tests for MessageHandler initialization."""

    def test_message_handler_init(self, mock_console: MagicMock) -> None:
        """T082: MessageHandler initializes with session, console, and optional spinner."""
        # Arrange
        session = ChatSession()
        mock_spinner = MagicMock()

        # Act
        handler = MessageHandler(
            session=session,
            console=mock_console,
            spinner=mock_spinner,
        )

        # Assert
        assert handler.session is session
        assert handler.console is mock_console
        assert handler.spinner is mock_spinner

    def test_message_handler_init_without_spinner(
        self, mock_console: MagicMock
    ) -> None:
        """MessageHandler can be initialized without spinner (optional)."""
        # Arrange
        session = ChatSession()

        # Act
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )

        # Assert
        assert handler.session is session
        assert handler.console is mock_console
        assert handler.spinner is None


class TestMessageHandlerStatus:
    """Tests for handle_status method."""

    def test_handle_status_updates_spinner(self, mock_console: MagicMock) -> None:
        """T083: handle_status updates spinner text when spinner is available."""
        # Arrange
        session = ChatSession()
        mock_spinner = MagicMock()
        handler = MessageHandler(
            session=session,
            console=mock_console,
            spinner=mock_spinner,
        )
        status_message = "Interpretando prompt..."

        # Act
        handler.handle_status(status_message)

        # Assert
        mock_spinner.update.assert_called_once_with(status_message)

    def test_handle_status_no_op_without_spinner(self, mock_console: MagicMock) -> None:
        """handle_status does nothing if spinner is None."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
            spinner=None,
        )

        # Act - should not raise
        handler.handle_status("Some status")

        # Assert - no exception raised


class TestMessageHandlerChunk:
    """Tests for handle_chunk method."""

    def test_handle_chunk_appends_content(self, mock_console: MagicMock) -> None:
        """T084: handle_chunk appends content (no-op for v1, but tracks buffer)."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )

        # Act
        handler.handle_chunk("first ")
        handler.handle_chunk("second")

        # Assert - chunks are accumulated in buffer
        assert handler.content_buffer == "first second"

    def test_handle_chunk_starts_empty(self, mock_console: MagicMock) -> None:
        """Content buffer starts empty."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )

        # Assert
        assert handler.content_buffer == ""


class TestMessageHandlerInterpretation:
    """Tests for handle_interpretation method."""

    def test_handle_interpretation_renders_panel(
        self,
        mock_console: MagicMock,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """T085: handle_interpretation renders interpretation panel to console."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )

        # Act
        handler.handle_interpretation(sample_interpretation)

        # Assert - console.print was called
        mock_console.print.assert_called()
        # The call should contain a Panel (from render_interpretation)
        call_args = mock_console.print.call_args[0][0]
        # Rich Panel has specific attributes we can check
        assert hasattr(call_args, "renderable") or hasattr(call_args, "title")

    def test_handle_interpretation_updates_session(
        self,
        mock_console: MagicMock,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """T086: handle_interpretation stores interpretation in session.last_interpretation."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )
        assert session.last_interpretation is None

        # Act
        handler.handle_interpretation(sample_interpretation)

        # Assert
        assert session.last_interpretation is sample_interpretation


class TestMessageHandlerQuery:
    """Tests for handle_query method."""

    def test_handle_query_renders_panel(
        self,
        mock_console: MagicMock,
        sample_query: QueryResponse,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """T087: handle_query renders query panel to console."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )
        handler.current_prompt = "buscar usuários"
        handler.current_interpretation = sample_interpretation

        # Act
        handler.handle_query(sample_query)

        # Assert - console.print was called
        mock_console.print.assert_called()

    def test_handle_query_updates_session(
        self,
        mock_console: MagicMock,
        sample_query: QueryResponse,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """T088: handle_query calls session.add_query with prompt, interpretation, query."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )
        handler.current_prompt = "buscar usuários ativos"
        handler.current_interpretation = sample_interpretation

        # Act
        handler.handle_query(sample_query)

        # Assert
        assert len(session.get_history()) == 1
        record = session.get_history()[0]
        assert record.prompt == "buscar usuários ativos"
        assert record.interpretation == sample_interpretation
        assert record.query == sample_query


class TestMessageHandlerError:
    """Tests for handle_error method."""

    def test_handle_error_renders_error_panel(
        self,
        mock_console: MagicMock,
    ) -> None:
        """T089: handle_error renders error panel to console."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )
        error = ErrorResponse(
            code="ERR_001",
            message="Não foi possível interpretar o prompt",
            details={"reason": "Nenhuma tabela encontrada"},
            suggestions=["Verifique a ortografia", "Use termos mais específicos"],
        )

        # Act
        handler.handle_error(error)

        # Assert - console.print was called with error panel
        mock_console.print.assert_called()
        # Verify it was called (we can't easily check the content without
        # inspecting Rich internals, but we verify the call was made)
        assert mock_console.print.call_count >= 1


class TestMessageHandlerPromptTracking:
    """Tests for prompt tracking during message handling."""

    def test_set_current_prompt(self, mock_console: MagicMock) -> None:
        """set_current_prompt stores the prompt for later use in add_query."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )

        # Act
        handler.set_current_prompt("buscar usuários")

        # Assert
        assert handler.current_prompt == "buscar usuários"

    def test_reset_clears_state(
        self,
        mock_console: MagicMock,
        sample_interpretation: InterpretationResponse,
    ) -> None:
        """reset() clears current prompt, interpretation, and content buffer."""
        # Arrange
        session = ChatSession()
        handler = MessageHandler(
            session=session,
            console=mock_console,
        )
        handler.set_current_prompt("buscar usuários")
        handler.current_interpretation = sample_interpretation
        handler.handle_chunk("some content")

        # Act
        handler.reset()

        # Assert
        assert handler.current_prompt == ""
        assert handler.current_interpretation is None
        assert handler.content_buffer == ""


# =============================================================================
# SuggestionHandler Tests - Phase 6: US5 Suggestion Handler
# =============================================================================


class TestSuggestionHandlerHasCriticalAmbiguities:
    """Tests for SuggestionHandler.has_critical_ambiguities method."""

    def test_has_critical_ambiguities_true(self) -> None:
        """T097: has_critical_ambiguities returns True when interpretation has ambiguities."""
        # Arrange
        handler = SuggestionHandler()
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos (ambíguo)",
            entities=[],
            filters=[],
            confidence=0.5,
            ambiguities=[
                AmbiguityResponse(
                    field="status",
                    message="'ativo' pode se referir ao status da conta ou do cartão",
                    suggestions=["status da conta", "status do cartão"],
                ),
            ],
        )

        # Act
        result = handler.has_critical_ambiguities(interpretation)

        # Assert
        assert result is True

    def test_has_critical_ambiguities_false(self) -> None:
        """T098: has_critical_ambiguities returns False when no ambiguities."""
        # Arrange
        handler = SuggestionHandler()
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos",
            entities=[],
            filters=[],
            confidence=0.85,
            ambiguities=[],  # Empty list - no ambiguities
        )

        # Act
        result = handler.has_critical_ambiguities(interpretation)

        # Assert
        assert result is False

    def test_has_critical_ambiguities_false_default(self) -> None:
        """has_critical_ambiguities returns False when ambiguities field uses default."""
        # Arrange
        handler = SuggestionHandler()
        # InterpretationResponse without explicitly setting ambiguities uses default []
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos",
            entities=[],
            filters=[],
            confidence=0.85,
        )

        # Act
        result = handler.has_critical_ambiguities(interpretation)

        # Assert
        assert result is False


class TestSuggestionHandlerPromptForClarification:
    """Tests for SuggestionHandler.prompt_for_clarification method."""

    def test_prompt_for_clarification_shows_options(
        self, mock_console: MagicMock
    ) -> None:
        """T099: prompt_for_clarification displays options from the ambiguity."""
        # Arrange
        handler = SuggestionHandler(console=mock_console)
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos (ambíguo)",
            entities=[],
            filters=[],
            confidence=0.5,
            ambiguities=[
                AmbiguityResponse(
                    field="status",
                    message="'ativo' pode se referir ao status da conta ou do cartão",
                    suggestions=["status da conta", "status do cartão"],
                ),
            ],
        )

        # Mock ask_select to capture the choices passed to it
        with patch(
            "src.cli.chat.handlers.suggestion_handler.ask_select"
        ) as mock_ask_select:
            mock_ask_select.return_value = "status da conta"

            # Act
            handler.prompt_for_clarification(interpretation)

            # Assert - verify ask_select was called with the suggestions
            mock_ask_select.assert_called_once()
            call_kwargs = mock_ask_select.call_args
            # Check that choices contain the suggestions
            assert "status da conta" in call_kwargs.kwargs["choices"]
            assert "status do cartão" in call_kwargs.kwargs["choices"]

    def test_prompt_for_clarification_returns_selection(
        self, mock_console: MagicMock
    ) -> None:
        """T100: prompt_for_clarification returns the user's selection."""
        # Arrange
        handler = SuggestionHandler(console=mock_console)
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos (ambíguo)",
            entities=[],
            filters=[],
            confidence=0.5,
            ambiguities=[
                AmbiguityResponse(
                    field="status",
                    message="'ativo' pode se referir ao status da conta ou do cartão",
                    suggestions=["status da conta", "status do cartão"],
                ),
            ],
        )

        with patch(
            "src.cli.chat.handlers.suggestion_handler.ask_select"
        ) as mock_ask_select:
            mock_ask_select.return_value = "status do cartão"

            # Act
            result = handler.prompt_for_clarification(interpretation)

            # Assert
            assert result == "status do cartão"

    def test_prompt_for_clarification_cancelled_returns_none(
        self, mock_console: MagicMock
    ) -> None:
        """T101: prompt_for_clarification returns None when user cancels (Ctrl+C)."""
        # Arrange
        handler = SuggestionHandler(console=mock_console)
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos (ambíguo)",
            entities=[],
            filters=[],
            confidence=0.5,
            ambiguities=[
                AmbiguityResponse(
                    field="status",
                    message="'ativo' pode se referir ao status da conta ou do cartão",
                    suggestions=["status da conta", "status do cartão"],
                ),
            ],
        )

        with patch(
            "src.cli.chat.handlers.suggestion_handler.ask_select"
        ) as mock_ask_select:
            # ask_select returns None when cancelled
            mock_ask_select.return_value = None

            # Act
            result = handler.prompt_for_clarification(interpretation)

            # Assert
            assert result is None

    def test_prompt_for_clarification_no_ambiguities_returns_none(
        self, mock_console: MagicMock
    ) -> None:
        """prompt_for_clarification returns None when no ambiguities exist."""
        # Arrange
        handler = SuggestionHandler(console=mock_console)
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos",
            entities=[],
            filters=[],
            confidence=0.85,
            ambiguities=[],
        )

        # Act
        result = handler.prompt_for_clarification(interpretation)

        # Assert - should return None without calling ask_select
        assert result is None

    def test_prompt_for_clarification_multiple_ambiguities_uses_first(
        self, mock_console: MagicMock
    ) -> None:
        """prompt_for_clarification handles first ambiguity when multiple exist."""
        # Arrange
        handler = SuggestionHandler(console=mock_console)
        interpretation = InterpretationResponse(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            status=InterpretationStatus.READY,
            summary="Buscar usuários ativos (ambíguo)",
            entities=[],
            filters=[],
            confidence=0.4,
            ambiguities=[
                AmbiguityResponse(
                    field="status",
                    message="'ativo' pode se referir ao status da conta ou do cartão",
                    suggestions=["status da conta", "status do cartão"],
                ),
                AmbiguityResponse(
                    field="tipo",
                    message="'usuário' pode ser pessoa física ou jurídica",
                    suggestions=["pessoa física", "pessoa jurídica"],
                ),
            ],
        )

        with patch(
            "src.cli.chat.handlers.suggestion_handler.ask_select"
        ) as mock_ask_select:
            mock_ask_select.return_value = "status da conta"

            # Act
            result = handler.prompt_for_clarification(interpretation)

            # Assert - uses first ambiguity's suggestions
            mock_ask_select.assert_called_once()
            call_kwargs = mock_ask_select.call_args
            assert "status da conta" in call_kwargs.kwargs["choices"]
            assert result == "status da conta"
