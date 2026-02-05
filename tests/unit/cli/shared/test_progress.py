"""Tests for progress module - TDD RED phase.

Tests for spinners and progress indicators: spinner context manager,
PhaseSpinner for multi-step operations, and progress bar factories.
"""

from dataclasses import FrozenInstanceError
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.progress import Progress

from src.cli.shared.ui.progress import (
    Phase,
    PhaseSpinner,
    create_bar_progress,
    create_spinner_progress,
    spinner,
)


class TestSpinnerContextManager:
    """Tests for spinner() context manager."""

    def test_spinner_context_manager(self) -> None:
        """T046: Verify spinner() works as context manager with message.

        The spinner should provide visual feedback during operations and
        properly clean up on context exit.
        """
        # Test spinner with mock console in interactive mode
        with patch("src.cli.shared.ui.progress.is_interactive", return_value=True):
            # Create a mock Progress that we can track
            mock_progress = MagicMock()
            mock_progress.__enter__ = MagicMock(return_value=mock_progress)
            mock_progress.__exit__ = MagicMock(return_value=None)
            mock_progress.add_task = MagicMock(return_value=0)

            with patch(
                "src.cli.shared.ui.progress.create_spinner_progress",
                return_value=mock_progress,
            ):
                with spinner("Processing..."):
                    # Context should work without error
                    pass

                # Progress context should have been used
                mock_progress.__enter__.assert_called_once()
                mock_progress.__exit__.assert_called_once()
                mock_progress.add_task.assert_called_once_with(
                    description="Processing...", total=None
                )

    def test_spinner_non_interactive_fallback(self) -> None:
        """T047: Verify spinner() uses static fallback in non-interactive terminals.

        When terminal is not interactive (piped/redirected), spinner should
        print static messages instead of animated spinner.
        """
        output = StringIO()
        console = Console(file=output, force_terminal=False, width=80)

        with (  # noqa: SIM117 - separate patches from code under test
            patch("src.cli.shared.ui.progress.is_interactive", return_value=False),
            patch("src.cli.shared.ui.progress.create_console", return_value=console),
        ):
            with spinner("Processing..."):
                pass

        # Should have printed message (not animated)
        result = output.getvalue()
        assert "Processing" in result

    def test_spinner_handles_exception(self) -> None:
        """Verify spinner properly cleans up when exception occurs inside context."""
        with patch("src.cli.shared.ui.progress.is_interactive", return_value=True):
            mock_progress = MagicMock()
            mock_progress.__enter__ = MagicMock(return_value=mock_progress)
            mock_progress.__exit__ = MagicMock(return_value=None)
            mock_progress.add_task = MagicMock(return_value=0)

            with patch(
                "src.cli.shared.ui.progress.create_spinner_progress",
                return_value=mock_progress,
            ):
                with pytest.raises(ValueError), spinner("Processing..."):
                    raise ValueError("Test error")

                # Exit should still be called despite exception
                mock_progress.__exit__.assert_called_once()


class TestPhaseDataclass:
    """Tests for Phase dataclass."""

    def test_phase_dataclass_frozen(self) -> None:
        """T048: Verify Phase is a frozen dataclass (immutable).

        Phase instances should be immutable to prevent accidental modification
        during multi-step operations.
        """
        phase = Phase(name="Loading", description="Loading data from source")

        # Should have attributes
        assert phase.name == "Loading"
        assert phase.description == "Loading data from source"

        # Should be frozen (immutable)
        with pytest.raises(FrozenInstanceError):
            phase.name = "Modified"  # type: ignore[misc]

    def test_phase_equality(self) -> None:
        """Verify Phase instances with same values are equal."""
        phase1 = Phase(name="Loading", description="Loading data")
        phase2 = Phase(name="Loading", description="Loading data")

        assert phase1 == phase2

    def test_phase_different_values(self) -> None:
        """Verify Phase instances with different values are not equal."""
        phase1 = Phase(name="Loading", description="Loading data")
        phase2 = Phase(name="Processing", description="Processing data")

        assert phase1 != phase2


class TestPhaseSpinnerInitialState:
    """Tests for PhaseSpinner initialization."""

    def test_phase_spinner_initial_state(self) -> None:
        """T049: Verify PhaseSpinner initializes with list of phases.

        PhaseSpinner should track current phase index and provide access
        to all phases for display.
        """
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
            Phase(name="Step 3", description="Third step"),
        ]

        ps = PhaseSpinner(phases=phases)

        # Should have phases stored
        assert ps.phases == phases
        assert len(ps.phases) == 3

        # Should start at phase 0
        assert ps.current_index == 0

        # Should have current_phase property
        assert ps.current_phase == phases[0]

    def test_phase_spinner_empty_phases_raises(self) -> None:
        """Verify PhaseSpinner raises error with empty phases list."""
        with pytest.raises(ValueError, match="at least one phase"):
            PhaseSpinner(phases=[])


