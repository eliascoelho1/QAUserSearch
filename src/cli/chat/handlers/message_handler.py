"""Message handler for CLI Chat.

This module provides the MessageHandler class that orchestrates WebSocket
message processing and UI rendering.

The handler:
- Updates spinner status during processing phases
- Accumulates streaming content chunks
- Renders interpretation and query panels
- Stores results in session state
- Renders error panels when needed

Example:
    >>> from rich.console import Console
    >>> from src.cli.chat.handlers.message_handler import MessageHandler
    >>> from src.cli.chat.session import ChatSession
    >>>
    >>> console = Console()
    >>> session = ChatSession()
    >>> handler = MessageHandler(session=session, console=console)
    >>>
    >>> handler.set_current_prompt("buscar usuários ativos")
    >>> handler.handle_status("Interpretando...")
    >>> handler.handle_interpretation(interpretation_response)
    >>> handler.handle_query(query_response)
"""

from typing import TYPE_CHECKING, Any

from src.cli.chat.renderer import render_error, render_interpretation, render_query
from src.schemas.interpreter import InterpretationResponse

if TYPE_CHECKING:
    from rich.console import Console

    from src.cli.chat.session import ChatSession
    from src.schemas.interpreter import (
        ErrorResponse,
        QueryResponse,
    )


class MessageHandler:
    """Handler for processing WebSocket messages and rendering UI feedback.

    Orchestrates the flow between incoming messages and UI rendering:
    - Status messages update the spinner
    - Chunks are accumulated for streaming display
    - Interpretation results are rendered and stored in session
    - Query results are rendered and added to session history
    - Errors are rendered with suggestions

    Attributes:
        session: The chat session for state management.
        console: Rich console for output rendering.
        spinner: Optional spinner for status updates.
        content_buffer: Buffer for accumulating streaming chunks.
        current_prompt: The current prompt being processed.
        current_interpretation: The current interpretation (set before query).

    Example:
        >>> handler = MessageHandler(session, console, spinner)
        >>> handler.set_current_prompt("buscar usuários")
        >>> handler.handle_status("Analisando...")
        >>> handler.handle_interpretation(interpretation)
        >>> handler.handle_query(query)
    """

    def __init__(
        self,
        session: "ChatSession",
        console: "Console",
        spinner: Any | None = None,
    ) -> None:
        """Initialize the message handler.

        Args:
            session: The chat session for storing state.
            console: Rich console for rendering output.
            spinner: Optional spinner for status updates (e.g., PhaseSpinner).
        """
        self.session = session
        self.console = console
        self.spinner = spinner
        self.content_buffer: str = ""
        self.current_prompt: str = ""
        self.current_interpretation: InterpretationResponse | None = None

    def set_current_prompt(self, prompt: str) -> None:
        """Set the current prompt being processed.

        Args:
            prompt: The natural language prompt from the user.
        """
        self.current_prompt = prompt

    def reset(self) -> None:
        """Reset handler state for a new prompt.

        Clears the content buffer, current prompt, and current interpretation.
        Call this before processing a new user prompt.
        """
        self.content_buffer = ""
        self.current_prompt = ""
        self.current_interpretation = None

    def handle_status(self, message: str) -> None:
        """Handle status update message by updating the spinner.

        Args:
            message: Status message to display (e.g., "Interpretando...").

        Note:
            Does nothing if spinner is None.
        """
        if self.spinner is not None:
            self.spinner.update(message)

    def handle_chunk(self, content: str) -> None:
        """Handle streaming content chunk.

        Appends the content to the internal buffer. In v1 this is primarily
        for tracking; future versions may use this for live streaming display.

        Args:
            content: Content chunk to append.
        """
        self.content_buffer += content

    def handle_interpretation(self, interpretation: "InterpretationResponse") -> None:
        """Handle interpretation result.

        Renders the interpretation panel to console and stores it in session
        for potential use by /execute command.

        Args:
            interpretation: The interpretation response from the backend.
        """
        # Store in session for /execute command
        self.session.last_interpretation = interpretation

        # Store for use in handle_query
        self.current_interpretation = interpretation

        # Render the interpretation panel
        panel = render_interpretation(interpretation)
        self.console.print(panel)

    def handle_query(self, query: "QueryResponse") -> None:
        """Handle generated query result.

        Renders the query panel to console and adds the complete record
        to session history.

        Args:
            query: The query response from the backend.
        """
        # Render the query panel
        panel = render_query(query)
        self.console.print(panel)

        # Add to session history
        self.session.add_query(
            prompt=self.current_prompt,
            interpretation=self.current_interpretation,
            query=query,
        )

    def handle_error(self, error: "ErrorResponse") -> None:
        """Handle error response.

        Renders the error panel with code, message, details, and suggestions.

        Args:
            error: The error response from the backend.
        """
        panel = render_error(error)
        self.console.print(panel)
