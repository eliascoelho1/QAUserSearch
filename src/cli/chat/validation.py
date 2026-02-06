"""Input validation and edge case handling for CLI Chat.

This module provides validation functions and constants for:
- Prompt validation (length limits, character escaping)
- Terminal capability detection (width, TTY)
- Timeout handling for responses

All validation errors are raised as ValidationError with clear messages.

Example:
    >>> from src.cli.chat.validation import validate_prompt, check_terminal_width
    >>> validate_prompt("buscar usuários")  # OK
    >>> validate_prompt("")  # Raises ValidationError
"""

import os
import sys
from dataclasses import dataclass

# =============================================================================
# Constants
# =============================================================================

# Prompt validation limits
PROMPT_MIN_LENGTH = 1
PROMPT_MAX_LENGTH = 2000

# Terminal width thresholds
TERMINAL_MIN_WIDTH = 60

# Response timeout in seconds
RESPONSE_TIMEOUT_SECONDS = 30.0


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(Exception):
    """Exception raised for validation failures.

    Attributes:
        message: Human-readable error message.
        code: Error code for programmatic handling.
        suggestion: Optional suggestion for fixing the error.
    """

    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        suggestion: str | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message.
            code: Error code for programmatic handling.
            suggestion: Optional suggestion for fixing the error.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.suggestion = suggestion


# =============================================================================
# Terminal Detection
# =============================================================================


@dataclass
class TerminalInfo:
    """Information about the current terminal environment.

    Attributes:
        is_tty: Whether stdin/stdout is a TTY (interactive).
        width: Terminal width in columns.
        height: Terminal height in rows.
        supports_color: Whether terminal supports color output.
        is_narrow: Whether terminal width is below minimum threshold.
    """

    is_tty: bool
    width: int
    height: int
    supports_color: bool
    is_narrow: bool


def get_terminal_info() -> TerminalInfo:
    """Get information about the current terminal environment.

    Detects terminal capabilities for adaptive output formatting.

    Returns:
        TerminalInfo with terminal capabilities.

    Example:
        >>> info = get_terminal_info()
        >>> if info.is_narrow:
        ...     print("Terminal is too narrow for full output")
    """
    # Check if stdin/stdout is a TTY
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()

    # Get terminal size (fallback to 80x24)
    try:
        size = os.get_terminal_size()
        width = size.columns
        height = size.lines
    except OSError:
        # Not a terminal or size unavailable
        width = 80
        height = 24

    # Check for color support
    # NO_COLOR environment variable disables color
    no_color = os.environ.get("NO_COLOR", "").strip() != ""
    # TERM=dumb or missing TERM also suggests no color
    term = os.environ.get("TERM", "")
    supports_color = not no_color and term != "dumb" and term != ""

    # Check if terminal is too narrow
    is_narrow = width < TERMINAL_MIN_WIDTH

    return TerminalInfo(
        is_tty=is_tty,
        width=width,
        height=height,
        supports_color=supports_color,
        is_narrow=is_narrow,
    )


def check_terminal_width() -> str | None:
    """Check if terminal width is adequate for full output.

    Returns:
        Warning message if terminal is narrow, None otherwise.

    Example:
        >>> warning = check_terminal_width()
        >>> if warning:
        ...     print(warning)
    """
    info = get_terminal_info()
    if info.is_narrow:
        return (
            f"Terminal estreito ({info.width} colunas). "
            f"Recomendado: {TERMINAL_MIN_WIDTH}+ colunas para melhor visualização."
        )
    return None


def is_interactive_terminal() -> bool:
    """Check if running in an interactive terminal (TTY).

    Returns:
        True if stdin and stdout are connected to a TTY.

    Example:
        >>> if not is_interactive_terminal():
        ...     print("Running in non-interactive mode")
    """
    return get_terminal_info().is_tty


# =============================================================================
# Prompt Validation
# =============================================================================


def escape_special_characters(text: str) -> str:
    """Escape special characters in prompt for safe processing.

    Handles:
    - Null bytes (removed)
    - Control characters (removed except newlines/tabs)
    - Excessive whitespace (normalized)

    Args:
        text: Raw input text.

    Returns:
        Sanitized text safe for processing.

    Example:
        >>> escape_special_characters("hello\\x00world")
        'helloworld'
        >>> escape_special_characters("  hello   world  ")
        'hello world'
    """
    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove control characters (except newline and tab)
    result = []
    for char in text:
        if char in ("\n", "\t") or not (0 <= ord(char) <= 31):
            result.append(char)
    text = "".join(result)

    # Normalize whitespace (collapse multiple spaces, strip leading/trailing)
    # But preserve intentional newlines
    lines = text.split("\n")
    normalized_lines = [" ".join(line.split()) for line in lines]
    text = "\n".join(normalized_lines)

    return text.strip()


def validate_prompt(prompt: str) -> str:
    """Validate and sanitize a user prompt.

    Checks:
    - Not empty (after stripping whitespace)
    - Not exceeding maximum length
    - Escapes special characters

    Args:
        prompt: Raw user input.

    Returns:
        Validated and sanitized prompt.

    Raises:
        ValidationError: If prompt is empty or too long.

    Example:
        >>> validate_prompt("buscar usuários")
        'buscar usuários'
        >>> validate_prompt("")
        ValidationError: Prompt não pode estar vazio
    """
    # First escape special characters
    sanitized = escape_special_characters(prompt)

    # Check minimum length
    if len(sanitized) < PROMPT_MIN_LENGTH:
        raise ValidationError(
            message="Prompt não pode estar vazio.",
            code="EMPTY_PROMPT",
            suggestion="Digite uma consulta em linguagem natural.",
        )

    # Check maximum length
    if len(sanitized) > PROMPT_MAX_LENGTH:
        raise ValidationError(
            message=f"Prompt muito longo ({len(sanitized)} caracteres). "
            f"Máximo permitido: {PROMPT_MAX_LENGTH} caracteres.",
            code="PROMPT_TOO_LONG",
            suggestion="Tente resumir sua consulta ou dividir em partes menores.",
        )

    return sanitized


# =============================================================================
# Timeout Handling
# =============================================================================


class ResponseTimeoutError(Exception):
    """Exception raised when response timeout is exceeded.

    Attributes:
        timeout_seconds: The timeout that was exceeded.
        message: Human-readable error message.
    """

    def __init__(self, timeout_seconds: float = RESPONSE_TIMEOUT_SECONDS) -> None:
        """Initialize timeout error.

        Args:
            timeout_seconds: The timeout that was exceeded.
        """
        self.timeout_seconds = timeout_seconds
        self.message = (
            f"Tempo limite de resposta excedido ({timeout_seconds}s). "
            "O servidor pode estar lento ou indisponível."
        )
        super().__init__(self.message)


def get_response_timeout() -> float:
    """Get the configured response timeout in seconds.

    Returns:
        Timeout value in seconds.
    """
    return RESPONSE_TIMEOUT_SECONDS
