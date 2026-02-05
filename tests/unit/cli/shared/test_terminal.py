"""Tests for terminal utilities module - TDD RED phase.

Tests for terminal capability detection: color support, unicode support,
terminal size, and interactivity checks.
"""

import os
from unittest.mock import patch


class TestSupportsColor:
    """Tests for supports_color function."""

    def test_supports_color_no_color_env(self) -> None:
        """T016: Verify supports_color returns False when NO_COLOR is set.

        Per NO_COLOR spec (https://no-color.org/), any value (including empty)
        means colors should be disabled.
        """
        from src.cli.shared.utils.terminal import supports_color

        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            result = supports_color()
            assert result is False

    def test_supports_color_no_color_empty(self) -> None:
        """Verify NO_COLOR= (empty value) also disables colors."""
        from src.cli.shared.utils.terminal import supports_color

        with patch.dict(os.environ, {"NO_COLOR": ""}, clear=False):
            result = supports_color()
            assert result is False

    def test_supports_color_force_color_env(self) -> None:
        """T017: Verify supports_color returns True when FORCE_COLOR is set.

        FORCE_COLOR should override terminal detection and enable colors.
        """
        from src.cli.shared.utils.terminal import supports_color

        with (
            patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False),
            patch("sys.stdout.isatty", return_value=False),
        ):
            result = supports_color()
            assert result is True

    def test_supports_color_no_color_overrides_force_color(self) -> None:
        """Verify NO_COLOR takes precedence over FORCE_COLOR."""
        from src.cli.shared.utils.terminal import supports_color

        with patch.dict(os.environ, {"NO_COLOR": "1", "FORCE_COLOR": "1"}, clear=False):
            result = supports_color()
            assert result is False

    def test_supports_color_tty(self) -> None:
        """Verify supports_color returns True for TTY when no env vars."""
        from src.cli.shared.utils.terminal import supports_color

        # Ensure no conflicting env vars
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)

        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            result = supports_color()
            assert result is True

    def test_supports_color_no_tty_returns_false(self) -> None:
        """Verify supports_color returns False for non-TTY without FORCE_COLOR."""
        from src.cli.shared.utils.terminal import supports_color

        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)

        with (
            patch.dict(os.environ, env, clear=True),
            patch("sys.stdout.isatty", return_value=False),
        ):
            result = supports_color()
            assert result is False


class TestSupportsUnicode:
    """Tests for supports_unicode function."""

    def test_supports_unicode_windows_no_wt(self) -> None:
        """T018: Verify supports_unicode returns False on Windows without Windows Terminal.

        Windows cmd.exe without Windows Terminal has poor unicode support.
        """
        from src.cli.shared.utils.terminal import supports_unicode

        # Remove WT_SESSION to simulate non-Windows Terminal
        env = os.environ.copy()
        env.pop("WT_SESSION", None)

        with (
            patch("sys.platform", "win32"),
            patch.dict(os.environ, env, clear=True),
        ):
            result = supports_unicode()
            assert result is False

    def test_supports_unicode_windows_with_wt(self) -> None:
        """Verify supports_unicode returns True on Windows with Windows Terminal."""
        from src.cli.shared.utils.terminal import supports_unicode

        with (
            patch("sys.platform", "win32"),
            patch.dict(os.environ, {"WT_SESSION": "1"}, clear=False),
        ):
            result = supports_unicode()
            assert result is True

    def test_supports_unicode_unix(self) -> None:
        """Verify supports_unicode returns True on Unix-like systems."""
        from src.cli.shared.utils.terminal import supports_unicode

        with patch("sys.platform", "darwin"):
            result = supports_unicode()
            assert result is True

    def test_supports_unicode_linux(self) -> None:
        """Verify supports_unicode returns True on Linux."""
        from src.cli.shared.utils.terminal import supports_unicode

        with patch("sys.platform", "linux"):
            result = supports_unicode()
            assert result is True


class TestIsInteractive:
    """Tests for is_interactive function."""

    def test_is_interactive_tty(self) -> None:
        """T019: Verify is_interactive returns True when stdin and stdout are TTY."""
        from src.cli.shared.utils.terminal import is_interactive

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            result = is_interactive()
            assert result is True

    def test_is_interactive_pipe(self) -> None:
        """T020: Verify is_interactive returns False when piped/redirected."""
        from src.cli.shared.utils.terminal import is_interactive

        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdout.isatty", return_value=True),
        ):
            result = is_interactive()
            assert result is False

    def test_is_interactive_stdout_redirect(self) -> None:
        """Verify is_interactive returns False when stdout is redirected."""
        from src.cli.shared.utils.terminal import is_interactive

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=False),
        ):
            result = is_interactive()
            assert result is False

    def test_is_interactive_both_piped(self) -> None:
        """Verify is_interactive returns False when both stdin and stdout are piped."""
        from src.cli.shared.utils.terminal import is_interactive

        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdout.isatty", return_value=False),
        ):
            result = is_interactive()
            assert result is False


class TestGetTerminalSize:
    """Tests for get_terminal_size function."""

    def test_get_terminal_size_fallback(self) -> None:
        """T021: Verify get_terminal_size returns fallback when detection fails."""
        from src.cli.shared.utils.terminal import get_terminal_size

        # Force OSError by mocking shutil.get_terminal_size
        with patch("shutil.get_terminal_size", side_effect=OSError("Not a terminal")):
            result = get_terminal_size()
            # Should return fallback values (80, 24)
            assert result == (80, 24)

    def test_get_terminal_size_returns_tuple(self) -> None:
        """Verify get_terminal_size returns (columns, lines) tuple."""
        from src.cli.shared.utils.terminal import get_terminal_size

        with patch(
            "shutil.get_terminal_size", return_value=os.terminal_size((120, 40))
        ):
            result = get_terminal_size()
            assert result == (120, 40)
            assert isinstance(result, tuple)
            assert len(result) == 2

    def test_get_terminal_size_custom_fallback(self) -> None:
        """Verify get_terminal_size uses custom fallback when provided."""
        from src.cli.shared.utils.terminal import get_terminal_size

        with patch("shutil.get_terminal_size", side_effect=OSError("Not a terminal")):
            result = get_terminal_size(fallback=(100, 50))
            assert result == (100, 50)
