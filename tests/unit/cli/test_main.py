"""Tests for CLI entry point (qa command).

TDD RED: These tests define the expected behavior for the unified entry point.
"""

from typer.testing import CliRunner

from src.cli.main import app
from tests.unit.cli import strip_ansi

runner = CliRunner()


class TestQaHelp:
    """Tests for qa --help command."""

    def test_qa_help_lists_subcommands(self) -> None:
        """Verify qa --help shows both chat and catalog subcommands."""
        result = runner.invoke(app, ["--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "chat" in stdout
        assert "catalog" in stdout

    def test_qa_help_shows_description(self) -> None:
        """Verify qa --help shows CLI description."""
        result = runner.invoke(app, ["--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "QAUserSearch" in stdout or "CLI" in stdout


class TestQaChatHelp:
    """Tests for qa chat --help command."""

    def test_qa_chat_help(self) -> None:
        """Verify qa chat --help shows available options."""
        result = runner.invoke(app, ["chat", "--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "--mock" in stdout
        assert "--server" in stdout

    def test_qa_chat_help_shows_default_server(self) -> None:
        """Verify qa chat --help shows default server URL."""
        result = runner.invoke(app, ["chat", "--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "ws://localhost:8000" in stdout or "default" in stdout.lower()


class TestQaCatalogHelp:
    """Tests for qa catalog --help command."""

    def test_qa_catalog_help(self) -> None:
        """Verify qa catalog --help shows catalog subcommands."""
        result = runner.invoke(app, ["catalog", "--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        # Catalog should show its subcommands (extract, validate, etc.)
        assert "extract" in stdout.lower() or "catalog" in stdout.lower()

    def test_qa_catalog_includes_extract_command(self) -> None:
        """Verify catalog subcommand includes extract."""
        result = runner.invoke(app, ["catalog", "--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "extract" in stdout.lower()
