"""Interactive prompts for CLI user input.

Provides styled prompts for text input, confirmation, selection, and checkbox
with consistent styling and graceful handling of keyboard interrupts (Ctrl+C).

Example:
    >>> from src.cli.shared.ui.prompts import ask_text, ask_confirm, ask_select
    >>> name = ask_text("Enter your name:")
    >>> if ask_confirm("Continue?"):
    ...     choice = ask_select("Choose option:", choices=["A", "B", "C"])
"""

from enum import Enum
from typing import cast

import questionary

from src.cli.shared.ui.theme import get_questionary_style
from src.cli.shared.utils.terminal import is_interactive


class ApprovalResult(str, Enum):
    """Result of an approval prompt.

    Inherits from str for JSON serialization support.

    Values:
        APPROVE: User approved the item
        EDIT: User wants to edit the item before approving
        REJECT: User rejected the item
        SKIP: User wants to skip this item and continue
        CANCEL: User cancelled the entire workflow (including Ctrl+C)
    """

    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    SKIP = "skip"
    CANCEL = "cancel"


def ask_text(
    message: str,
    *,
    default: str = "",
) -> str | None:
    """Prompt user for text input with styled interface.

    Args:
        message: The question/prompt to display.
        default: Default value if user presses Enter without input.

    Returns:
        User input string, or None if:
        - Terminal is non-interactive (piped/redirected)
        - User pressed Ctrl+C

    Example:
        >>> name = ask_text("Enter your name:", default="Anonymous")
        >>> if name is None:
        ...     print("Input cancelled")
    """
    if not is_interactive():
        return None

    style = get_questionary_style()

    try:
        result = questionary.text(
            message,
            default=default,
            style=style,
        ).ask()
        return cast(str | None, result)
    except KeyboardInterrupt:
        return None


def ask_confirm(
    message: str,
    *,
    default: bool = True,
) -> bool | None:
    """Prompt user for yes/no confirmation with styled interface.

    Args:
        message: The question/prompt to display.
        default: Default value if user presses Enter without input.

    Returns:
        True if user confirms, False if denies, or None if:
        - Terminal is non-interactive (piped/redirected)
        - User pressed Ctrl+C

    Example:
        >>> if ask_confirm("Delete file?", default=False):
        ...     delete_file()
        >>> # Returns None on Ctrl+C, so always check
        >>> result = ask_confirm("Continue?")
        >>> if result is None:
        ...     print("Operation cancelled")
    """
    if not is_interactive():
        return None

    style = get_questionary_style()

    try:
        result = questionary.confirm(
            message,
            default=default,
            style=style,
        ).ask()
        return cast(bool | None, result)
    except KeyboardInterrupt:
        return None


def ask_select(
    message: str,
    *,
    choices: list[str],
    default: str | None = None,
) -> str | None:
    """Prompt user to select one option from a list with styled interface.

    Displays a navigable list of options. User can use arrow keys to
    navigate and Enter to select.

    Args:
        message: The question/prompt to display.
        choices: List of options to choose from.
        default: Default selected option (must be in choices).

    Returns:
        Selected option string, or None if:
        - Terminal is non-interactive (piped/redirected)
        - User pressed Ctrl+C

    Example:
        >>> env = ask_select(
        ...     "Choose environment:",
        ...     choices=["development", "staging", "production"],
        ...     default="development",
        ... )
        >>> if env is None:
        ...     print("Selection cancelled")
    """
    if not is_interactive():
        return None

    style = get_questionary_style()

    try:
        result = questionary.select(
            message,
            choices=choices,
            default=default,
            style=style,
            instruction="(Use setas ↑↓ para navegar, Enter para selecionar)",
        ).ask()
        return cast(str | None, result)
    except KeyboardInterrupt:
        return None


def ask_checkbox(
    message: str,
    *,
    choices: list[str],
) -> list[str] | None:
    """Prompt user to select multiple options from a list with styled interface.

    Displays a navigable list where user can toggle selections using Space
    and confirm with Enter.

    Args:
        message: The question/prompt to display.
        choices: List of options to choose from.

    Returns:
        List of selected option strings (may be empty), or None if:
        - Terminal is non-interactive (piped/redirected)
        - User pressed Ctrl+C

    Example:
        >>> features = ask_checkbox(
        ...     "Select features to enable:",
        ...     choices=["logging", "metrics", "tracing"],
        ... )
        >>> if features is None:
        ...     print("Selection cancelled")
        >>> elif not features:
        ...     print("No features selected")
    """
    if not is_interactive():
        return None

    style = get_questionary_style()

    try:
        result = questionary.checkbox(
            message,
            choices=choices,
            style=style,
            instruction="(Use setas ↑↓, Espaço para selecionar, Enter para confirmar)",
        ).ask()
        return cast(list[str] | None, result)
    except KeyboardInterrupt:
        return None


# Mapping from display labels to ApprovalResult values
_APPROVAL_CHOICES = {
    "✅ Aprovar": ApprovalResult.APPROVE,
    "✏️ Editar": ApprovalResult.EDIT,
    "❌ Rejeitar": ApprovalResult.REJECT,
    "⏭️ Pular": ApprovalResult.SKIP,
    "🚫 Cancelar": ApprovalResult.CANCEL,
}


def ask_approval(
    message: str,
    *,
    allow_edit: bool = True,
    allow_skip: bool = True,
) -> ApprovalResult:
    """Prompt user to approve, edit, reject, skip, or cancel an item.

    Specialized prompt for approval workflows where users need to review
    and make decisions about items (e.g., AI-generated content, suggestions).

    Args:
        message: The question/prompt to display.
        allow_edit: Whether to show the Edit option (default True).
        allow_skip: Whether to show the Skip option (default True).

    Returns:
        ApprovalResult enum indicating user's decision:
        - APPROVE: User approved the item
        - EDIT: User wants to edit the item (if allow_edit=True)
        - REJECT: User rejected the item
        - SKIP: User wants to skip this item (if allow_skip=True)
        - CANCEL: User cancelled (Ctrl+C or non-interactive terminal)

    Example:
        >>> from src.cli.shared.ui.prompts import ask_approval, ApprovalResult
        >>> result = ask_approval("Approve this description?")
        >>> if result == ApprovalResult.APPROVE:
        ...     save_description()
        >>> elif result == ApprovalResult.EDIT:
        ...     edited = edit_description()
        >>> elif result == ApprovalResult.REJECT:
        ...     discard_description()
        >>> elif result == ApprovalResult.SKIP:
        ...     continue_to_next()
        >>> elif result == ApprovalResult.CANCEL:
        ...     abort_workflow()
    """
    if not is_interactive():
        return ApprovalResult.CANCEL

    # Build choices list based on options
    choices: list[str] = []
    choices.append("✅ Aprovar")
    if allow_edit:
        choices.append("✏️ Editar")
    choices.append("❌ Rejeitar")
    if allow_skip:
        choices.append("⏭️ Pular")
    choices.append("🚫 Cancelar")

    style = get_questionary_style()

    try:
        result = questionary.select(
            message,
            choices=choices,
            style=style,
            instruction="(Use setas ↑↓ para navegar, Enter para selecionar)",
        ).ask()

        if result is None:
            return ApprovalResult.CANCEL

        return _APPROVAL_CHOICES.get(result, ApprovalResult.CANCEL)
    except KeyboardInterrupt:
        return ApprovalResult.CANCEL
