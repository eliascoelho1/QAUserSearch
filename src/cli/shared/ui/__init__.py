"""UI components for CLI interfaces.

This module exports visual components for building rich CLI experiences:

- **Panels**: info_panel, success_panel, warning_panel, error_panel
- **Progress**: spinner, PhaseSpinner, create_bar_progress
- **Prompts**: ask_text, ask_confirm, ask_select, ask_checkbox, ask_approval
- **Theme**: COLORS, ICONS, get_rich_theme, get_questionary_style

Example:
    >>> from src.cli.shared.ui import success_panel, spinner, ask_confirm
    >>> console = create_console()
    >>> console.print(success_panel("Done!", "Success"))

    >>> with spinner("Processing..."):
    ...     do_work()

    >>> if ask_confirm("Continue?"):
    ...     proceed()
"""

from src.cli.shared.ui.panels import (
    create_panel,
    error_panel,
    info_panel,
    success_panel,
    warning_panel,
)
from src.cli.shared.ui.progress import (
    Phase,
    PhaseSpinner,
    create_bar_progress,
    create_spinner_progress,
    spinner,
)
from src.cli.shared.ui.prompts import (
    ApprovalResult,
    ask_approval,
    ask_checkbox,
    ask_confirm,
    ask_select,
    ask_text,
)
from src.cli.shared.ui.theme import (
    COLORS,
    ICONS_ASCII,
    ICONS_EMOJI,
    IconType,
    get_icon,
    get_questionary_style,
    get_rich_theme,
)

__all__ = [
    # Theme
    "COLORS",
    "ICONS_ASCII",
    "ICONS_EMOJI",
    "IconType",
    "get_icon",
    "get_questionary_style",
    "get_rich_theme",
    # Panels
    "create_panel",
    "error_panel",
    "info_panel",
    "success_panel",
    "warning_panel",
    # Progress
    "Phase",
    "PhaseSpinner",
    "create_bar_progress",
    "create_spinner_progress",
    "spinner",
    # Prompts
    "ApprovalResult",
    "ask_approval",
    "ask_checkbox",
    "ask_confirm",
    "ask_select",
    "ask_text",
]
