"""CLI Chat module for QAUserSearch.

This module provides an interactive chat interface for natural language queries
against the QA database. It supports both WebSocket connections to a real backend
and a mock mode for offline development.

Example:
    >>> from src.cli.chat import run_chat
    >>> import asyncio
    >>> asyncio.run(run_chat(mock_mode=True))

Modules:
    - session: Chat session state management
    - commands: Special command processing (/exit, /help, etc.)
    - renderer: Rich panel rendering for interpretations and queries
    - handlers: Message handling for WebSocket responses
    - mock_client: Mock client for offline development
    - client: WebSocket client for real backend connection
    - validation: Input validation and edge case handling
"""

import asyncio
import signal
from contextlib import suppress
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt

from src.cli.chat.client import WSChatClient
from src.cli.chat.commands import (
    CommandResult,
    CommandType,
    execute_command,
    is_command,
    parse_command,
)
from src.cli.chat.handlers.message_handler import MessageHandler
from src.cli.chat.mock_client import ChatClientProtocol, MockChatClient
from src.cli.chat.renderer import (
    render_confidence_bar,
    render_error,
    render_help,
    render_history,
    render_interpretation,
    render_query,
    render_welcome,
)
from src.cli.chat.session import ChatSession, QueryRecord
from src.cli.chat.validation import (
    ResponseTimeoutError,
    ValidationError,
    check_terminal_width,
    get_response_timeout,
    get_terminal_info,
    is_interactive_terminal,
    validate_prompt,
)
from src.schemas.websocket import (
    WSChunkMessage,
    WSErrorMessage,
    WSInterpretationMessage,
    WSQueryMessage,
    WSStatusMessage,
)

if TYPE_CHECKING:
    pass


# Default WebSocket server URL
DEFAULT_SERVER_URL = "ws://localhost:8000/ws/query/interpret"


