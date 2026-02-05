"""Pytest fixtures for cli.shared tests.

Provides mock fixtures for testing CLI components without actual terminal interaction.
"""

from collections.abc import Generator
from io import StringIO
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_console() -> Generator[MagicMock, None, None]:
    """Mock Rich Console for testing output without terminal.

    Yields:
        MagicMock: A mock Console instance with common methods stubbed.

    Example:
        >>> def test_panel_render(mock_console: MagicMock) -> None:
        ...     info_panel("message", console=mock_console)
        ...     mock_console.print.assert_called_once()
    """
    console = MagicMock()
    console.width = 80
    console.height = 24
    console.is_terminal = True
    console.encoding = "utf-8"
    yield console


@pytest.fixture
def mock_terminal_interactive() -> Generator[dict[str, Any], None, None]:
    """Mock terminal as interactive TTY with color and unicode support.

    Yields:
        dict: Patch context with mocked environment.

    Example:
        >>> def test_spinner_in_tty(mock_terminal_interactive) -> None:
        ...     assert is_interactive() is True
    """
    with (
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stdout.isatty", return_value=True),
        patch.dict("os.environ", {}, clear=False),
    ):
        yield {"isatty": True, "color": True, "unicode": True}


@pytest.fixture
def mock_terminal_non_interactive() -> Generator[dict[str, Any], None, None]:
    """Mock terminal as non-interactive (piped/redirected).

    Yields:
        dict: Patch context with mocked environment.

    Example:
        >>> def test_spinner_in_pipe(mock_terminal_non_interactive) -> None:
        ...     assert is_interactive() is False
    """
    with (
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stdout.isatty", return_value=False),
    ):
        yield {"isatty": False, "color": False, "unicode": False}


@pytest.fixture
def mock_no_color_env() -> Generator[dict[str, str], None, None]:
    """Mock NO_COLOR environment variable set.

    Yields:
        dict: The environment dict with NO_COLOR=1.

    Example:
        >>> def test_no_color_output(mock_no_color_env) -> None:
        ...     assert supports_color() is False
    """
    with patch.dict("os.environ", {"NO_COLOR": "1"}, clear=False):
        yield {"NO_COLOR": "1"}


@pytest.fixture
def mock_force_color_env() -> Generator[dict[str, str], None, None]:
    """Mock FORCE_COLOR environment variable set.

    Yields:
        dict: The environment dict with FORCE_COLOR=1.

    Example:
        >>> def test_force_color_output(mock_force_color_env) -> None:
        ...     assert supports_color() is True
    """
    with patch.dict("os.environ", {"FORCE_COLOR": "1"}, clear=False):
        yield {"FORCE_COLOR": "1"}


@pytest.fixture
def capture_output() -> Generator[StringIO, None, None]:
    """Capture stdout for testing printed output.

    Yields:
        StringIO: Buffer containing captured output.

    Example:
        >>> def test_output(capture_output: StringIO) -> None:
        ...     print("hello")
        ...     assert "hello" in capture_output.getvalue()
    """
    buffer = StringIO()
    with patch("sys.stdout", buffer):
        yield buffer


@pytest.fixture
def mock_questionary_prompt() -> Generator[MagicMock, None, None]:
    """Mock questionary prompt for testing without user interaction.

    Yields:
        MagicMock: A mock that can be configured to return specific answers.

    Example:
        >>> def test_ask_confirm(mock_questionary_prompt: MagicMock) -> None:
        ...     mock_questionary_prompt.ask.return_value = True
        ...     result = ask_confirm("Continue?")
        ...     assert result is True
    """
    mock = MagicMock()
    mock.ask.return_value = None
    yield mock


@pytest.fixture
def mock_keyboard_interrupt() -> Generator[MagicMock, None, None]:
    """Mock that raises KeyboardInterrupt when called.

    Yields:
        MagicMock: A mock that raises KeyboardInterrupt on .ask().

    Example:
        >>> def test_ctrl_c_handling(mock_keyboard_interrupt: MagicMock) -> None:
        ...     result = ask_text("Input?")  # Uses the mock
        ...     assert result is None  # Ctrl+C returns None
    """
    mock = MagicMock()
    mock.ask.side_effect = KeyboardInterrupt()
    yield mock
