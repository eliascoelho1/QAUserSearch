"""Message handlers for CLI Chat.

This module contains handlers for processing WebSocket messages
and providing visual feedback during query processing.

Modules:
    - message_handler: Handles status, interpretation, query, and error messages
    - suggestion_handler: Handles ambiguity resolution with interactive prompts

Example:
    >>> from src.cli.chat.handlers import MessageHandler
    >>> handler = MessageHandler(session, console, spinner)
"""

from src.cli.chat.handlers.message_handler import MessageHandler

__all__ = ["MessageHandler"]
