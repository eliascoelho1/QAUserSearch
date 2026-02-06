"""Command processing for CLI Chat.

This module provides:
- CommandType: Enum of available commands
- CommandResult: Result of executing a command
- is_command: Check if text is a command
- parse_command: Parse text into CommandType
- execute_command: Execute a command and return result

Example:
    >>> from src.cli.chat.commands import is_command, parse_command, execute_command
    >>> if is_command("/help"):
    ...     cmd = parse_command("/help")
    ...     if cmd:
    ...         result = execute_command(cmd, session, console)
    ...         if result.output:
    ...             console.print(result.output)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from src.cli.chat.session import ChatSession, QueryRecord


class CommandType(str, Enum):
    """Enum of available chat commands.

    Values:
        EXIT: Exit the chat session (/exit or /quit)
        HELP: Show help information (/help)
        CLEAR: Clear session history and screen (/clear)
        HISTORY: Show query history (/history)
        EXECUTE: Execute last query (coming soon) (/execute)
        MOCK: Toggle mock mode (/mock)
    """

    EXIT = "exit"
    HELP = "help"
    CLEAR = "clear"
    HISTORY = "history"
    EXECUTE = "execute"
    MOCK = "mock"


# Command aliases mapping
_COMMAND_ALIASES: dict[str, CommandType] = {
    "quit": CommandType.EXIT,  # /quit is alias for /exit
}


@dataclass
class CommandResult:
    """Result of executing a command.

    Attributes:
        should_exit: Whether the chat loop should exit after this command.
        message: Optional text message to display (plain text).
        output: Optional Rich Renderable to display (Panel, Table, etc.).

    Example:
        >>> result = CommandResult(should_exit=True, message="Até logo!")
        >>> if result.message:
        ...     print(result.message)
        >>> if result.output:
        ...     console.print(result.output)
    """

    should_exit: bool = field(default=False)
    message: str | None = field(default=None)
    output: RenderableType | None = field(default=None)


def is_command(text: str) -> bool:
    """Check if text is a command (starts with '/').

    Args:
        text: The input text to check.

    Returns:
        True if text starts with '/', False otherwise.

    Example:
        >>> is_command("/help")
        True
        >>> is_command("buscar usuários")
        False
    """
    return text.startswith("/")


def parse_command(text: str) -> CommandType | None:
    """Parse text into a CommandType.

    Supports case-insensitive matching and aliases (e.g., /quit -> EXIT).

    Args:
        text: The command text (e.g., "/exit", "/HELP").

    Returns:
        CommandType if recognized, None if unknown or invalid.

    Example:
        >>> parse_command("/exit")
        CommandType.EXIT
        >>> parse_command("/quit")  # alias
        CommandType.EXIT
        >>> parse_command("/unknown")
        None
    """
    if not text or not text.startswith("/"):
        return None

    # Extract command name (lowercase for case-insensitive matching)
    command_name = text[1:].lower().strip()

    if not command_name:
        return None

    # Check aliases first
    if command_name in _COMMAND_ALIASES:
        return _COMMAND_ALIASES[command_name]

    # Try to match enum value
    try:
        return CommandType(command_name)
    except ValueError:
        return None


def execute_command(
    command_type: CommandType,
    session: "ChatSession",
    console: Console,
) -> CommandResult:
    """Execute a command and return the result.

    Args:
        command_type: The type of command to execute.
        session: The current chat session (may be modified).
        console: Rich Console for output operations (e.g., clear).

    Returns:
        CommandResult with execution results.

    Example:
        >>> result = execute_command(CommandType.EXIT, session, console)
        >>> if result.should_exit:
        ...     break  # Exit chat loop
    """
    match command_type:
        case CommandType.EXIT:
            return _execute_exit()
        case CommandType.HELP:
            return _execute_help()
        case CommandType.CLEAR:
            return _execute_clear(session, console)
        case CommandType.HISTORY:
            return _execute_history(session)
        case CommandType.EXECUTE:
            return _execute_execute()
        case CommandType.MOCK:
            return _execute_mock(session)


def _execute_exit() -> CommandResult:
    """Execute EXIT command - exit the chat session."""
    return CommandResult(
        should_exit=True,
        message="Até logo! Saindo do chat...",
    )


def _execute_help() -> CommandResult:
    """Execute HELP command - show help information."""
    help_content = _build_help_panel()
    return CommandResult(
        should_exit=False,
        output=help_content,
    )


def _execute_clear(session: "ChatSession", console: Console) -> CommandResult:
    """Execute CLEAR command - clear session and screen."""
    session.clear()
    console.clear()
    return CommandResult(
        should_exit=False,
        message="Histórico limpo.",
    )


def _execute_history(session: "ChatSession") -> CommandResult:
    """Execute HISTORY command - show query history."""
    history = session.get_history()

    if not history:
        return CommandResult(
            should_exit=False,
            output=_build_empty_history_panel(),
        )

    return CommandResult(
        should_exit=False,
        output=_build_history_table(history),
    )


def _execute_execute() -> CommandResult:
    """Execute EXECUTE command - run last query (coming soon)."""
    return CommandResult(
        should_exit=False,
        message="Funcionalidade em breve! Execute queries ainda não está implementado.",
    )


def _execute_mock(session: "ChatSession") -> CommandResult:
    """Execute MOCK command - toggle mock mode."""
    new_mode = session.toggle_mock_mode()

    if new_mode:
        message = "Modo mock ativado. Usando respostas simuladas."
    else:
        message = "Modo mock desativado. Usando conexão real."

    return CommandResult(
        should_exit=False,
        message=message,
    )


def _build_help_panel() -> Panel:
    """Build the help panel with command descriptions."""
    commands_table = Table(show_header=False, box=None, padding=(0, 2))
    commands_table.add_column("Command", style="cyan bold")
    commands_table.add_column("Description")

    commands_table.add_row("/exit, /quit", "Sair do chat")
    commands_table.add_row("/help", "Mostrar esta ajuda")
    commands_table.add_row("/clear", "Limpar histórico e tela")
    commands_table.add_row("/history", "Mostrar histórico de queries")
    commands_table.add_row("/execute", "Executar última query (em breve)")
    commands_table.add_row("/mock", "Alternar modo mock on/off")

    tips = Text()
    tips.append("\n\nDicas:\n", style="bold")
    tips.append("• Digite sua pergunta em linguagem natural\n", style="dim")
    tips.append("• Exemplo: 'buscar usuários com cartão ativo'\n", style="dim")
    tips.append("• Use Ctrl+C para cancelar operação atual\n", style="dim")

    content = Text()
    content.append_text(tips)

    return Panel(
        Panel.fit(commands_table, title="Comandos Disponíveis", border_style="cyan"),
        title="[bold cyan]Ajuda do QAUserSearch Chat[/bold cyan]",
        border_style="blue",
        padding=(1, 2),
    )


def _build_empty_history_panel() -> Panel:
    """Build panel for empty history."""
    return Panel(
        Text("Nenhuma query no histórico.", style="dim"),
        title="[bold]Histórico[/bold]",
        border_style="dim",
    )


def _build_history_table(history: "list[QueryRecord]") -> Table:
    """Build table with query history.

    Args:
        history: List of QueryRecord items.

    Returns:
        Rich Table with history items.
    """
    from src.cli.chat.session import QueryRecord  # noqa: PLC0415

    table = Table(
        title="Histórico de Queries",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Hora", style="dim", width=8)
    table.add_column("Prompt", style="white")
    table.add_column("Status", width=8)

    for i, record in enumerate(history, 1):
        if not isinstance(record, QueryRecord):
            continue

        time_str = record.timestamp.strftime("%H:%M:%S")
        prompt_short = (
            record.prompt[:40] + "..." if len(record.prompt) > 40 else record.prompt
        )
        status = (
            Text("✓", style="green")
            if record.was_successful
            else Text("✗", style="red")
        )

        table.add_row(str(i), time_str, prompt_short, status)

    return table
