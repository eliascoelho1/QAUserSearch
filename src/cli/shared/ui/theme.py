"""Theme system for CLI UI components.

Provides a centralized color palette and style factories for Rich and Questionary,
ensuring visual consistency across all CLI components.

Example:
    >>> from src.cli.shared.ui.theme import COLORS, get_rich_theme
    >>> console = Console(theme=get_rich_theme())
    >>> console.print(f"[success]{COLORS.SUCCESS}[/success]")

    >>> from src.cli.shared.ui.theme import get_questionary_style
    >>> style = get_questionary_style()
    >>> questionary.confirm("Continue?", style=style).ask()
"""

from enum import Enum

from prompt_toolkit.styles import Style
from rich.theme import Theme


class COLORS:
    """Centralized color palette namespace.

    All colors are hex codes compatible with Rich and prompt_toolkit.

    Attributes:
        PRIMARY: Main brand color (blue).
        SECONDARY: Complementary color (purple).
        SUCCESS: Success/positive actions (green).
        WARNING: Warning/caution (amber).
        ERROR: Error/destructive actions (red).
        INFO: Informational messages (cyan).
        MUTED: Dimmed/secondary text (gray).
    """

    PRIMARY: str = "#3B82F6"  # Blue 500
    SECONDARY: str = "#8B5CF6"  # Violet 500
    SUCCESS: str = "#10B981"  # Emerald 500
    WARNING: str = "#F59E0B"  # Amber 500
    ERROR: str = "#EF4444"  # Red 500
    INFO: str = "#06B6D4"  # Cyan 500
    MUTED: str = "#6B7280"  # Gray 500


class IconType(str, Enum):
    """Types of icons available for UI components.

    Inherits from str for JSON serialization compatibility.
    """

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Emoji icons (Unicode support required)
ICONS_EMOJI: dict[IconType, str] = {
    IconType.SUCCESS: "✅",
    IconType.ERROR: "❌",
    IconType.WARNING: "⚠️",
    IconType.INFO: "ℹ️",
}

# ASCII fallback icons (no Unicode required)
ICONS_ASCII: dict[IconType, str] = {
    IconType.SUCCESS: "[OK]",
    IconType.ERROR: "[X]",
    IconType.WARNING: "[!]",
    IconType.INFO: "[i]",
}


def get_icon(icon_type: IconType, *, use_unicode: bool = True) -> str:
    """Get icon for the given type with optional ASCII fallback.

    Args:
        icon_type: Type of icon to retrieve.
        use_unicode: If True, returns emoji icon. If False, returns ASCII fallback.

    Returns:
        Icon string (emoji or ASCII based on use_unicode).

    Example:
        >>> get_icon(IconType.SUCCESS, use_unicode=True)
        '✅'
        >>> get_icon(IconType.SUCCESS, use_unicode=False)
        '[OK]'
    """
    if use_unicode:
        return ICONS_EMOJI[icon_type]
    return ICONS_ASCII[icon_type]


def get_rich_theme() -> Theme:
    """Create a Rich Theme with the application color palette.

    Returns:
        Theme: Rich Theme object with semantic style names.

    Example:
        >>> console = Console(theme=get_rich_theme())
        >>> console.print("[success]Operation complete![/success]")
    """
    return Theme(
        {
            "primary": COLORS.PRIMARY,
            "secondary": COLORS.SECONDARY,
            "success": COLORS.SUCCESS,
            "warning": COLORS.WARNING,
            "error": COLORS.ERROR,
            "info": COLORS.INFO,
            "muted": COLORS.MUTED,
        }
    )


def get_questionary_style() -> Style:
    """Create a prompt_toolkit Style for Questionary prompts.

    The style aligns colors with the Rich theme palette for visual consistency.

    Returns:
        Style: prompt_toolkit Style for use with questionary prompts.

    Example:
        >>> style = get_questionary_style()
        >>> questionary.confirm("Continue?", style=style).ask()
    """
    return Style.from_dict(
        {
            "qmark": f"fg:{COLORS.PRIMARY} bold",  # Question mark
            "question": "bold",  # Question text
            "answer": f"fg:{COLORS.SUCCESS}",  # User's answer
            "pointer": f"fg:{COLORS.PRIMARY} bold",  # Selection pointer
            "highlighted": f"fg:{COLORS.PRIMARY} bold",  # Highlighted item
            "selected": f"fg:{COLORS.SUCCESS}",  # Selected items (checkbox)
            "separator": f"fg:{COLORS.MUTED}",  # Separator lines
            "instruction": f"fg:{COLORS.MUTED}",  # Instructions text
            "text": "",  # Default text
        }
    )
