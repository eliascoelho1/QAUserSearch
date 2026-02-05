"""Feedback panels for CLI UI.

Provides styled Rich panels for different feedback types: info, success,
warning, and error. Includes automatic icon fallback for terminals without
unicode support.

Example:
    >>> from src.cli.shared.ui.panels import success_panel, error_panel
    >>> console = create_console()
    >>> console.print(success_panel("Operation complete!", "Success"))
    >>> console.print(error_panel("Something went wrong", "Error"))
"""

from rich.panel import Panel

from src.cli.shared.ui.theme import COLORS, IconType, get_icon
from src.cli.shared.utils.terminal import supports_unicode


def create_panel(
    message: str,
    title: str,
    border_style: str,
    icon: str | None = None,
) -> Panel:
    """Create a styled panel with message and title.

    Base function for creating feedback panels. Combines an optional icon
    with the title and applies the specified border style.

    Args:
        message: Content to display inside the panel.
        title: Title text shown in the panel border.
        border_style: Color/style for the panel border (hex color or style name).
        icon: Optional icon to prepend to the title.

    Returns:
        Panel: Rich Panel instance with applied styling.

    Example:
        >>> panel = create_panel("Hello!", "Greeting", COLORS.INFO, icon="[i]")
        >>> console.print(panel)
    """
    # Combine icon and title if icon provided
    full_title = f"{icon} {title}" if icon else title

    return Panel(
        message,
        title=full_title,
        title_align="left",
        border_style=border_style,
        padding=(0, 1),
    )


def info_panel(message: str, title: str) -> Panel:
    """Create an info panel with cyan/blue border style.

    Info panels are used for informational messages that don't indicate
    success, warning, or error states.

    Args:
        message: Content to display inside the panel.
        title: Title text shown in the panel border.

    Returns:
        Panel: Rich Panel styled for informational content.

    Example:
        >>> panel = info_panel("Processing started", "Info")
        >>> console.print(panel)
    """
    use_unicode = supports_unicode()
    icon = get_icon(IconType.INFO, use_unicode=use_unicode)
    return create_panel(
        message=message,
        title=title,
        border_style=COLORS.INFO,
        icon=icon,
    )


def success_panel(message: str, title: str) -> Panel:
    """Create a success panel with green border style.

    Success panels are used to indicate successful completion of operations
    or positive outcomes.

    Args:
        message: Content to display inside the panel.
        title: Title text shown in the panel border.

    Returns:
        Panel: Rich Panel styled for success messages.

    Example:
        >>> panel = success_panel("File saved successfully!", "Success")
        >>> console.print(panel)
    """
    use_unicode = supports_unicode()
    icon = get_icon(IconType.SUCCESS, use_unicode=use_unicode)
    return create_panel(
        message=message,
        title=title,
        border_style=COLORS.SUCCESS,
        icon=icon,
    )


def warning_panel(message: str, title: str) -> Panel:
    """Create a warning panel with amber/yellow border style.

    Warning panels are used to indicate potential issues or situations
    that require user attention but are not critical errors.

    Args:
        message: Content to display inside the panel.
        title: Title text shown in the panel border.

    Returns:
        Panel: Rich Panel styled for warning messages.

    Example:
        >>> panel = warning_panel("Disk space running low", "Warning")
        >>> console.print(panel)
    """
    use_unicode = supports_unicode()
    icon = get_icon(IconType.WARNING, use_unicode=use_unicode)
    return create_panel(
        message=message,
        title=title,
        border_style=COLORS.WARNING,
        icon=icon,
    )


def error_panel(message: str, title: str) -> Panel:
    """Create an error panel with red border style.

    Error panels are used to indicate errors, failures, or critical issues
    that prevented an operation from completing.

    Args:
        message: Content to display inside the panel.
        title: Title text shown in the panel border.

    Returns:
        Panel: Rich Panel styled for error messages.

    Example:
        >>> panel = error_panel("Connection failed", "Error")
        >>> console.print(panel)
    """
    use_unicode = supports_unicode()
    icon = get_icon(IconType.ERROR, use_unicode=use_unicode)
    return create_panel(
        message=message,
        title=title,
        border_style=COLORS.ERROR,
        icon=icon,
    )
