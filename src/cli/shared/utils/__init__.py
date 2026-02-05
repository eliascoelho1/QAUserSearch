"""Terminal utilities for CLI interfaces.

This module exports utilities for terminal capability detection and console creation:

- **Terminal detection**: supports_color, supports_unicode, is_interactive
- **Console factory**: create_console, get_terminal_size
"""

from src.cli.shared.utils.terminal import (
    get_terminal_size,
    is_interactive,
    supports_color,
    supports_unicode,
)

__all__ = [
    "get_terminal_size",
    "is_interactive",
    "supports_color",
    "supports_unicode",
]
