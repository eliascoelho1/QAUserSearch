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


class TestApprovalResult:
    """Tests for ApprovalResult enum."""

    def test_approval_result_enum_values(self) -> None:
        """T080: Verify ApprovalResult enum has all expected values.

        ApprovalResult should have values for APPROVE, EDIT, REJECT, SKIP, and CANCEL
        to support all possible user decisions in approval workflows.
        """
        from src.cli.shared.ui.prompts import ApprovalResult

        # All expected values should exist
        assert hasattr(ApprovalResult, "APPROVE")
        assert hasattr(ApprovalResult, "EDIT")
        assert hasattr(ApprovalResult, "REJECT")
        assert hasattr(ApprovalResult, "SKIP")
        assert hasattr(ApprovalResult, "CANCEL")

        # Values should be strings
        assert ApprovalResult.APPROVE.value == "approve"
        assert ApprovalResult.EDIT.value == "edit"
        assert ApprovalResult.REJECT.value == "reject"
        assert ApprovalResult.SKIP.value == "skip"
        assert ApprovalResult.CANCEL.value == "cancel"

    def test_approval_result_inherits_str(self) -> None:
        """T081: Verify ApprovalResult inherits from str for JSON serialization.

        By inheriting from str, ApprovalResult values can be serialized to JSON
        directly without conversion.
        """
        import json

        from src.cli.shared.ui.prompts import ApprovalResult

        # Should inherit from str
        assert isinstance(ApprovalResult.APPROVE, str)
        assert isinstance(ApprovalResult.EDIT, str)

        # Should be usable as string values (value attribute)
        assert ApprovalResult.APPROVE.value == "approve"
        assert ApprovalResult.REJECT.value == "reject"

        # Since it inherits from str, JSON serialization works directly
        result = {"status": ApprovalResult.APPROVE}
        json_str = json.dumps(result)
        assert '"approve"' in json_str


class TestAskApproval:
    """Tests for ask_approval() function."""

    def test_ask_approval_all_options(self) -> None:
        """T082: Verify ask_approval() shows all options by default.

        When called without options, ask_approval should present all five
        choices: Approve, Edit, Reject, Skip, and Cancel.
        """
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "✅ Aprovar"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_approval("Aprovar item?")

            assert result == ApprovalResult.APPROVE
            mock_select.assert_called_once()

            # Check that all 5 options were provided
            call_kwargs = mock_select.call_args
            choices = call_kwargs[1].get("choices", [])
            assert len(choices) == 5

    def test_ask_approval_no_edit(self) -> None:
        """T083: Verify ask_approval() can hide edit option.

        When allow_edit=False, the Edit option should not appear
        in the choices list.
        """
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "✅ Aprovar"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_approval("Aprovar item?", allow_edit=False)

            assert result == ApprovalResult.APPROVE

            # Check that only 4 options were provided (no Edit)
            call_kwargs = mock_select.call_args
            choices = call_kwargs[1].get("choices", [])
            assert len(choices) == 4
            # Edit option should not be in choices
            choice_texts = [c if isinstance(c, str) else str(c) for c in choices]
            assert not any("Editar" in c for c in choice_texts)

    def test_ask_approval_no_skip(self) -> None:
        """T084: Verify ask_approval() can hide skip option.

        When allow_skip=False, the Skip option should not appear
        in the choices list.
        """
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "✅ Aprovar"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_approval("Aprovar item?", allow_skip=False)

            assert result == ApprovalResult.APPROVE

            # Check that only 4 options were provided (no Skip)
            call_kwargs = mock_select.call_args
            choices = call_kwargs[1].get("choices", [])
            assert len(choices) == 4
            # Skip option should not be in choices
            choice_texts = [c if isinstance(c, str) else str(c) for c in choices]
            assert not any("Pular" in c for c in choice_texts)

    def test_ask_approval_keyboard_interrupt(self) -> None:
        """T085: Verify ask_approval() returns CANCEL on Ctrl+C.

        When user presses Ctrl+C, ask_approval should catch KeyboardInterrupt
        and return ApprovalResult.CANCEL gracefully.
        """
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        mock_prompt = MagicMock()
        mock_prompt.ask.side_effect = KeyboardInterrupt()

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
        ):
            mock_select.return_value = mock_prompt

            result = ask_approval("Aprovar item?")

            assert result == ApprovalResult.CANCEL

    def test_ask_approval_non_interactive_returns_cancel(self) -> None:
        """Verify ask_approval() returns CANCEL in non-interactive mode."""
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        with patch("src.cli.shared.ui.prompts.is_interactive", return_value=False):
            result = ask_approval("Aprovar item?")
            assert result == ApprovalResult.CANCEL

    def test_ask_approval_maps_all_selections(self) -> None:
        """Verify ask_approval() correctly maps all user selections."""
        from src.cli.shared.ui.prompts import ApprovalResult, ask_approval

        # Test mapping for each possible selection
        selection_to_result = {
            "✅ Aprovar": ApprovalResult.APPROVE,
            "✏️ Editar": ApprovalResult.EDIT,
            "❌ Rejeitar": ApprovalResult.REJECT,
            "⏭️ Pular": ApprovalResult.SKIP,
            "🚫 Cancelar": ApprovalResult.CANCEL,
        }

        for selection, expected_result in selection_to_result.items():
            mock_prompt = MagicMock()
            mock_prompt.ask.return_value = selection

            with (
                patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
                patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
            ):
                mock_select.return_value = mock_prompt

                result = ask_approval("Test?")

                assert (
                    result == expected_result
                ), f"Expected {expected_result} for selection '{selection}'"

    def test_ask_approval_uses_questionary_style(self) -> None:
        """Verify ask_approval() applies questionary style from theme."""
        from src.cli.shared.ui.prompts import ask_approval

        mock_prompt = MagicMock()
        mock_prompt.ask.return_value = "✅ Aprovar"

        with (
            patch("src.cli.shared.ui.prompts.is_interactive", return_value=True),
            patch("src.cli.shared.ui.prompts.questionary.select") as mock_select,
            patch("src.cli.shared.ui.prompts.get_questionary_style") as mock_style,
        ):
            mock_select.return_value = mock_prompt
            mock_style.return_value = MagicMock()

            ask_approval("Aprovar?")

            mock_style.assert_called_once()
            call_kwargs = mock_select.call_args
            assert "style" in call_kwargs[1]
