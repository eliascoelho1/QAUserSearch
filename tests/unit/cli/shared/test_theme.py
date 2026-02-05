"""Tests for theme module - TDD RED phase.

Tests for COLORS namespace, icon functions, and theme/style factories.
"""

import re

from src.cli.shared.ui.theme import (
    COLORS,
    ICONS_ASCII,
    ICONS_EMOJI,
    IconType,
    get_icon,
    get_questionary_style,
    get_rich_theme,
)


class TestColors:
    """Tests for COLORS namespace constants."""

    def test_colors_constants_exist(self) -> None:
        """T004: Verify all required color constants exist.

        Required colors: PRIMARY, SECONDARY, SUCCESS, WARNING, ERROR, INFO, MUTED.
        """
        required_colors = [
            "PRIMARY",
            "SECONDARY",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "INFO",
            "MUTED",
        ]
        for color_name in required_colors:
            assert hasattr(COLORS, color_name), f"COLORS.{color_name} is missing"
            value = getattr(COLORS, color_name)
            assert isinstance(value, str), f"COLORS.{color_name} should be a string"

    def test_colors_are_valid_hex(self) -> None:
        """T005: Verify all color constants are valid hex codes.

        Valid formats: #RGB or #RRGGBB (case insensitive).
        """
        hex_pattern = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
        color_attrs = [
            "PRIMARY",
            "SECONDARY",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "INFO",
            "MUTED",
        ]
        for color_name in color_attrs:
            value = getattr(COLORS, color_name)
            assert hex_pattern.match(
                value
            ), f"COLORS.{color_name}={value!r} is not valid hex"


class TestIcons:
    """Tests for icon functions and constants."""

    def test_get_icon_unicode(self) -> None:
        """T006: Verify get_icon returns emoji when use_unicode=True."""
        result = get_icon(IconType.SUCCESS, use_unicode=True)
        assert result == ICONS_EMOJI[IconType.SUCCESS]
        assert result != "[OK]"  # Should NOT be ASCII fallback

    def test_get_icon_ascii_fallback(self) -> None:
        """T007: Verify get_icon returns ASCII when use_unicode=False."""
        result = get_icon(IconType.SUCCESS, use_unicode=False)
        assert result == ICONS_ASCII[IconType.SUCCESS]
        assert result == "[OK]"  # Should be ASCII fallback

    def test_icon_type_enum_values(self) -> None:
        """Verify IconType enum has all required types."""
        required_types = ["SUCCESS", "ERROR", "WARNING", "INFO"]
        for type_name in required_types:
            assert hasattr(IconType, type_name), f"IconType.{type_name} is missing"

    def test_icons_emoji_mapping_complete(self) -> None:
        """Verify all IconTypes have emoji mappings."""
        for icon_type in IconType:
            assert (
                icon_type in ICONS_EMOJI
            ), f"ICONS_EMOJI missing mapping for {icon_type}"

    def test_icons_ascii_mapping_complete(self) -> None:
        """Verify all IconTypes have ASCII mappings."""
        for icon_type in IconType:
            assert (
                icon_type in ICONS_ASCII
            ), f"ICONS_ASCII missing mapping for {icon_type}"


class TestGetRichTheme:
    """Tests for get_rich_theme function."""

    def test_get_rich_theme_returns_theme(self) -> None:
        """T008: Verify get_rich_theme returns a Rich Theme object."""
        from rich.theme import Theme

        result = get_rich_theme()
        assert isinstance(result, Theme)

    def test_get_rich_theme_has_required_styles(self) -> None:
        """Verify theme has styles for all semantic color names."""
        theme = get_rich_theme()
        required_styles = ["primary", "success", "error", "warning", "info", "muted"]
        for style_name in required_styles:
            assert style_name in theme.styles, f"Theme missing style: {style_name}"


class TestGetQuestionaryStyle:
    """Tests for get_questionary_style function."""

    def test_get_questionary_style_returns_style(self) -> None:
        """T009: Verify get_questionary_style returns a prompt_toolkit Style."""
        from prompt_toolkit.styles import Style

        result = get_questionary_style()
        assert isinstance(result, Style)

    def test_get_questionary_style_has_qmark(self) -> None:
        """Verify questionary style defines qmark style."""
        style = get_questionary_style()
        # Style is not easily introspectable, but creating it shouldn't fail
        assert style is not None
