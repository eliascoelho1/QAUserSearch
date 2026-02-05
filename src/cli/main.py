"""Unified CLI entry point for QAUserSearch.

This module provides the main 'qa' command with subcommands for chat and catalog.

Example usage:
    qa --help              # Show available commands
    qa chat --mock         # Start chat in mock mode
    qa chat --server URL   # Start chat with custom WebSocket server
    qa catalog extract ... # Run catalog extraction commands
"""

import asyncio

import typer

from src.cli.catalog import app as catalog_app

app = typer.Typer(
    name="qa",
    help="QAUserSearch CLI - Search QA test data using natural language.",
    no_args_is_help=True,
)

# Register catalog subcommand from existing module
app.add_typer(catalog_app, name="catalog", help="Catalog schema extraction commands.")

# Default WebSocket server URL
DEFAULT_SERVER_URL = "ws://localhost:8000/ws/query/interpret"


@app.command()
def chat(
    mock: bool = typer.Option(
        False,
        "--mock",
        "-m",
        help="Run in mock mode (offline, simulated responses).",
    ),
    server: str = typer.Option(
        DEFAULT_SERVER_URL,
        "--server",
        "-s",
        help="WebSocket server URL for real backend connection.",
    ),
) -> None:
    """Start interactive chat session for natural language queries.

    Use --mock for offline development without a backend server.
    Use --server to specify a custom WebSocket endpoint.

    Examples:
        qa chat --mock              # Start in mock mode
        qa chat --server ws://...   # Connect to custom server
    """
    from src.cli.chat import run_chat

    # Run the async chat loop
    asyncio.run(run_chat(mock_mode=mock, server_url=server))


if __name__ == "__main__":
    app()
