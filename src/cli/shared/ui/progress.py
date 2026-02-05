"""Progress indicators for CLI UI.

Provides spinners and progress bars for visual feedback during operations.
Includes context managers for simple spinners and PhaseSpinner for multi-step
operations with progress tracking.

Example:
    >>> from src.cli.shared.ui.progress import spinner, PhaseSpinner, Phase
    >>> with spinner("Processing..."):
    ...     # Long running operation
    ...     pass

    >>> phases = [Phase("Load", "Loading data"), Phase("Process", "Processing")]
    >>> ps = PhaseSpinner(phases)
    >>> with ps.live():
    ...     ps.advance()
    ...     ps.complete()
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from src.cli.shared.ui.theme import COLORS, IconType, get_icon
from src.cli.shared.utils.terminal import create_console, is_interactive

if TYPE_CHECKING:
    from rich.console import Console


@dataclass(frozen=True)
class Phase:
    """Represents a single phase in a multi-step operation.

    Phases are immutable to prevent accidental modification during operations.

    Attributes:
        name: Short name for the phase (displayed in UI).
        description: Longer description explaining what the phase does.

    Example:
        >>> phase = Phase("Loading", "Loading data from external source")
        >>> print(f"{phase.name}: {phase.description}")
        Loading: Loading data from external source
    """

    name: str
    description: str


@dataclass
class PhaseSpinner:
    """Multi-phase spinner for tracking progress through sequential steps.

    Manages a list of phases and provides visual feedback as each phase
    completes. Supports both interactive (animated) and non-interactive
    (static text) modes.

    Attributes:
        phases: List of Phase objects representing operation steps.
        current_index: Index of the currently active phase (0-based).
        is_complete: True if operation completed successfully.
        is_failed: True if operation failed.
        error_message: Error message if operation failed.

    Example:
        >>> phases = [
        ...     Phase("Load", "Loading data"),
        ...     Phase("Process", "Processing records"),
        ...     Phase("Save", "Saving results"),
        ... ]
        >>> ps = PhaseSpinner(phases)
        >>> with ps.live():
        ...     ps.advance()  # Move to "Process"
        ...     ps.advance()  # Move to "Save"
        ...     ps.complete()
    """

    phases: list[Phase]
    current_index: int = field(default=0, init=False)
    is_complete: bool = field(default=False, init=False)
    is_failed: bool = field(default=False, init=False)
    error_message: str | None = field(default=None, init=False)
    _console: "Console | None" = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate phases after initialization."""
        if not self.phases:
            raise ValueError("PhaseSpinner requires at least one phase")

    @property
    def current_phase(self) -> Phase:
        """Get the currently active phase.

        Returns:
            The Phase object at the current index.
        """
        return self.phases[self.current_index]

    def advance(self) -> None:
        """Move to the next phase.

        If already at the last phase, this is a no-op (does not wrap around
        or raise an error).
        """
        if self.current_index < len(self.phases) - 1:
            self.current_index += 1

    def complete(self) -> None:
        """Mark the operation as successfully completed.

        Sets is_complete to True and is_failed to False.
        """
        self.is_complete = True
        self.is_failed = False

    def fail(self, message: str | None = None) -> None:
        """Mark the operation as failed.

        Args:
            message: Optional error message to display.
        """
        self.is_failed = True
        self.is_complete = False
        self.error_message = message

    @contextmanager
    def live(self) -> Iterator["PhaseSpinner"]:
        """Context manager for displaying live phase progress.

        In interactive terminals, displays an animated spinner with current
        phase information. In non-interactive mode, prints static phase
        updates.

        Yields:
            Self for method chaining within the context.

        Example:
            >>> with ps.live():
            ...     # Do work
            ...     ps.advance()
            ...     ps.complete()
        """
        self._console = create_console()

        if is_interactive():
            # Interactive mode: use Rich Live display
            from rich.live import Live
            from rich.table import Table

            def render_status() -> Table:
                """Render current status as a Rich Table."""
                table = Table.grid(padding=(0, 1))
                table.add_column(no_wrap=True)
                table.add_column()

                use_unicode = True  # Console handles fallback
                for i, phase in enumerate(self.phases):
                    if i < self.current_index:
                        # Completed phase
                        icon = get_icon(IconType.SUCCESS, use_unicode=use_unicode)
                        style = f"[{COLORS.SUCCESS}]"
                    elif i == self.current_index:
                        if self.is_failed:
                            icon = get_icon(IconType.ERROR, use_unicode=use_unicode)
                            style = f"[{COLORS.ERROR}]"
                        elif self.is_complete:
                            icon = get_icon(IconType.SUCCESS, use_unicode=use_unicode)
                            style = f"[{COLORS.SUCCESS}]"
                        else:
                            icon = "..."
                            style = f"[{COLORS.PRIMARY}]"
                    else:
                        # Pending phase
                        icon = " "
                        style = f"[{COLORS.MUTED}]"

                    table.add_row(
                        f"{style}{icon}[/]",
                        f"{style}{phase.name}: {phase.description}[/]",
                    )

                if self.is_failed and self.error_message:
                    table.add_row("", f"[{COLORS.ERROR}]Error: {self.error_message}[/]")

                return table

            with Live(render_status(), console=self._console, refresh_per_second=10):
                try:
                    yield self
                finally:
                    # Final render happens automatically on exit
                    pass
        else:
            # Non-interactive mode: print static updates
            assert self._console is not None
            self._console.print(f"[{COLORS.PRIMARY}]Starting operation...[/]")
            try:
                yield self
            finally:
                # Print final status
                if self.is_complete:
                    self._console.print(
                        f"[{COLORS.SUCCESS}]{get_icon(IconType.SUCCESS)} "
                        f"Operation complete[/]"
                    )
                elif self.is_failed:
                    msg = f" - {self.error_message}" if self.error_message else ""
                    self._console.print(
                        f"[{COLORS.ERROR}]{get_icon(IconType.ERROR)} "
                        f"Operation failed{msg}[/]"
                    )


