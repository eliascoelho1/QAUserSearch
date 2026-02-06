"""Unit tests for cli module."""

import re

# Regex to strip ANSI escape codes from output (ensures CI/local consistency)
_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text.

    This is useful for CLI tests where output may contain color codes
    that vary between CI and local environments.

    Args:
        text: Text potentially containing ANSI escape codes.

    Returns:
        Text with all ANSI escape codes removed.
    """
    return _ANSI_ESCAPE_PATTERN.sub("", text)
