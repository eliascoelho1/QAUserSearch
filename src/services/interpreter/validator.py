"""SQL Validator service for security checks.

This module implements a blacklist-based validation to prevent
dangerous SQL commands from being executed.
"""

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


# Forbidden SQL commands that are not allowed for execution
# Uses word boundaries to avoid false positives (e.g., "DELETED_AT" column)
FORBIDDEN_COMMANDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"--",  # SQL comments (potential injection)
    r"/\*",  # Block comments (potential injection)
    r";\s*\w",  # Multiple statements (statement after semicolon with word)
]

# Patterns that suggest potential SQL injection attempts
SUSPICIOUS_PATTERNS = [
    r"'\s*OR\s+'",  # Classic OR injection
    r"'\s*AND\s+'",  # Classic AND injection
    r"UNION\s+SELECT",  # UNION injection
    r"SLEEP\s*\(",  # Time-based injection
    r"BENCHMARK\s*\(",  # Time-based injection
    r"LOAD_FILE\s*\(",  # File access
    r"INTO\s+OUTFILE",  # File write
    r"INTO\s+DUMPFILE",  # File write
]


@dataclass
class SQLValidationResult:
    """Result of SQL validation."""

    is_valid: bool
    blocked_command: str | None = None
    security_warnings: list[str] | None = None
    error_message: str | None = None


class SQLValidator:
    """Validates SQL queries for security.

    Uses a blacklist approach to block dangerous commands
    while allowing SELECT queries.
    """

    def __init__(self) -> None:
        """Initialize the validator with compiled regex patterns."""
        self._forbidden_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in FORBIDDEN_COMMANDS
        ]
        self._suspicious_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS
        ]

    def validate(self, query: str) -> SQLValidationResult:
        """Validate a SQL query for security.

        Args:
            query: The SQL query to validate.

        Returns:
            SQLValidationResult with validation status and details.
        """
        log = logger.bind(query_preview=query[:100])

        # Check for empty query
        if not query or not query.strip():
            return SQLValidationResult(
                is_valid=False,
                error_message="Query vazia não é permitida",
            )

        query_upper = query.upper().strip()

        # Must start with SELECT
        if not query_upper.startswith("SELECT"):
            return SQLValidationResult(
                is_valid=False,
                blocked_command="NON_SELECT",
                error_message="Apenas consultas SELECT são permitidas",
            )

        # Check for forbidden commands
        for pattern in self._forbidden_patterns:
            match = pattern.search(query)
            if match:
                blocked = match.group().strip()
                log.warning("Forbidden command detected", blocked_command=blocked)
                return SQLValidationResult(
                    is_valid=False,
                    blocked_command=blocked,
                    error_message=f"Comando {blocked} não é permitido. Apenas consultas SELECT são aceitas.",
                )

        # Check for suspicious patterns (warnings, not blocking)
        warnings: list[str] = []
        for pattern in self._suspicious_patterns:
            if pattern.search(query):
                warnings.append(f"Padrão suspeito detectado: {pattern.pattern[:30]}...")

        if warnings:
            log.warning("Suspicious patterns detected", warnings=warnings)
            return SQLValidationResult(
                is_valid=True,
                security_warnings=warnings,
            )

        log.info("Query validation passed")
        return SQLValidationResult(is_valid=True)

    def get_blocked_command(self, query: str) -> str | None:
        """Get the first blocked command found in a query.

        Args:
            query: The SQL query to check.

        Returns:
            The blocked command or None if valid.
        """
        result = self.validate(query)
        return result.blocked_command


# Singleton instance for convenience
_validator: SQLValidator | None = None


def get_sql_validator() -> SQLValidator:
    """Get the SQL validator singleton."""
    global _validator
    if _validator is None:
        _validator = SQLValidator()
    return _validator
