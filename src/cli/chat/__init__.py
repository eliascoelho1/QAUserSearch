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
