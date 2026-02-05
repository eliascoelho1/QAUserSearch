"""Shared CLI UI components and utilities.

This module provides reusable UI components for building consistent CLI interfaces:

- **ui**: Visual components (panels, progress indicators, prompts, themes)
- **utils**: Terminal utilities (detection, console factory)

Example:
    >>> from src.cli.shared.ui import success_panel, spinner, ask_confirm
    >>> from src.cli.shared.utils import create_console

    >>> console = create_console()
    >>> console.print(success_panel("Operation complete!", "Success"))

    >>> with spinner("Processing..."):
    ...     do_work()

    >>> if ask_confirm("Continue?"):
    ...     proceed()
"""

# Re-export ui module
from src.cli.shared import ui, utils

# Re-export commonly used ui components for convenience
from src.cli.shared.ui import (
    COLORS,
    ApprovalResult,
    IconType,
    Phase,
    PhaseSpinner,
    ask_approval,
    ask_checkbox,
    ask_confirm,
    ask_select,
    ask_text,
    create_bar_progress,
    create_panel,
    error_panel,
    get_icon,
    get_questionary_style,
    get_rich_theme,
    info_panel,
    spinner,
    success_panel,
    warning_panel,
)

# Re-export commonly used utils for convenience
from src.cli.shared.utils import (
    create_console,
    get_terminal_size,
    is_interactive,
    supports_color,
    supports_unicode,
)

__all__ = [
    # Submodules
    "ui",
    "utils",
    # Theme
    "COLORS",
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
    "spinner",
    # Prompts
    "ApprovalResult",
    "ask_approval",
    "ask_checkbox",
    "ask_confirm",
    "ask_select",
    "ask_text",
    # Utils
    "create_console",
    "get_terminal_size",
    "is_interactive",
    "supports_color",
    "supports_unicode",
]
