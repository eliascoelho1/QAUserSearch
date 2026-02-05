"""CLI Chat module for QAUserSearch.

This module provides an interactive chat interface for natural language queries
against the QA database. It supports both WebSocket connections to a real backend
and a mock mode for offline development.

Example:
    >>> from src.cli.chat import run_chat
    >>> await run_chat(mock_mode=True)

Modules:
    - session: Chat session state management
    - commands: Special command processing (/exit, /help, etc.)
    - renderer: Rich panel rendering for interpretations and queries
    - handlers: Message handling for WebSocket responses
    - mock_client: Mock client for offline development
    - client: WebSocket client for real backend connection
"""

from src.cli.chat.commands import (
    CommandResult,
    CommandType,
    execute_command,
    is_command,
    parse_command,
)
from src.cli.chat.renderer import (
    render_confidence_bar,
    render_error,
    render_help,
    render_history,
    render_interpretation,
    render_query,
    render_welcome,
)
from src.cli.chat.session import ChatSession, QueryRecord

__all__ = [
    "ChatSession",
    "CommandResult",
    "CommandType",
    "QueryRecord",
    "execute_command",
    "is_command",
    "parse_command",
    "render_confidence_bar",
    "render_error",
    "render_help",
    "render_history",
    "render_interpretation",
    "render_query",
    "render_welcome",
]
