"""Terminal utilities for capability detection and console creation.

Provides functions to detect terminal capabilities (color, unicode, size)
and a factory for creating pre-configured Rich Console instances.

Example:
    >>> from src.cli.shared.utils.terminal import supports_color, is_interactive
    >>> if supports_color():
    ...     print("Terminal supports colors!")
    >>> if is_interactive():
    ...     print("Terminal is interactive (TTY)")
"""

import os
import shutil
import sys


def get_terminal_size(
    fallback: tuple[int, int] = (80, 24),
) -> tuple[int, int]:
    """Get terminal dimensions (columns, lines).

    Args:
        fallback: Tuple of (columns, lines) to return if detection fails.
            Defaults to (80, 24) - standard terminal size.

    Returns:
        Tuple of (columns, lines) representing terminal dimensions.

    Example:
        >>> cols, lines = get_terminal_size()
        >>> print(f"Terminal is {cols}x{lines}")
    """
    try:
        size = shutil.get_terminal_size(fallback=fallback)
        return (size.columns, size.lines)
    except OSError:
        return fallback


def supports_color() -> bool:
    """Check if the terminal supports color output.

    Follows the NO_COLOR specification (https://no-color.org/):
    - If NO_COLOR is set (any value including empty), returns False
    - If FORCE_COLOR is set, returns True (unless NO_COLOR is set)
    - Otherwise, returns True if stdout is a TTY

    Returns:
        True if colors should be enabled, False otherwise.

    Example:
        >>> import os
        >>> os.environ["NO_COLOR"] = "1"
        >>> supports_color()
        False
    """
    # NO_COLOR takes precedence (any value, including empty string)
    if "NO_COLOR" in os.environ:
        return False

    # FORCE_COLOR overrides TTY detection
    if os.environ.get("FORCE_COLOR"):
        return True

    # Default to TTY check
    try:
        return sys.stdout.isatty()
    except AttributeError:
        return False


def supports_unicode() -> bool:
    """Check if the terminal supports unicode characters.

    On Windows, unicode support depends on Windows Terminal or ConEmu.
    On Unix-like systems (macOS, Linux), unicode is generally supported.

    Returns:
        True if unicode should be used, False for ASCII fallback.

    Example:
        >>> supports_unicode()
        True  # On macOS/Linux
    """
    # Windows without Windows Terminal has poor unicode support
    if sys.platform == "win32":
        # Windows Terminal sets WT_SESSION env var
        return "WT_SESSION" in os.environ

    # Unix-like systems generally support unicode
    return True


def is_interactive() -> bool:
    """Check if the terminal is interactive (connected to a TTY).

    A terminal is considered interactive if both stdin and stdout
    are connected to a TTY. This is useful for determining whether
    to show animated spinners, prompts, etc.

    Returns:
        True if terminal is interactive, False if piped/redirected.

    Example:
        >>> is_interactive()
        True  # When running in terminal
        >>> # When piped: echo "test" | python script.py
        False
    """
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except AttributeError:
        return False
