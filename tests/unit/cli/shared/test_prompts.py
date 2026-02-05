"""Tests for prompts module - TDD RED phase.

Tests for interactive prompts: text input, confirmation, selection,
checkbox, and keyboard interrupt handling.
"""

from unittest.mock import MagicMock, patch


class TestAskText:
    """Tests for ask_text() function."""

    def test_ask_text_returns_input(self) -> None:
        """T065: Verify ask_text() returns user input as string.

        When user provides text input, ask_text should return
        the input string.
        """
        from src.cli.shared.ui.prompts import ask_text

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "user input"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.text") as mock_text,
        ):
            mock_text.return_value = mock_prompt

            result = ask_text("Enter value:")

            assert result == "user input"
            mock_text.assert_called_once()

    def test_ask_text_keyboard_interrupt_returns_none(self) -> None:
        """T066: Verify ask_text() returns None on Ctrl+C.

        When user presses Ctrl+C, ask_text should catch KeyboardInterrupt
        and return None gracefully.
        """
        from src.cli.shared.ui.prompts import ask_text

        mock_prompt = MagicMock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.text") as mock_text,
        ):
            mock_text.return_value = mock_prompt

            result = ask_text("Enter value:")

            assert result is None

    def test_ask_text_with_default(self) -> None:
        """Verify ask_text() passes default value to questionary."""
        from src.cli.shared.ui.prompts import ask_text

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "default_value"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.text") as mock_text,
        ):
            mock_text.return_value = mock_prompt

            result = ask_text("Enter value:", default="default_value")

            assert result == "default_value"
            mock_text.assert_called_once()
            # Check that default was passed
            call_kwargs = mock_text.call_args
            assert call_kwargs[1].get("default") == "default_value"


class TestAskConfirm:
    """Tests for ask_confirm() function."""

    def test_ask_confirm_returns_bool(self) -> None:
        """T067: Verify ask_confirm() returns boolean value.

        When user confirms or denies, ask_confirm should return
        True or False respectively.
        """
        from src.cli.shared.ui.prompts import ask_confirm

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = True

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = mock_prompt

            result = ask_confirm("Continue?")

            assert result is True
            mock_confirm.assert_called_once()

    def test_ask_confirm_returns_false(self) -> None:
        """Verify ask_confirm() returns False when user denies."""
        from src.cli.shared.ui.prompts import ask_confirm

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = False

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = mock_prompt

            result = ask_confirm("Continue?")

            assert result is False

    def test_ask_confirm_keyboard_interrupt_returns_none(self) -> None:
        """T068: Verify ask_confirm() returns None on Ctrl+C.

        When user presses Ctrl+C, ask_confirm should catch KeyboardInterrupt
        and return None gracefully.
        """
        from src.cli.shared.ui.prompts import ask_confirm

        mock_prompt = MagicMock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = mock_prompt

            result = ask_confirm("Continue?")

            assert result is None

    def test_ask_confirm_with_default(self) -> None:
        """Verify ask_confirm() passes default value to questionary."""
        from src.cli.shared.ui.prompts import ask_confirm

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = False

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = mock_prompt

            result = ask_confirm("Continue?", default=False)

            assert result is False
            call_kwargs = mock_confirm.call_args
            assert call_kwargs[1].get("default") is False


class TestAskSelect:
    """Tests for ask_select() function."""

    def test_ask_select_returns_choice(self) -> None:
        """T069: Verify ask_select() returns selected choice.

        When user selects an option, ask_select should return
        the selected value.
        """
        from src.cli.shared.ui.prompts import ask_select

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "Option B"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_select(
                "Choose option:", choices=["Option A", "Option B", "Option C"]
            )

            assert result == "Option B"
            mock_select.assert_called_once()

    def test_ask_select_keyboard_interrupt_returns_none(self) -> None:
        """T070: Verify ask_select() returns None on Ctrl+C.

        When user presses Ctrl+C, ask_select should catch KeyboardInterrupt
        and return None gracefully.
        """
        from src.cli.shared.ui.prompts import ask_select

        mock_prompt = MagicMock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_select("Choose option:", choices=["Option A", "Option B"])

            assert result is None

    def test_ask_select_with_instruction(self) -> None:
        """Verify ask_select() passes instruction in Portuguese."""
        from src.cli.shared.ui.prompts import ask_select

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "Option A"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            ask_select("Choose:", choices=["Option A"])

            call_kwargs = mock_select.call_args
            # Should have instruction parameter (in Portuguese)
            assert "instruction" in call_kwargs[1]


