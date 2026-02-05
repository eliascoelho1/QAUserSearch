"""Tests for src.cli.shared module exports.

Verifies that all public components are properly exported and importable
through the module's public interface.
"""

from __future__ import annotations


class TestUIExports:
    """Tests for src.cli.shared.ui exports."""

    def test_theme_exports(self) -> None:
        """Verify theme components are exported from ui module."""
        from src.cli.shared.ui import (
            COLORS,
            ICONS_ASCII,
            ICONS_EMOJI,
            IconType,
            get_icon,
            get_questionary_style,
            get_rich_theme,
        )

        assert COLORS is not None
        assert ICONS_ASCII is not None
        assert ICONS_EMOJI is not None
        assert IconType is not None
        assert callable(get_icon)
        assert callable(get_questionary_style)
        assert callable(get_rich_theme)

    def test_panels_exports(self) -> None:
        """Verify panel components are exported from ui module."""
        from src.cli.shared.ui import (
            create_panel,
            error_panel,
            info_panel,
            success_panel,
            warning_panel,
        )

        assert callable(create_panel)
        assert callable(error_panel)
        assert callable(info_panel)
        assert callable(success_panel)
        assert callable(warning_panel)

    def test_progress_exports(self) -> None:
        """Verify progress components are exported from ui module."""
        from src.cli.shared.ui import (
            Phase,
            PhaseSpinner,
            create_bar_progress,
            create_spinner_progress,
            spinner,
        )

        assert Phase is not None
        assert PhaseSpinner is not None
        assert callable(create_bar_progress)
        assert callable(create_spinner_progress)
        assert callable(spinner)

    def test_prompts_exports(self) -> None:
        """Verify prompt components are exported from ui module."""
        from src.cli.shared.ui import (
            ApprovalResult,
            ask_approval,
            ask_checkbox,
            ask_confirm,
            ask_select,
            ask_text,
        )

        assert ApprovalResult is not None
        assert callable(ask_approval)
        assert callable(ask_checkbox)
        assert callable(ask_confirm)
        assert callable(ask_select)
        assert callable(ask_text)

    def test_ui_star_import(self) -> None:
        """Verify 'from src.cli.shared.ui import *' works without errors."""
        # This test verifies __all__ is properly defined and all exports work
        import src.cli.shared.ui as ui_module

        all_exports = ui_module.__all__

        # Verify __all__ is defined and non-empty
        assert isinstance(all_exports, list)
        assert len(all_exports) > 0

        # Verify all items in __all__ are actually exported
        for name in all_exports:
            assert hasattr(ui_module, name), f"'{name}' in __all__ but not exported"


class TestUtilsExports:
    """Tests for src.cli.shared.utils exports."""

    def test_terminal_exports(self) -> None:
        """Verify terminal utilities are exported from utils module."""
        from src.cli.shared.utils import (
            create_console,
            get_terminal_size,
            is_interactive,
            supports_color,
            supports_unicode,
        )

        assert callable(create_console)
        assert callable(get_terminal_size)
        assert callable(is_interactive)
        assert callable(supports_color)
        assert callable(supports_unicode)

    def test_utils_star_import(self) -> None:
        """Verify 'from src.cli.shared.utils import *' works without errors."""
        import src.cli.shared.utils as utils_module

        all_exports = utils_module.__all__

        # Verify __all__ is defined and non-empty
        assert isinstance(all_exports, list)
        assert len(all_exports) > 0

        # Verify all items in __all__ are actually exported
        for name in all_exports:
            assert hasattr(utils_module, name), f"'{name}' in __all__ but not exported"


class TestSharedExports:
    """Tests for src.cli.shared module re-exports."""

    def test_submodules_exported(self) -> None:
        """Verify ui and utils submodules are re-exported."""
        from src.cli.shared import ui, utils

        assert ui is not None
        assert utils is not None

    def test_ui_reexports(self) -> None:
        """Verify commonly used ui components are re-exported at top level."""
        from src.cli.shared import (
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

        # Theme
        assert COLORS is not None
        assert IconType is not None
        assert callable(get_icon)
        assert callable(get_questionary_style)
        assert callable(get_rich_theme)

        # Panels
        assert callable(create_panel)
        assert callable(error_panel)
        assert callable(info_panel)
        assert callable(success_panel)
        assert callable(warning_panel)

        # Progress
        assert Phase is not None
        assert PhaseSpinner is not None
        assert callable(create_bar_progress)
        assert callable(spinner)

        # Prompts
        assert ApprovalResult is not None
        assert callable(ask_approval)
        assert callable(ask_checkbox)
        assert callable(ask_confirm)
        assert callable(ask_select)
        assert callable(ask_text)

    def test_utils_reexports(self) -> None:
        """Verify commonly used utils are re-exported at top level."""
        from src.cli.shared import (
            create_console,
            get_terminal_size,
            is_interactive,
            supports_color,
            supports_unicode,
        )

        assert callable(create_console)
        assert callable(get_terminal_size)
        assert callable(is_interactive)
        assert callable(supports_color)
        assert callable(supports_unicode)

    def test_shared_star_import(self) -> None:
        """Verify 'from src.cli.shared import *' works without errors."""
        import src.cli.shared as shared_module

        all_exports = shared_module.__all__

        # Verify __all__ is defined and non-empty
        assert isinstance(all_exports, list)
        assert len(all_exports) > 0

        # Verify all items in __all__ are actually exported
        for name in all_exports:
            assert hasattr(shared_module, name), f"'{name}' in __all__ but not exported"


class TestAllExportsImportable:
    """Master test to verify all exports are importable via module public interface."""

    def test_all_exports_importable(self) -> None:
        """Comprehensive test that all public exports work correctly.

        This test verifies SC-001: 100% dos componentes importáveis via
        `from src.cli.shared.ui import *`
        """
        # Test 1: ui module star import
        import src.cli.shared.ui as ui_module

        for name in ui_module.__all__:
            obj = getattr(ui_module, name)
            assert obj is not None, f"ui.{name} is None"

        # Test 2: utils module star import
        import src.cli.shared.utils as utils_module

        for name in utils_module.__all__:
            obj = getattr(utils_module, name)
            assert obj is not None, f"utils.{name} is None"

        # Test 3: shared module star import
        import src.cli.shared as shared_module

        for name in shared_module.__all__:
            obj = getattr(shared_module, name)
            assert obj is not None, f"shared.{name} is None"

        # Test 4: Count total exports (for verification)
        ui_count = len(ui_module.__all__)
        utils_count = len(utils_module.__all__)

        # UI should have: 7 theme + 5 panels + 5 progress + 6 prompts = 23
        assert ui_count >= 20, f"Expected at least 20 ui exports, got {ui_count}"

        # Utils should have: 5 terminal functions
        assert utils_count >= 5, f"Expected at least 5 utils exports, got {utils_count}"
