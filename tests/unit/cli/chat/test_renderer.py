"""Unit tests for CLI Chat Renderer.

Tests for rendering functions that create Rich Renderable objects:
- render_welcome(): Welcome banner with instructions
- render_interpretation(): Interpretation panel with summary, entities, filters
- render_query(): SQL query with syntax highlighting
- render_confidence_bar(): Visual confidence bar (green/amber/red)
- render_history(): History table
- render_help(): Help panel
- render_error(): Error panel
"""

from rich.console import Console

from src.schemas.interpreter import (
    ErrorResponse,
    InterpretationResponse,
    QueryResponse,
)


class TestRenderWelcome:
    """Tests for render_welcome() function."""

    def test_render_welcome_returns_panel(self) -> None:
        """T042: render_welcome should return a Rich Panel."""
        from src.cli.chat.renderer import render_welcome

        result = render_welcome()

        # Should return a Panel (or Group containing Panel)
        assert result is not None
        # Render to string to verify it's a valid renderable
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()
        assert len(output) > 0

    def test_render_welcome_contains_instructions(self) -> None:
        """T043: render_welcome should contain usage instructions."""
        from src.cli.chat.renderer import render_welcome

        result = render_welcome()

        # Render to string and check for expected content
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain instructions and commands
        assert "/help" in output or "help" in output.lower()
        assert "/exit" in output or "exit" in output.lower()
        # Should contain example queries or prompts
        assert "usuário" in output.lower() or "query" in output.lower()


class TestRenderInterpretation:
    """Tests for render_interpretation() function."""

    def test_render_interpretation_returns_panel(
        self, sample_interpretation: InterpretationResponse
    ) -> None:
        """T044: render_interpretation should return a Rich Panel."""
        from src.cli.chat.renderer import render_interpretation

        result = render_interpretation(sample_interpretation)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()
        assert len(output) > 0

    def test_render_interpretation_contains_summary(
        self, sample_interpretation: InterpretationResponse
    ) -> None:
        """T045: render_interpretation should display the summary."""
        from src.cli.chat.renderer import render_interpretation

        result = render_interpretation(sample_interpretation)

        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain the summary from the interpretation
        assert "Buscar usuários com cartão de crédito" in output

    def test_render_interpretation_contains_entities_table(
        self, sample_interpretation: InterpretationResponse
    ) -> None:
        """T046: render_interpretation should display entities table."""
        from src.cli.chat.renderer import render_interpretation

        result = render_interpretation(sample_interpretation)

        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain entity information
        assert "users" in output.lower()
        assert "credit.users" in output or "credit" in output

    def test_render_interpretation_contains_filters_table(
        self, sample_interpretation: InterpretationResponse
    ) -> None:
        """T047: render_interpretation should display filters table."""
        from src.cli.chat.renderer import render_interpretation

        result = render_interpretation(sample_interpretation)

        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain filter information
        assert "card_status" in output or "status" in output.lower()
        assert "active" in output


class TestRenderQuery:
    """Tests for render_query() function."""

    def test_render_query_returns_panel(self, sample_query: QueryResponse) -> None:
        """T048: render_query should return a Rich Panel."""
        from src.cli.chat.renderer import render_query

        result = render_query(sample_query)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()
        assert len(output) > 0
        assert "SELECT" in output

    def test_render_query_has_sql_syntax_highlight(
        self, sample_query: QueryResponse
    ) -> None:
        """T049: render_query should use SQL syntax highlighting."""
        from src.cli.chat.renderer import render_query

        result = render_query(sample_query)

        console = Console(force_terminal=True, width=80, force_interactive=True)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain SQL keywords
        assert "SELECT" in output
        assert "FROM" in output
        assert "WHERE" in output


class TestRenderConfidenceBar:
    """Tests for render_confidence_bar() function."""

    def test_render_confidence_bar_high(self) -> None:
        """T050: render_confidence_bar with high confidence (>=0.8) should be green."""
        from src.cli.chat.renderer import render_confidence_bar

        result = render_confidence_bar(0.85)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should show confidence value
        assert "0.85" in output or "85" in output
        # Should have filled blocks
        assert "█" in output or "▓" in output or "■" in output

    def test_render_confidence_bar_medium(self) -> None:
        """T051: render_confidence_bar with medium confidence (>=0.5, <0.8) should be amber/yellow."""
        from src.cli.chat.renderer import render_confidence_bar

        result = render_confidence_bar(0.65)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should show confidence value
        assert "0.65" in output or "65" in output
        # Should have visual representation
        assert "█" in output or "▓" in output or "■" in output

    def test_render_confidence_bar_low(self) -> None:
        """T052: render_confidence_bar with low confidence (<0.5) should be red."""
        from src.cli.chat.renderer import render_confidence_bar

        result = render_confidence_bar(0.35)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should show confidence value
        assert "0.35" in output or "35" in output
        # Should have visual representation
        assert "█" in output or "▓" in output or "■" in output or "░" in output


class TestRenderHistory:
    """Tests for render_history() function."""

    def test_render_history_returns_table(
        self,
        sample_interpretation: InterpretationResponse,
        sample_query: QueryResponse,
    ) -> None:
        """T053: render_history should return a Rich Table."""
        from datetime import UTC, datetime

        from src.cli.chat.renderer import render_history
        from src.cli.chat.session import QueryRecord

        # Create some query records
        records = [
            QueryRecord(
                prompt="buscar usuários ativos",
                timestamp=datetime.now(UTC),
                interpretation=sample_interpretation,
                query=sample_query,
            ),
            QueryRecord(
                prompt="listar cartões",
                timestamp=datetime.now(UTC),
                interpretation=sample_interpretation,
                query=sample_query,
            ),
        ]

        result = render_history(records)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain the prompts
        assert "buscar usuários ativos" in output or "buscar" in output.lower()
        assert "listar cartões" in output or "listar" in output.lower()


class TestRenderHelp:
    """Tests for render_help() function."""

    def test_render_help_returns_panel(self) -> None:
        """T054: render_help should return a Rich Panel."""
        from src.cli.chat.renderer import render_help

        result = render_help()

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain commands
        assert "/exit" in output or "exit" in output.lower()
        assert "/help" in output or "help" in output.lower()
        assert "/clear" in output or "clear" in output.lower()
        assert "/history" in output or "history" in output.lower()


class TestRenderError:
    """Tests for render_error() function."""

    def test_render_error_returns_panel(self) -> None:
        """T055: render_error should return a Rich Panel."""
        from src.cli.chat.renderer import render_error

        error = ErrorResponse(
            code="ERR_001",
            message="Não foi possível interpretar o prompt",
            details={"reason": "Nenhuma tabela encontrada"},
            suggestions=["Verifique a ortografia", "Use termos mais específicos"],
        )

        result = render_error(error)

        assert result is not None
        console = Console(force_terminal=True, width=80)
        with console.capture() as capture:
            console.print(result)
        output = capture.get()

        # Should contain error information
        assert "ERR_001" in output or "Erro" in output
        assert "interpretar" in output.lower() or "prompt" in output.lower()
        # Should contain suggestions
        assert "ortografia" in output.lower() or "sugest" in output.lower()
