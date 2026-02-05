"""Tests for Command Processing - Phase 2: Command Processing (US3).

TDD Tests for:
- T018: test_command_type_enum_values
- T019: test_is_command_true
- T020: test_is_command_false_no_slash
- T021: test_parse_command_exit
- T022: test_parse_command_quit_alias
- T023: test_parse_command_case_insensitive
- T024: test_parse_command_unknown_returns_none
- T025: test_execute_command_exit
- T026: test_execute_command_help
- T027: test_execute_command_clear
- T028: test_execute_command_history
- T029: test_execute_command_execute_shows_info
- T030: test_execute_command_mock_toggles
"""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from src.cli.chat.commands import (
    CommandResult,
    CommandType,
    execute_command,
    is_command,
    parse_command,
)
from src.cli.chat.session import ChatSession
from src.schemas.interpreter import InterpretationResponse, QueryResponse

if TYPE_CHECKING:
    pass


class TestCommandTypeEnum:
    """Tests for CommandType enum."""

    def test_command_type_enum_values(self) -> None:
        """T018: CommandType enum has EXIT, HELP, CLEAR, HISTORY, EXECUTE, MOCK values."""
        # Assert - All required enum values exist
        assert hasattr(CommandType, "EXIT")
        assert hasattr(CommandType, "HELP")
        assert hasattr(CommandType, "CLEAR")
        assert hasattr(CommandType, "HISTORY")
        assert hasattr(CommandType, "EXECUTE")
        assert hasattr(CommandType, "MOCK")

        # Assert - Enum values are strings matching command names
        assert CommandType.EXIT.value == "exit"
        assert CommandType.HELP.value == "help"
        assert CommandType.CLEAR.value == "clear"
        assert CommandType.HISTORY.value == "history"
        assert CommandType.EXECUTE.value == "execute"
        assert CommandType.MOCK.value == "mock"


class TestIsCommand:
    """Tests for is_command() function."""

    def test_is_command_true(self) -> None:
        """T019: is_command returns True for text starting with '/'."""
        assert is_command("/exit") is True
        assert is_command("/help") is True
        assert is_command("/HELP") is True
        assert is_command("/unknown") is True
        assert is_command("/") is True

    def test_is_command_false_no_slash(self) -> None:
        """T020: is_command returns False for text not starting with '/'."""
        assert is_command("exit") is False
        assert is_command("help") is False
        assert is_command("buscar usuários") is False
        assert is_command("") is False
        assert is_command(" /exit") is False  # leading space


class TestParseCommand:
    """Tests for parse_command() function."""

    def test_parse_command_exit(self) -> None:
        """T021: parse_command returns EXIT for '/exit'."""
        assert parse_command("/exit") == CommandType.EXIT

    def test_parse_command_quit_alias(self) -> None:
        """T022: parse_command returns EXIT for '/quit' (alias)."""
        assert parse_command("/quit") == CommandType.EXIT

    def test_parse_command_case_insensitive(self) -> None:
        """T023: parse_command is case insensitive."""
        assert parse_command("/EXIT") == CommandType.EXIT
        assert parse_command("/Exit") == CommandType.EXIT
        assert parse_command("/HELP") == CommandType.HELP
        assert parse_command("/Help") == CommandType.HELP
        assert parse_command("/QUIT") == CommandType.EXIT
        assert parse_command("/Quit") == CommandType.EXIT
        assert parse_command("/CLEAR") == CommandType.CLEAR
        assert parse_command("/HISTORY") == CommandType.HISTORY
        assert parse_command("/EXECUTE") == CommandType.EXECUTE
        assert parse_command("/MOCK") == CommandType.MOCK

    def test_parse_command_unknown_returns_none(self) -> None:
        """T024: parse_command returns None for unknown commands."""
        assert parse_command("/unknown") is None
        assert parse_command("/foo") is None
        assert parse_command("/") is None
        assert parse_command("") is None
        assert parse_command("exit") is None  # not a command

    def test_parse_command_all_commands(self) -> None:
        """Additional: parse_command returns correct type for all commands."""
        assert parse_command("/help") == CommandType.HELP
        assert parse_command("/clear") == CommandType.CLEAR
        assert parse_command("/history") == CommandType.HISTORY
        assert parse_command("/execute") == CommandType.EXECUTE
        assert parse_command("/mock") == CommandType.MOCK


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_fields(self) -> None:
        """CommandResult has should_exit, message, and output fields."""
        # Arrange & Act
        result = CommandResult(should_exit=True, message="Goodbye!", output=None)

        # Assert
        assert result.should_exit is True
        assert result.message == "Goodbye!"
        assert result.output is None

    def test_command_result_defaults(self) -> None:
        """CommandResult has sensible defaults."""
        # Arrange & Act
        result = CommandResult()

        # Assert
        assert result.should_exit is False
        assert result.message is None
        assert result.output is None