class TestAskCheckbox:
    """Tests for ask_checkbox() function."""

    def test_ask_checkbox_returns_list(self) -> None:
        """T071: Verify ask_checkbox() returns list of selected choices.

        When user selects multiple options, ask_checkbox should return
        a list with all selected values.
        """
        from src.cli.shared.ui.prompts import ask_checkbox

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = ["Option A", "Option C"]

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.checkbox") as mock_checkbox,
        ):
            mock_checkbox.return_value = mock_prompt

            result = ask_checkbox(
                "Select options:",
                choices=["Option A", "Option B", "Option C"],
            )

            assert result == ["Option A", "Option C"]
            mock_checkbox.assert_called_once()

    def test_ask_checkbox_keyboard_interrupt_returns_none(self) -> None:
        """T072: Verify ask_checkbox() returns None on Ctrl+C.

        When user presses Ctrl+C, ask_checkbox should catch KeyboardInterrupt
        and return None gracefully.
        """
        from src.cli.shared.ui.prompts import ask_checkbox

        mock_prompt = MagicMock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.checkbox") as mock_checkbox,
        ):
            mock_checkbox.return_value = mock_prompt

            result = ask_checkbox("Select:", choices=["A", "B"])

            assert result is None

    def test_ask_checkbox_with_instruction(self) -> None:
        """Verify ask_checkbox() passes instruction in Portuguese."""
        from src.cli.shared.ui.prompts import ask_checkbox

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = []

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.checkbox") as mock_checkbox,
        ):
            mock_checkbox.return_value = mock_prompt

            ask_checkbox("Select:", choices=["A"])

            call_kwargs = mock_checkbox.call_args
            # Should have instruction parameter (in Portuguese)
            assert "instruction" in call_kwargs[1]


class TestPromptsNonInteractive:
    """Tests for non-interactive terminal behavior."""

    def test_prompts_non_interactive_returns_none(self) -> None:
        """T073: Verify all prompts return None when terminal is non-interactive.

        When terminal is piped/redirected (not a TTY), prompts cannot
        get user input and should return None immediately.
        """
        from src.cli.shared.ui.prompts import (
            ask_checkbox,
            ask_confirm,
            ask_select,
            ask_text,
        )

        with patch("src.cli.shared.ui.prompts.is_interactive", return_value=False):
            # All prompt functions should return None in non-interactive mode
            assert ask_text("Enter:") is None
            assert ask_confirm("Continue?") is None
            assert ask_select("Choose:", choices=["A", "B"]) is None
            assert ask_checkbox("Select:", choices=["A", "B"]) is None


class TestPromptsStyle:
    """Tests for prompt styling consistency."""

    def test_ask_text_uses_questionary_style(self) -> None:
        """Verify ask_text() applies questionary style from theme."""
        from src.cli.shared.ui.prompts import ask_text

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "input"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.text") as mock_text,
            patch("src.cli.shared.ui.prompts.get_questionary_style") as mock_style,
        ):
            mock_text.return_value = mock_prompt
            mock_style.return_value = MagicMock()

            ask_text("Enter:")

            # Should get questionary style
            mock_style.assert_called_once()
            # Style should be passed to questionary
            call_kwargs = mock_text.call_args
            assert "style" in call_kwargs[1]

    def test_ask_confirm_uses_questionary_style(self) -> None:
        """Verify ask_confirm() applies questionary style from theme."""
        from src.cli.shared.ui.prompts import ask_confirm

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = True

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.confirm") as mock_confirm,
            patch("src.cli.shared.ui.prompts.get_questionary_style") as mock_style,
        ):
            mock_confirm.return_value = mock_prompt
            mock_style.return_value = MagicMock()

            ask_confirm("Continue?")

            mock_style.assert_called_once()
            call_kwargs = mock_confirm.call_args
            assert "style" in call_kwargs[1]

    def test_ask_select_uses_questionary_style(self) -> None:
        """Verify ask_select() applies questionary style from theme."""
        from src.cli.shared.ui.prompts import ask_select

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "A"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
            patch("src.cli.shared.ui.prompts.get_questionary_style") as mock_style,
        ):
            mock_select.return_value = mock_prompt
            mock_style.return_value = MagicMock()

            ask_select("Choose:", choices=["A"])

            mock_style.assert_called_once()
            call_kwargs = mock_select.call_args
            assert "style" in call_kwargs[1]

    def test_ask_checkbox_uses_questionary_style(self) -> None:
        """Verify ask_checkbox() applies questionary style from theme."""
        from src.cli.shared.ui.prompts import ask_checkbox

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = []

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.checkbox") as mock_checkbox,
            patch("src.cli.shared.ui.prompts.get_questionary_style") as mock_style,
        ):
            mock_checkbox.return_value = mock_prompt
            mock_style.return_value = MagicMock()

            ask_checkbox("Select:", choices=["A"])

            mock_style.assert_called_once()
            call_kwargs = mock_checkbox.call_args
            assert "style" in call_kwargs[1]