class TestPhaseSpinnerAdvance:
    """Tests for PhaseSpinner.advance() method."""

    def test_phase_spinner_advance(self) -> None:
        """T050: Verify PhaseSpinner.advance() moves to next phase.

        Calling advance() should increment the phase index and update
        the current phase.
        """
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
            Phase(name="Step 3", description="Third step"),
        ]

        ps = PhaseSpinner(phases=phases)

        # Initially at phase 0
        assert ps.current_index == 0
        assert ps.current_phase == phases[0]

        # Advance to phase 1
        ps.advance()
        assert ps.current_index == 1
        assert ps.current_phase == phases[1]

        # Advance to phase 2
        ps.advance()
        assert ps.current_index == 2
        assert ps.current_phase == phases[2]

    def test_phase_spinner_no_advance_past_end(self) -> None:
        """T053: Verify PhaseSpinner.advance() doesn't go past last phase.

        Calling advance() when already at the last phase should be a no-op
        (not raise error or wrap around).
        """
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
        ]

        ps = PhaseSpinner(phases=phases)

        # Advance to last phase
        ps.advance()
        assert ps.current_index == 1

        # Try to advance past end - should stay at last phase
        ps.advance()
        assert ps.current_index == 1
        assert ps.current_phase == phases[1]


class TestPhaseSpinnerComplete:
    """Tests for PhaseSpinner.complete() method."""

    def test_phase_spinner_complete(self) -> None:
        """T051: Verify PhaseSpinner.complete() marks all phases done.

        Calling complete() should mark the current operation as successfully
        finished and clean up the display.
        """
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
        ]

        ps = PhaseSpinner(phases=phases)

        # Complete should mark as successful
        ps.complete()

        assert ps.is_complete is True
        assert ps.is_failed is False


class TestPhaseSpinnerFail:
    """Tests for PhaseSpinner.fail() method."""

    def test_phase_spinner_fail(self) -> None:
        """T052: Verify PhaseSpinner.fail() marks operation as failed.

        Calling fail() should mark the operation as failed, optionally
        with an error message for display.
        """
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
        ]

        ps = PhaseSpinner(phases=phases)
        ps.advance()

        # Fail with message
        ps.fail("Connection timeout")

        assert ps.is_failed is True
        assert ps.is_complete is False
        assert ps.error_message == "Connection timeout"

    def test_phase_spinner_fail_without_message(self) -> None:
        """Verify PhaseSpinner.fail() works without message."""
        phases = [Phase(name="Step 1", description="First step")]

        ps = PhaseSpinner(phases=phases)
        ps.fail()

        assert ps.is_failed is True
        assert ps.error_message is None


class TestCreateBarProgress:
    """Tests for create_bar_progress factory."""

    def test_create_bar_progress(self) -> None:
        """T054: Verify create_bar_progress creates progress bar with bar, %, time.

        The progress bar should include:
        - Visual bar representation
        - Percentage complete
        - Elapsed/estimated time
        """
        progress = create_bar_progress()

        assert isinstance(progress, Progress)

        # Should have columns configured
        assert len(progress.columns) > 0

        # Test that it can be used (doesn't crash)
        with progress:
            task_id = progress.add_task("Testing...", total=100)
            progress.update(task_id, advance=50)


class TestCreateSpinnerProgress:
    """Tests for create_spinner_progress factory."""

    def test_create_spinner_progress(self) -> None:
        """Verify create_spinner_progress creates spinner progress."""
        progress = create_spinner_progress()

        assert isinstance(progress, Progress)

        # Should have spinner column configured
        assert len(progress.columns) > 0

        # Test that it can be used
        with progress:
            task_id = progress.add_task("Testing...", total=None)
            # Spinner tasks have indeterminate progress
            progress.update(task_id)


class TestPhaseSpinnerLive:
    """Tests for PhaseSpinner.live() context manager."""

    def test_phase_spinner_live_context(self) -> None:
        """Verify PhaseSpinner.live() works as context manager."""
        phases = [
            Phase(name="Step 1", description="First step"),
            Phase(name="Step 2", description="Second step"),
        ]

        ps = PhaseSpinner(phases=phases)

        # Should work as context manager (mocked for non-terminal)
        output = StringIO()
        console = Console(file=output, force_terminal=False)

        with (  # noqa: SIM117 - separate patches from code under test
            patch("src.cli.shared.ui.progress.create_console", return_value=console),
            patch("src.cli.shared.ui.progress.is_interactive", return_value=False),
        ):
            with ps.live():
                ps.advance()
                ps.complete()

        # Should have completed
        assert ps.is_complete is True

    def test_phase_spinner_non_interactive_prints_status(self) -> None:
        """Verify PhaseSpinner prints status messages in non-interactive mode."""
        phases = [
            Phase(name="Loading", description="Loading data"),
            Phase(name="Processing", description="Processing records"),
        ]

        ps = PhaseSpinner(phases=phases)

        output = StringIO()
        console = Console(file=output, force_terminal=False)

        with (  # noqa: SIM117 - separate patches from code under test
            patch("src.cli.shared.ui.progress.create_console", return_value=console),
            patch("src.cli.shared.ui.progress.is_interactive", return_value=False),
        ):
            with ps.live():
                ps.advance()
                ps.complete()

        result = output.getvalue()
        # Should have printed start and completion messages
        assert "Starting" in result or "operation" in result
        assert "complete" in result.lower() or "Done" in result
