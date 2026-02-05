"""Tests for CLI entry point (qa command).

TDD RED: These tests define the expected behavior for the unified entry point.
"""

from typer.testing import CliRunner

from src.cli.main import app

runner = CliRunner()


class TestQaHelp:
    """Tests for qa --help command."""

    def test_qa_help_lists_subcommands(self) -> None:
        """Verify qa --help shows both chat and catalog subcommands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "chat" in result.stdout
        assert "catalog" in result.stdout

    def test_qa_help_shows_description(self) -> None:
        """Verify qa --help shows CLI description."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "QAUserSearch" in result.stdout or "CLI" in result.stdout


class TestQaChatHelp:
    """Tests for qa chat --help command."""

    def test_qa_chat_help(self) -> None:
        """Verify qa chat --help shows available options."""
        result = runner.invoke(app, ["chat", "--help"])

        assert result.exit_code == 0
        assert "--mock" in result.stdout
        assert "--server" in result.stdout

    def test_qa_chat_help_shows_default_server(self) -> None:
        """Verify qa chat --help shows default server URL."""
        result = runner.invoke(app, ["chat", "--help"])

        assert result.exit_code == 0
        assert (
            "ws://localhost:8000" in result.stdout or "default" in result.stdout.lower()
        )


class TestQaCatalogHelp:
    """Tests for qa catalog --help command."""

    def test_qa_catalog_help(self) -> None:
        """Verify qa catalog --help shows catalog subcommands."""
        result = runner.invoke(app, ["catalog", "--help"])

        assert result.exit_code == 0
        # Catalog should show its subcommands (extract, validate, etc.)
        assert "extract" in result.stdout.lower() or "catalog" in result.stdout.lower()

    def test_qa_catalog_includes_extract_command(self) -> None:
        """Verify catalog subcommand includes extract."""
        result = runner.invoke(app, ["catalog", "--help"])

        assert result.exit_code == 0
        assert "extract" in result.stdout.lower()