class ChatLoop:
    """Main chat loop orchestrator.

    Manages the interactive chat session, handling user input, commands,
    queries, and graceful shutdown.

    Attributes:
        session: The chat session state.
        console: Rich console for output.
        client: The chat client (mock or WebSocket).
        handler: Message handler for processing responses.
        server_url: WebSocket server URL (used when toggling mock mode).
        is_interactive: Whether running in an interactive terminal.
    """

    def __init__(
        self,
        mock_mode: bool = False,
        server_url: str | None = None,
    ) -> None:
        """Initialize the chat loop.

        Args:
            mock_mode: Whether to start in mock mode (offline).
            server_url: WebSocket server URL for real mode.
        """
        # Detect terminal capabilities
        terminal_info = get_terminal_info()
        self.is_interactive = terminal_info.is_tty

        # Configure console based on terminal capabilities
        # force_terminal=False for non-TTY to avoid escape codes
        self.console = Console(
            force_terminal=self.is_interactive,
            no_color=not terminal_info.supports_color,
            width=terminal_info.width if terminal_info.is_narrow else None,
        )

        self.session = ChatSession(mock_mode=mock_mode)
        self.server_url = server_url or DEFAULT_SERVER_URL
        self._running = True
        self._processing = False

        # Initialize client based on mode
        self.client: ChatClientProtocol = self._create_client()
        self.handler = MessageHandler(
            session=self.session,
            console=self.console,
        )

    def _create_client(self) -> ChatClientProtocol:
        """Create the appropriate client based on mock mode.

        Returns:
            MockChatClient if mock_mode is True, WSChatClient otherwise.
        """
        if self.session.mock_mode:
            return MockChatClient(min_delay_ms=300, max_delay_ms=1000)
        return WSChatClient(url=self.server_url)

    def _switch_client(self) -> None:
        """Switch between mock and real client after /mock command."""
        self.client = self._create_client()

    def _display_welcome(self) -> None:
        """Display the welcome screen."""
        # Check terminal width and show warning if narrow
        width_warning = check_terminal_width()
        if width_warning:
            self.console.print(f"[yellow]{width_warning}[/yellow]\n")

        welcome = render_welcome()
        self.console.print(welcome)

        # Show mode indicator
        if self.session.mock_mode:
            self.console.print(
                "[dim italic]Modo: MOCK (offline) - use /mock para alternar[/dim italic]\n"
            )
        else:
            self.console.print(
                f"[dim italic]Conectando a: {self.server_url}[/dim italic]\n"
            )

        # Show non-interactive warning
        if not self.is_interactive:
            self.console.print(
                "[yellow]Modo não-interativo detectado. "
                "Para entrada interativa, use um terminal TTY.[/yellow]\n"
            )

    def _get_user_input(self) -> str | None:
        """Get user input from the prompt.

        Returns:
            The user input string, or None if interrupted.
        """
        try:
            return Prompt.ask("[bold cyan]Você[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            return None

    def _handle_command(self, user_input: str) -> bool:
        """Handle a command input.

        Args:
            user_input: The command string (starts with '/').

        Returns:
            True if the chat should continue, False if it should exit.
        """
        command_type = parse_command(user_input)

        if command_type is None:
            self.console.print(
                f"[yellow]Comando desconhecido: {user_input}[/yellow]\n"
                "[dim]Digite /help para ver comandos disponíveis.[/dim]"
            )
            return True

        # Execute the command
        result = execute_command(command_type, self.session, self.console)

        # Display output if any
        if result.message:
            self.console.print(f"[green]{result.message}[/green]")
        if result.output:
            self.console.print(result.output)

        # Handle /mock toggle - switch client
        if command_type == CommandType.MOCK:
            self._switch_client()
            mode = "MOCK (offline)" if self.session.mock_mode else "REAL (WebSocket)"
            self.console.print(
                f"[dim italic]Cliente alterado para: {mode}[/dim italic]"
            )

        return not result.should_exit

    async def _process_query(self, prompt: str) -> None:
        """Process a natural language query.

        Validates the prompt, sends it to the server (with timeout),
        and handles the response messages.

        Args:
            prompt: The user's natural language query.
        """
        # Validate prompt first
        try:
            validated_prompt = validate_prompt(prompt)
        except ValidationError as e:
            self.console.print(f"[bold red]Erro de validação:[/bold red] {e.message}")
            if e.suggestion:
                self.console.print(f"[dim]{e.suggestion}[/dim]")
            return

        self._processing = True
        self.handler.reset()
        self.handler.set_current_prompt(validated_prompt)

        try:
            # Show spinner while processing
            with self.console.status(
                "[bold cyan]Processando...[/bold cyan]", spinner="dots"
            ) as status:
                # Connect if not connected
                if not self.client.is_connected:
                    status.update("[bold cyan]Conectando...[/bold cyan]")
                    await self.client.connect()

                # Send prompt and process messages with timeout
                timeout = get_response_timeout()
                try:
                    async with asyncio.timeout(timeout):
                        async for message in self.client.send_prompt(validated_prompt):
                            if isinstance(message, WSStatusMessage):
                                status_msg = message.data.get(
                                    "message", "Processando..."
                                )
                                status.update(f"[bold cyan]{status_msg}[/bold cyan]")
                                self.handler.handle_status(status_msg)

                            elif isinstance(message, WSChunkMessage):
                                content = message.data.get("content", "")
                                self.handler.handle_chunk(content)

                            elif isinstance(message, WSInterpretationMessage):
                                # Stop spinner before rendering panel
                                status.stop()
                                self.handler.handle_interpretation(message.data)
                                # Restart spinner for query generation
                                status.start()
                                status.update("[bold cyan]Gerando query...[/bold cyan]")

                            elif isinstance(message, WSQueryMessage):
                                # Stop spinner before rendering panel
                                status.stop()
                                self.handler.handle_query(message.data)

                            elif isinstance(message, WSErrorMessage):
                                # Stop spinner before rendering error
                                status.stop()
                                self.handler.handle_error(message.data)
                except TimeoutError:
                    raise ResponseTimeoutError(timeout) from None

        except ResponseTimeoutError as e:
            self.console.print(f"[bold red]Timeout:[/bold red] {e.message}")
            self.console.print(
                "[dim]Tente novamente ou use /mock para modo offline.[/dim]"
            )
        except ConnectionError as e:
            self.console.print(f"[bold red]Erro de conexão:[/bold red] {e}")
            self.console.print(
                "[dim]Tente /mock para modo offline ou verifique o servidor.[/dim]"
            )
        except asyncio.CancelledError:
            self.console.print("\n[yellow]Operação cancelada.[/yellow]")
        finally:
            self._processing = False

    async def run(self) -> None:
        """Run the main chat loop.

        Displays welcome screen, then enters the input loop.
        Handles commands (starting with '/') and queries.
        Exits gracefully on /exit, /quit, or Ctrl+C.
        """
        # Setup signal handler for graceful Ctrl+C
        loop = asyncio.get_event_loop()

        def signal_handler() -> None:
            if self._processing:
                # Cancel current operation
                self.console.print("\n[yellow]Cancelando operação...[/yellow]")
            else:
                # Exit chat
                self._running = False
                self.console.print("\n[cyan]Saindo do chat...[/cyan]")

        # Install signal handler
        with suppress(NotImplementedError):
            loop.add_signal_handler(signal.SIGINT, signal_handler)

        try:
            # Display welcome screen
            self._display_welcome()

            # Main input loop
            while self._running:
                # Get user input
                user_input = self._get_user_input()

                if user_input is None:
                    # Ctrl+C during prompt
                    self._running = False
                    self.console.print("\n[cyan]Até logo![/cyan]")
                    break

                # Skip empty input
                user_input = user_input.strip()
                if not user_input:
                    continue

                # Check if it's a command
                if is_command(user_input):
                    should_continue = self._handle_command(user_input)
                    if not should_continue:
                        break
                else:
                    # Process as query
                    await self._process_query(user_input)

                # Add newline for readability
                self.console.print()

        finally:
            # Cleanup: disconnect client
            if self.client.is_connected:
                await self.client.disconnect()

            # Remove signal handler
            with suppress(NotImplementedError):
                loop.remove_signal_handler(signal.SIGINT)


async def run_chat(
    mock_mode: bool = False,
    server_url: str | None = None,
) -> None:
    """Run the interactive chat session.

    This is the main entry point for the chat CLI. It creates a ChatLoop
    and runs it until the user exits.

    Args:
        mock_mode: Whether to start in mock mode (offline development).
        server_url: WebSocket server URL for real backend connection.
            Defaults to ws://localhost:8000/ws/query/interpret.

    Example:
        >>> import asyncio
        >>> asyncio.run(run_chat(mock_mode=True))
    """
    chat_loop = ChatLoop(mock_mode=mock_mode, server_url=server_url)
    await chat_loop.run()


__all__ = [
    "ChatLoop",
    "ChatSession",
    "CommandResult",
    "CommandType",
    "QueryRecord",
    "ResponseTimeoutError",
    "ValidationError",
    "check_terminal_width",
    "execute_command",
    "get_response_timeout",
    "get_terminal_info",
    "is_command",
    "is_interactive_terminal",
    "parse_command",
    "render_confidence_bar",
    "render_error",
    "render_help",
    "render_history",
    "render_interpretation",
    "render_query",
    "render_welcome",
    "run_chat",
    "validate_prompt",
]