def create_spinner_progress() -> Progress:
    """Create a Progress instance configured for spinner display.

    Returns a Progress with spinner animation and text columns, suitable
    for indeterminate-duration operations.

    Returns:
        Progress: Configured Rich Progress instance.

    Example:
        >>> progress = create_spinner_progress()
        >>> with progress:
        ...     task_id = progress.add_task("Processing...", total=None)
        ...     # Do work
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def create_bar_progress() -> Progress:
    """Create a Progress instance configured for progress bar display.

    Returns a Progress with bar, percentage, and time columns, suitable
    for operations with known total steps.

    Returns:
        Progress: Configured Rich Progress instance.

    Example:
        >>> progress = create_bar_progress()
        >>> with progress:
        ...     task_id = progress.add_task("Downloading...", total=100)
        ...     for i in range(100):
        ...         progress.update(task_id, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TextColumn("ETA:"),
        TimeRemainingColumn(),
    )


@contextmanager
def spinner(message: str) -> Iterator[None]:
    """Context manager for displaying a spinner during an operation.

    In interactive terminals, shows an animated spinner with the message.
    In non-interactive mode, prints the message without animation.

    Args:
        message: Text to display alongside the spinner.

    Yields:
        None - use the context for executing operations.

    Example:
        >>> with spinner("Processing files..."):
        ...     process_files()  # Spinner shows during this
    """
    if is_interactive():
        progress = create_spinner_progress()
        with progress:
            progress.add_task(description=message, total=None)
            yield
    else:
        console = create_console()
        console.print(f"[{COLORS.PRIMARY}]{message}[/]")
        try:
            yield
        finally:
            console.print(f"[{COLORS.SUCCESS}]{get_icon(IconType.SUCCESS)} Done[/]")
