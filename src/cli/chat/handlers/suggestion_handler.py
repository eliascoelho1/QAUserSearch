"""Suggestion handler for CLI Chat ambiguity resolution.

This module provides the SuggestionHandler class that detects critical
ambiguities in interpretations and prompts users for clarification.

The handler:
- Checks if an interpretation has critical ambiguities
- Displays interactive prompts for users to select clarification options
- Returns the user's selection or None if cancelled

Example:
    >>> from rich.console import Console
    >>> from src.cli.chat.handlers.suggestion_handler import SuggestionHandler
    >>>
    >>> console = Console()
    >>> handler = SuggestionHandler(console=console)
    >>>
    >>> if handler.has_critical_ambiguities(interpretation):
    ...     selection = handler.prompt_for_clarification(interpretation)
    ...     if selection:
    ...         # User made a selection
    ...         print(f"User selected: {selection}")
"""

from typing import TYPE_CHECKING

from src.cli.shared.ui.prompts import ask_select

if TYPE_CHECKING:
    from rich.console import Console

    from src.schemas.interpreter import InterpretationResponse


class SuggestionHandler:
    """Handler for detecting and resolving ambiguities in interpretations.

    This handler checks if an interpretation has critical ambiguities and
    provides interactive prompts for users to clarify their intent.

    Attributes:
        console: Optional Rich console for output rendering.

    Example:
        >>> handler = SuggestionHandler(console=console)
        >>> if handler.has_critical_ambiguities(interpretation):
        ...     choice = handler.prompt_for_clarification(interpretation)
        ...     if choice is None:
        ...         print("User cancelled")
    """

    def __init__(self, console: "Console | None" = None) -> None:
        """Initialize the suggestion handler.

        Args:
            console: Optional Rich console for rendering output.
        """
        self.console = console

    def has_critical_ambiguities(
        self, interpretation: "InterpretationResponse"
    ) -> bool:
        """Check if the interpretation has critical ambiguities.

        Critical ambiguities are detected when the interpretation's
        ambiguities list is not empty.

        Args:
            interpretation: The interpretation response to check.

        Returns:
            True if there are ambiguities that need resolution, False otherwise.

        Example:
            >>> if handler.has_critical_ambiguities(interpretation):
            ...     # Handle ambiguity
        """
        return len(interpretation.ambiguities) > 0

    def prompt_for_clarification(
        self, interpretation: "InterpretationResponse"
    ) -> str | None:
        """Display an interactive prompt for the user to resolve ambiguity.

        Shows a selection prompt with the suggestions from the first
        ambiguity in the interpretation. The prompt includes the field
        name and message describing the ambiguity.

        Args:
            interpretation: The interpretation response with ambiguities.

        Returns:
            The user's selected option, or None if:
            - No ambiguities exist
            - User cancelled (Ctrl+C)
            - Terminal is non-interactive

        Example:
            >>> selection = handler.prompt_for_clarification(interpretation)
            >>> if selection:
            ...     print(f"User chose: {selection}")
            >>> else:
            ...     print("Cancelled or no ambiguities")
        """
        # Return None if no ambiguities
        if not interpretation.ambiguities:
            return None

        # Get the first ambiguity to resolve
        ambiguity = interpretation.ambiguities[0]

        # Build the prompt message
        message = f"Campo '{ambiguity.field}' é ambíguo: {ambiguity.message}"

        # Show interactive selection prompt
        result = ask_select(
            message=message,
            choices=ambiguity.suggestions,
        )

        return result
