"""Terminal utilities for CLI interfaces.

This module exports utilities for terminal capability detection and console creation:

- **Terminal detection**: supports_color, supports_unicode, is_interactive
- **Console factory**: create_console, get_terminal_size

Example:
    >>> from src.cli.shared.utils import supports_color, create_console
    >>> if supports_color():
    ...     console = create_console()
    ...     console.print("[success]Colors work![/success]")
"""

from src.cli.shared.utils.terminal import (
    create_console,
    get_terminal_size,
    is_interactive,
    supports_color,
    supports_unicode,
)

__all__ = [
    "create_console",
    "get_terminal_size",
    "is_interactive",
    "supports_color",
    "supports_unicode",
]