class TestExecuteCommand:
    """Tests for execute_command() function."""

    def test_execute_command_exit(self, mock_console: MagicMock) -> None:
        """T025: execute_command EXIT returns should_exit=True with message."""
        # Arrange
        session = ChatSession()

        # Act
        result = execute_command(CommandType.EXIT, session, mock_console)

        # Assert
        assert result.should_exit is True
        assert result.message is not None
        assert "saindo" in result.message.lower() or "até" in result.message.lower()

    def test_execute_command_help(self, mock_console: MagicMock) -> None:
        """T026: execute_command HELP returns output with help panel."""
        # Arrange
        session = ChatSession()

        # Act
        result = execute_command(CommandType.HELP, session, mock_console)

        # Assert
        assert result.should_exit is False
        assert result.output is not None
        # Output should be a Rich Renderable (Panel, Table, etc.)

    def test_execute_command_clear(self, mock_console: MagicMock) -> None:
        """T027: execute_command CLEAR clears session and console."""
        # Arrange
        session = ChatSession()
        session.history.append(MagicMock())  # Add dummy item

        # Act
        result = execute_command(CommandType.CLEAR, session, mock_console)

        # Assert
        assert result.should_exit is False
        assert result.message is not None
        assert "limpo" in result.message.lower() or "clear" in result.message.lower()
        assert len(session.history) == 0
        mock_console.clear.assert_called_once()

    def test_execute_command_history(
        self,
        mock_console: MagicMock,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T028: execute_command HISTORY returns output with history table."""
        # Arrange
        session = ChatSession()
        session.add_query(
            prompt="buscar usuários",
            interpretation=sample_interpretation,
            query=sample_query,
        )

        # Act
        result = execute_command(CommandType.HISTORY, session, mock_console)

        # Assert
        assert result.should_exit is False
        assert result.output is not None

    def test_execute_command_history_empty(self, mock_console: MagicMock) -> None:
        """T028b: execute_command HISTORY with empty history returns message."""
        # Arrange
        session = ChatSession()

        # Act
        result = execute_command(CommandType.HISTORY, session, mock_console)

        # Assert
        assert result.should_exit is False
        # Should have either output or message indicating empty history
        assert result.output is not None or result.message is not None

    def test_execute_command_execute_shows_info(self, mock_console: MagicMock) -> None:
        """T029: execute_command EXECUTE shows 'feature coming soon' info."""
        # Arrange
        session = ChatSession()

        # Act
        result = execute_command(CommandType.EXECUTE, session, mock_console)

        # Assert
        assert result.should_exit is False
        assert result.message is not None
        # Should indicate feature is coming soon or not implemented
        assert (
            "em breve" in result.message.lower()
            or "coming soon" in result.message.lower()
            or "ainda não" in result.message.lower()
        )

    def test_execute_command_mock_toggles(self, mock_console: MagicMock) -> None:
        """T030: execute_command MOCK toggles session mock_mode."""
        # Arrange
        session = ChatSession()
        assert session.mock_mode is False

        # Act - Toggle on
        result1 = execute_command(CommandType.MOCK, session, mock_console)

        # Assert
        assert result1.should_exit is False
        assert result1.message is not None
        assert session.mock_mode is True
        assert "ativado" in result1.message.lower() or "on" in result1.message.lower()

        # Act - Toggle off
        result2 = execute_command(CommandType.MOCK, session, mock_console)

        # Assert
        assert session.mock_mode is False
        assert result2.message is not None
        assert (
            "desativado" in result2.message.lower()
            or "off" in result2.message.lower()
            or result2.message != result1.message  # Different message
        )


class TestExecuteCommandWithRenderable:
    """Tests for execute_command() with Rich Renderable output."""

    def test_help_output_is_renderable(self, mock_console: MagicMock) -> None:
        """Help output should be a Rich Renderable object."""
        # Arrange
        session = ChatSession()

        # Act
        result = execute_command(CommandType.HELP, session, mock_console)

        # Assert - Output should be renderable (has __rich_console__ or is Panel/Table)
        assert result.output is not None
        # Check it's a Rich renderable (has one of these methods/attributes)
        assert hasattr(result.output, "__rich_console__") or hasattr(
            result.output, "__rich__"
        )

    def test_history_output_is_renderable(
        self,
        mock_console: MagicMock,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """History output should be a Rich Renderable object."""
        # Arrange
        session = ChatSession()
        session.add_query(
            prompt="test query",
            interpretation=sample_interpretation,
            query=sample_query,
        )

        # Act
        result = execute_command(CommandType.HISTORY, session, mock_console)

        # Assert
        assert result.output is not None
        assert hasattr(result.output, "__rich_console__") or hasattr(
            result.output, "__rich__"
        )
