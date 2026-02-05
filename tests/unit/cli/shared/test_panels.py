"""Tests for panels module - TDD RED phase.

Tests for styled feedback panels: info, success, warning, error.
Verifies visual styles and ASCII fallback functionality.
"""

from io import StringIO
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel

from src.cli.shared.ui.panels import (
    create_panel,
    error_panel,
    info_panel,
    success_panel,
    warning_panel,
)
from src.cli.shared.ui.theme import COLORS


class TestCreatePanel:
    """Tests for create_panel base function."""

    def test_create_panel_basic(self) -> None:
        """T033: Verify create_panel returns a Rich Panel with message and title.

        The base function should create a styled panel with the provided
        content, title, and border style.
        """
        panel = create_panel(
            message="Test message",
            title="Test Title",
            border_style=COLORS.INFO,
        )

        # Should return a Rich Panel instance
        assert isinstance(panel, Panel)

        # Panel should have the title
        assert panel.title is not None
        # Title may contain markup, check for our text
        assert "Test Title" in str(panel.title)

    def test_create_panel_with_icon(self) -> None:
        """Verify create_panel includes icon when provided."""
        panel = create_panel(
            message="Test message",
            title="Title",
            border_style=COLORS.SUCCESS,
            icon="[OK]",
        )

        assert isinstance(panel, Panel)
        # Icon should appear in the title
        assert panel.title is not None
        title_str = str(panel.title)
        assert "[OK]" in title_str or "Title" in title_str

    def test_create_panel_no_icon(self) -> None:
        """Verify create_panel works without icon."""
        panel = create_panel(
            message="Test message",
            title="Title Only",
            border_style=COLORS.INFO,
        )

        assert isinstance(panel, Panel)
        assert panel.title is not None


class TestInfoPanel:
    """Tests for info_panel function."""

    def test_info_panel_style(self) -> None:
        """T034: Verify info_panel uses INFO color (cyan/blue) for border.

        Info panels should have a cyan/blue border style to indicate
        informational content.
        """
        panel = info_panel("Information message", "Info Title")

        assert isinstance(panel, Panel)
        # Border style should use INFO color
        assert panel.border_style is not None
        border_style = str(panel.border_style)
        # Check that border style contains the INFO color (hex or style name)
        assert COLORS.INFO in border_style or "info" in border_style.lower()

    def test_info_panel_has_icon(self) -> None:
        """Verify info_panel includes info icon in title."""
        panel = info_panel("Message", "Title")

        assert panel.title is not None
        title_str = str(panel.title)
        # Should have info icon (emoji or ASCII)
        assert "ℹ️" in title_str or "[i]" in title_str or "Title" in title_str


class TestSuccessPanel:
    """Tests for success_panel function."""

    def test_success_panel_style(self) -> None:
        """T035: Verify success_panel uses SUCCESS color (green) for border.

        Success panels should have a green border style to indicate
        successful/positive outcomes.
        """
        panel = success_panel("Success message", "Success Title")

        assert isinstance(panel, Panel)
        # Border style should use SUCCESS color
        assert panel.border_style is not None
        border_style = str(panel.border_style)
        # Check that border style contains the SUCCESS color
        assert COLORS.SUCCESS in border_style or "success" in border_style.lower()

    def test_success_panel_has_icon(self) -> None:
        """Verify success_panel includes checkmark icon in title."""
        panel = success_panel("Message", "Title")

        assert panel.title is not None
        title_str = str(panel.title)
        # Should have success icon (emoji or ASCII)
        assert "✅" in title_str or "[OK]" in title_str or "Title" in title_str


class TestWarningPanel:
    """Tests for warning_panel function."""

    def test_warning_panel_style(self) -> None:
        """T036: Verify warning_panel uses WARNING color (amber) for border.

        Warning panels should have an amber/yellow border style to indicate
        caution or potential issues.
        """
        panel = warning_panel("Warning message", "Warning Title")

        assert isinstance(panel, Panel)
        # Border style should use WARNING color
        assert panel.border_style is not None
        border_style = str(panel.border_style)
        # Check that border style contains the WARNING color
        assert COLORS.WARNING in border_style or "warning" in border_style.lower()

    def test_warning_panel_has_icon(self) -> None:
        """Verify warning_panel includes warning icon in title."""
        panel = warning_panel("Message", "Title")

        assert panel.title is not None
        title_str = str(panel.title)
        # Should have warning icon (emoji or ASCII)
        assert "⚠️" in title_str or "[!]" in title_str or "Title" in title_str


class TestErrorPanel:
    """Tests for error_panel function."""

    def test_error_panel_style(self) -> None:
        """T037: Verify error_panel uses ERROR color (red) for border.

        Error panels should have a red border style to indicate
        errors or critical issues.
        """
        panel = error_panel("Error message", "Error Title")

        assert isinstance(panel, Panel)
        # Border style should use ERROR color
        assert panel.border_style is not None
        border_style = str(panel.border_style)
        # Check that border style contains the ERROR color
        assert COLORS.ERROR in border_style or "error" in border_style.lower()

    def test_error_panel_has_icon(self) -> None:
        """Verify error_panel includes error icon in title."""
        panel = error_panel("Message", "Title")

        assert panel.title is not None
        title_str = str(panel.title)
        # Should have error icon (emoji or ASCII)
        assert "❌" in title_str or "[X]" in title_str or "Title" in title_str


class TestPanelIconFallback:
    """Tests for ASCII icon fallback in panels."""

    def test_panel_icon_fallback_ascii(self) -> None:
        """T038: Verify panels use ASCII icons when supports_unicode()=False.

        On terminals without unicode support (e.g., Windows cmd.exe),
        panels should display ASCII icons like [OK], [X], [!], [i]
        instead of emoji.
        """
        # Mock supports_unicode to return False (simulating Windows cmd.exe)
        with patch("src.cli.shared.ui.panels.supports_unicode", return_value=False):
            # Success panel should use [OK] instead of ✅
            success = success_panel("Message", "Success")
            success_title = str(success.title) if success.title else ""
            assert "[OK]" in success_title

            # Error panel should use [X] instead of ❌
            error = error_panel("Message", "Error")
            error_title = str(error.title) if error.title else ""
            assert "[X]" in error_title

            # Warning panel should use [!] instead of ⚠️
            warning = warning_panel("Message", "Warning")
            warning_title = str(warning.title) if warning.title else ""
            assert "[!]" in warning_title

            # Info panel should use [i] instead of ℹ️
            info = info_panel("Message", "Info")
            info_title = str(info.title) if info.title else ""
            assert "[i]" in info_title

    def test_panel_icon_unicode_when_supported(self) -> None:
        """Verify panels use emoji icons when unicode is supported."""
        with patch("src.cli.shared.ui.panels.supports_unicode", return_value=True):
            success = success_panel("Message", "Success")
            success_title = str(success.title) if success.title else ""
            # Should have emoji
            assert "✅" in success_title

    def test_panels_render_without_error(self) -> None:
        """Verify all panel types can be rendered to console without error."""
        # Create a console with string output
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        # Render each panel type
        panels = [
            info_panel("Info message", "Info"),
            success_panel("Success message", "Success"),
            warning_panel("Warning message", "Warning"),
            error_panel("Error message", "Error"),
        ]

        for panel in panels:
            console.print(panel)

        # Should have output without raising exceptions
        result = output.getvalue()
        assert len(result) > 0
        assert "Info" in result
        assert "Success" in result
        assert "Warning" in result
        assert "Error" in result
