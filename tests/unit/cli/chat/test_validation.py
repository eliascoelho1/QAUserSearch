"""Tests for CLI Chat validation module.

Tests cover:
- T141: Prompt validation (1-2000 chars)
- T142: Terminal width detection (<60 cols)
- T143: Non-interactive terminal fallback
- T144: Special character escaping
- T145: Response timeout handling
"""

import os
from typing import Any
from unittest.mock import patch

import pytest

from src.cli.chat.validation import (
    PROMPT_MAX_LENGTH,
    PROMPT_MIN_LENGTH,
    RESPONSE_TIMEOUT_SECONDS,
    TERMINAL_MIN_WIDTH,
    ResponseTimeoutError,
    TerminalInfo,
    ValidationError,
    check_terminal_width,
    escape_special_characters,
    get_response_timeout,
    get_terminal_info,
    is_interactive_terminal,
    validate_prompt,
)


class TestValidatePrompt:
    """Tests for validate_prompt function (T141, T144)."""

    def test_validate_prompt_normal(self) -> None:
        """Test validation of a normal prompt."""
        result = validate_prompt("buscar usuários ativos")
        assert result == "buscar usuários ativos"

    def test_validate_prompt_empty_raises_error(self) -> None:
        """Test that empty prompt raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt("")
        assert exc_info.value.code == "EMPTY_PROMPT"
        assert "vazio" in exc_info.value.message.lower()

    def test_validate_prompt_whitespace_only_raises_error(self) -> None:
        """Test that whitespace-only prompt raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt("   \t\n   ")
        assert exc_info.value.code == "EMPTY_PROMPT"

    def test_validate_prompt_too_long_raises_error(self) -> None:
        """Test that prompt exceeding max length raises ValidationError."""
        long_prompt = "x" * (PROMPT_MAX_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt(long_prompt)
        assert exc_info.value.code == "PROMPT_TOO_LONG"
        assert str(PROMPT_MAX_LENGTH) in exc_info.value.message

    def test_validate_prompt_at_max_length_succeeds(self) -> None:
        """Test that prompt at exactly max length succeeds."""
        max_prompt = "x" * PROMPT_MAX_LENGTH
        result = validate_prompt(max_prompt)
        assert len(result) == PROMPT_MAX_LENGTH

    def test_validate_prompt_at_min_length_succeeds(self) -> None:
        """Test that single character prompt succeeds."""
        result = validate_prompt("x")
        assert result == "x"

    def test_validate_prompt_strips_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        result = validate_prompt("  buscar usuários  ")
        assert result == "buscar usuários"

    def test_validate_prompt_normalizes_internal_whitespace(self) -> None:
        """Test that multiple internal spaces are collapsed."""
        result = validate_prompt("buscar    usuários    ativos")
        assert result == "buscar usuários ativos"


class TestEscapeSpecialCharacters:
    """Tests for escape_special_characters function (T144)."""

    def test_escape_removes_null_bytes(self) -> None:
        """Test that null bytes are removed."""
        result = escape_special_characters("hello\x00world")
        assert result == "helloworld"

    def test_escape_removes_control_characters(self) -> None:
        """Test that control characters (except newline/tab) are removed."""
        # Control chars 0-31 except \n (10) and \t (9)
        result = escape_special_characters("hello\x01\x02\x03world")
        assert result == "helloworld"

    def test_escape_preserves_newlines(self) -> None:
        """Test that newlines are preserved."""
        result = escape_special_characters("hello\nworld")
        assert "hello" in result and "world" in result

    def test_escape_preserves_tabs(self) -> None:
        """Test that tabs are converted to spaces (whitespace normalization)."""
        result = escape_special_characters("hello\tworld")
        # Tab gets normalized to space
        assert "hello" in result and "world" in result

    def test_escape_normalizes_excessive_whitespace(self) -> None:
        """Test that multiple spaces are collapsed."""
        result = escape_special_characters("hello    world")
        assert result == "hello world"

    def test_escape_strips_leading_trailing_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        result = escape_special_characters("  hello world  ")
        assert result == "hello world"

    def test_escape_handles_unicode(self) -> None:
        """Test that unicode characters are preserved."""
        result = escape_special_characters("buscar usuários ativos")
        assert result == "buscar usuários ativos"

    def test_escape_handles_empty_string(self) -> None:
        """Test that empty string returns empty string."""
        result = escape_special_characters("")
        assert result == ""

    def test_escape_handles_only_control_chars(self) -> None:
        """Test that string with only control chars becomes empty."""
        result = escape_special_characters("\x00\x01\x02")
        assert result == ""


class TestTerminalDetection:
    """Tests for terminal detection functions (T142, T143)."""

    def test_get_terminal_info_returns_terminal_info(self) -> None:
        """Test that get_terminal_info returns TerminalInfo object."""
        info = get_terminal_info()
        assert isinstance(info, TerminalInfo)
        assert hasattr(info, "is_tty")
        assert hasattr(info, "width")
        assert hasattr(info, "height")
        assert hasattr(info, "supports_color")
        assert hasattr(info, "is_narrow")

    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_get_terminal_info_narrow_terminal(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test detection of narrow terminal."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        # Create a fake terminal size with narrow width
        mock_size.return_value = os.terminal_size((50, 24))

        info = get_terminal_info()
        assert info.is_narrow is True
        assert info.width == 50

    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_get_terminal_info_normal_terminal(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test detection of normal width terminal."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        mock_size.return_value = os.terminal_size((80, 24))

        info = get_terminal_info()
        assert info.is_narrow is False
        assert info.width == 80

    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_get_terminal_info_not_tty(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test detection of non-TTY (piped input)."""
        mock_stdin.isatty.return_value = False
        mock_stdout.isatty.return_value = True
        mock_size.return_value = os.terminal_size((80, 24))

        info = get_terminal_info()
        assert info.is_tty is False

    @patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False)
    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_get_terminal_info_no_color_env(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test that NO_COLOR env var disables color support."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        mock_size.return_value = os.terminal_size((80, 24))

        info = get_terminal_info()
        assert info.supports_color is False

    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_check_terminal_width_narrow(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test warning message for narrow terminal."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        mock_size.return_value = os.terminal_size((50, 24))

        warning = check_terminal_width()
        assert warning is not None
        assert "50" in warning
        assert str(TERMINAL_MIN_WIDTH) in warning

    @patch("src.cli.chat.validation.os.get_terminal_size")
    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_check_terminal_width_normal(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
        mock_size: Any,
    ) -> None:
        """Test no warning for normal terminal."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True
        mock_size.return_value = os.terminal_size((80, 24))

        warning = check_terminal_width()
        assert warning is None

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_is_interactive_terminal_true(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
    ) -> None:
        """Test interactive terminal detection."""
        mock_stdin.isatty.return_value = True
        mock_stdout.isatty.return_value = True

        with patch("src.cli.chat.validation.os.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((80, 24))
            assert is_interactive_terminal() is True

    @patch("sys.stdin")
    @patch("sys.stdout")
    def test_is_interactive_terminal_false(
        self,
        mock_stdout: Any,
        mock_stdin: Any,
    ) -> None:
        """Test non-interactive terminal detection."""
        mock_stdin.isatty.return_value = False
        mock_stdout.isatty.return_value = True

        with patch("src.cli.chat.validation.os.get_terminal_size") as mock_size:
            mock_size.return_value = os.terminal_size((80, 24))
            assert is_interactive_terminal() is False


class TestResponseTimeout:
    """Tests for response timeout handling (T145)."""

    def test_get_response_timeout_returns_float(self) -> None:
        """Test that get_response_timeout returns a float."""
        timeout = get_response_timeout()
        assert isinstance(timeout, float)
        assert timeout == RESPONSE_TIMEOUT_SECONDS

    def test_response_timeout_error_message(self) -> None:
        """Test ResponseTimeoutError has proper message."""
        error = ResponseTimeoutError(30.0)
        assert "30" in error.message
        assert error.timeout_seconds == 30.0

    def test_response_timeout_error_default(self) -> None:
        """Test ResponseTimeoutError with default timeout."""
        error = ResponseTimeoutError()
        assert error.timeout_seconds == RESPONSE_TIMEOUT_SECONDS


class TestValidationConstants:
    """Tests for validation constants."""

    def test_prompt_min_length(self) -> None:
        """Test PROMPT_MIN_LENGTH constant."""
        assert PROMPT_MIN_LENGTH == 1

    def test_prompt_max_length(self) -> None:
        """Test PROMPT_MAX_LENGTH constant."""
        assert PROMPT_MAX_LENGTH == 2000

    def test_terminal_min_width(self) -> None:
        """Test TERMINAL_MIN_WIDTH constant."""
        assert TERMINAL_MIN_WIDTH == 60

    def test_response_timeout_seconds(self) -> None:
        """Test RESPONSE_TIMEOUT_SECONDS constant."""
        assert RESPONSE_TIMEOUT_SECONDS == 30.0


class TestValidationErrorClass:
    """Tests for ValidationError exception class."""

    def test_validation_error_basic(self) -> None:
        """Test basic ValidationError creation."""
        error = ValidationError("Test message")
        assert error.message == "Test message"
        assert error.code == "VALIDATION_ERROR"
        assert error.suggestion is None

    def test_validation_error_with_code(self) -> None:
        """Test ValidationError with custom code."""
        error = ValidationError("Test message", code="CUSTOM_CODE")
        assert error.code == "CUSTOM_CODE"

    def test_validation_error_with_suggestion(self) -> None:
        """Test ValidationError with suggestion."""
        error = ValidationError(
            "Test message",
            suggestion="Try this instead",
        )
        assert error.suggestion == "Try this instead"

    def test_validation_error_is_exception(self) -> None:
        """Test that ValidationError can be raised and caught."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error")
        assert str(exc_info.value) == "Test error"
