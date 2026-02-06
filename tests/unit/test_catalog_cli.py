"""Unit tests for catalog CLI commands."""

import pytest
from typer.testing import CliRunner

from src.cli.catalog import KNOWN_SOURCES, app
from tests.unit.cli import strip_ansi


class TestCatalogCLI:
    """Tests for catalog CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_list_known_shows_all_sources(self, runner: CliRunner) -> None:
        """list-known should display all known sources."""
        result = runner.invoke(app, ["list-known"])
        output = strip_ansi(result.output)

        assert result.exit_code == 0
        for db_name, table_name in KNOWN_SOURCES:
            assert f"{db_name}.{table_name}" in output

    def test_extract_requires_arguments(self, runner: CliRunner) -> None:
        """extract without arguments should show error."""
        result = runner.invoke(app, ["extract"])

        assert result.exit_code != 0

    def test_help_shows_commands(self, runner: CliRunner) -> None:
        """--help should show available commands."""
        result = runner.invoke(app, ["--help"])
        output = strip_ansi(result.output)

        assert result.exit_code == 0
        assert "extract" in output
        assert "extract-all" in output
        assert "list-known" in output

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Running with no args should show help."""
        result = runner.invoke(app, [])
        output = strip_ansi(result.output)

        assert result.exit_code == 0
        assert "extract" in output
        assert "extract-all" in output
        assert "list-known" in output

    def test_extract_help_shows_arguments(self, runner: CliRunner) -> None:
        """extract --help should show required arguments."""
        result = runner.invoke(app, ["extract", "--help"])
        output = strip_ansi(result.output).lower()

        assert result.exit_code == 0
        assert "db_name" in output or "db-name" in output
        assert "table_name" in output or "table-name" in output
        assert "sample-size" in output

    def test_extract_all_help_shows_options(self, runner: CliRunner) -> None:
        """extract-all --help should show options."""
        result = runner.invoke(app, ["extract-all", "--help"])
        output = strip_ansi(result.output).lower()

        assert result.exit_code == 0
        assert "sample-size" in output

    def test_known_sources_has_expected_entries(self) -> None:
        """KNOWN_SOURCES should contain expected sources."""
        expected = [
            ("card_account_authorization", "account_main"),
            ("card_account_authorization", "card_main"),
            ("credit", "invoice"),
            ("credit", "closed_invoice"),
        ]

        assert len(KNOWN_SOURCES) == len(expected)
        for source in expected:
            assert source in KNOWN_SOURCES
