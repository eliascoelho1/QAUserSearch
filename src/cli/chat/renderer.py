"""Rich-based rendering functions for CLI Chat.

This module provides functions to render various UI components using Rich library:
- Welcome banner with ASCII art and instructions
- Interpretation panel with summary, entities, and filters
- SQL query with syntax highlighting
- Confidence bar (green/amber/red)
- History table
- Help panel
- Error panel

All functions return Rich Renderable objects (Panel, Table, Group, etc.)
that can be printed with a Rich Console.

Example:
    >>> from rich.console import Console
    >>> from src.cli.chat.renderer import render_welcome, render_interpretation
    >>> console = Console()
    >>> console.print(render_welcome())
    >>> console.print(render_interpretation(interpretation_response))
"""

from typing import TYPE_CHECKING

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from src.cli.chat.session import QueryRecord
    from src.schemas.interpreter import (
        ErrorResponse,
        InterpretationResponse,
        QueryResponse,
    )


# =============================================================================
# Constants
# =============================================================================

WELCOME_BANNER = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗  █████╗     ██╗   ██╗███████╗███████╗██████╗           ║
║  ██╔═══██╗██╔══██╗    ██║   ██║██╔════╝██╔════╝██╔══██╗          ║
║  ██║   ██║███████║    ██║   ██║███████╗█████╗  ██████╔╝          ║
║  ██║▄▄ ██║██╔══██║    ██║   ██║╚════██║██╔══╝  ██╔══██╗          ║
║  ╚██████╔╝██║  ██║    ╚██████╔╝███████║███████╗██║  ██║          ║
║   ╚══▀▀═╝ ╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝          ║
║                                                                   ║
║               QA User Search - Chat Interativo                    ║
╚═══════════════════════════════════════════════════════════════════╝
"""

CONFIDENCE_BAR_WIDTH = 10


# =============================================================================
# Helper Functions
# =============================================================================


def _get_confidence_color(confidence: float) -> str:
    """Get color based on confidence level.

    Args:
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Color name: "green" for high (>=0.8), "yellow" for medium (>=0.5),
        "red" for low (<0.5).
    """
    if confidence >= 0.8:
        return "green"
    elif confidence >= 0.5:
        return "yellow"
    else:
        return "red"


def _get_confidence_label(confidence: float) -> str:
    """Get a human-readable label for confidence score.

    Args:
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Human-readable label in Portuguese.
    """
    if confidence >= 0.8:
        return "Alta"
    elif confidence >= 0.5:
        return "Média"
    else:
        return "Baixa"


# =============================================================================
# Render Functions
# =============================================================================


def render_welcome() -> RenderableType:
    """Render the welcome banner with instructions.

    Returns:
        Rich renderable with ASCII banner, instructions, and example queries.

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> console.print(render_welcome())
    """
    banner = Text(WELCOME_BANNER, style="bold cyan")

    instructions = Text()
    instructions.append("\n📝 ", style="bold")
    instructions.append(
        "Descreva o que você procura em linguagem natural:\n", style="bold"
    )
    instructions.append(
        '   Exemplo: "usuários com cartão de crédito ativo nos últimos 30 dias"\n\n'
    )

    commands = Text()
    commands.append("⌨️  ", style="bold")
    commands.append("Comandos disponíveis:\n", style="bold")
    commands.append("   /help     - Exibe ajuda detalhada\n", style="dim")
    commands.append("   /history  - Mostra histórico de queries\n", style="dim")
    commands.append("   /clear    - Limpa histórico da sessão\n", style="dim")
    commands.append("   /mock     - Alterna modo offline\n", style="dim")
    commands.append("   /exit     - Encerra o chat\n", style="dim")

    content = Group(banner, instructions, commands)

    return Panel(
        content,
        title="[bold blue]Bem-vindo ao QA User Search[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    )


def render_confidence_bar(confidence: float) -> RenderableType:
    """Render a visual confidence bar with color coding.

    Args:
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        Rich Text with visual bar representation.
        - Green (>=0.8): High confidence
        - Yellow/Amber (>=0.5, <0.8): Medium confidence
        - Red (<0.5): Low confidence

    Example:
        >>> bar = render_confidence_bar(0.85)
        >>> # Renders: [████████░░] 0.85 (Alta)
    """
    color = _get_confidence_color(confidence)
    label = _get_confidence_label(confidence)

    filled_count = int(confidence * CONFIDENCE_BAR_WIDTH)
    empty_count = CONFIDENCE_BAR_WIDTH - filled_count

    filled_char = "█"
    empty_char = "░"

    bar = Text()
    bar.append("[")
    bar.append(filled_char * filled_count, style=color)
    bar.append(empty_char * empty_count, style="dim")
    bar.append("] ")
    bar.append(f"{confidence:.2f}", style=f"bold {color}")
    bar.append(f" ({label})", style=color)

    return bar


def render_interpretation(interpretation: "InterpretationResponse") -> RenderableType:
    """Render interpretation results as a panel.

    Args:
        interpretation: The interpretation response to render.

    Returns:
        Rich Panel containing summary, confidence bar, entities table,
        and filters table.

    Example:
        >>> panel = render_interpretation(interpretation_response)
        >>> console.print(panel)
    """
    # Summary section
    summary = Text()
    summary.append("📋 Resumo: ", style="bold")
    summary.append(interpretation.summary)
    summary.append("\n\n")

    # Confidence bar
    confidence_section = Text()
    confidence_section.append("📊 Confiança: ", style="bold")
    confidence_bar = render_confidence_bar(interpretation.confidence)

    # Entities table
    entities_table = Table(
        title="Entidades Identificadas", show_header=True, header_style="bold magenta"
    )
    entities_table.add_column("Nome", style="cyan")
    entities_table.add_column("Tabela", style="green")
    entities_table.add_column("Alias", style="dim")

    for entity in interpretation.entities:
        entities_table.add_row(
            entity.name,
            entity.table_name,
            entity.alias or "-",
        )

    # Filters table
    filters_table = Table(
        title="Filtros Extraídos", show_header=True, header_style="bold magenta"
    )
    filters_table.add_column("Campo", style="cyan")
    filters_table.add_column("Operador", style="yellow")
    filters_table.add_column("Valor", style="green")
    filters_table.add_column("Temporal", style="dim")

    for filter_item in interpretation.filters:
        filters_table.add_row(
            filter_item.field,
            str(
                filter_item.operator.value
                if hasattr(filter_item.operator, "value")
                else filter_item.operator
            ),
            str(filter_item.value),
            "✓" if filter_item.is_temporal else "-",
        )

    # Combine all sections
    content = Group(
        summary,
        confidence_section,
        confidence_bar,
        Text("\n"),
        entities_table,
        Text("\n"),
        filters_table,
    )

    return Panel(
        content,
        title="[bold green]🔍 Interpretação[/bold green]",
        border_style="green",
        padding=(1, 2),
    )


def render_query(query: "QueryResponse") -> RenderableType:
    """Render generated SQL query with syntax highlighting.

    Args:
        query: The query response containing SQL.

    Returns:
        Rich Panel with SQL syntax highlighted.

    Example:
        >>> panel = render_query(query_response)
        >>> console.print(panel)
    """
    # SQL with syntax highlighting
    sql_syntax = Syntax(
        query.sql,
        "sql",
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
    )

    # Validation status
    status = Text()
    if query.is_valid:
        status.append("✅ Query válida", style="bold green")
    else:
        status.append("❌ Query inválida", style="bold red")
        if query.validation_errors:
            status.append("\n   Erros: ")
            status.append(", ".join(query.validation_errors), style="red")

    content = Group(
        sql_syntax,
        Text("\n"),
        status,
    )

    return Panel(
        content,
        title="[bold blue]📄 Query SQL Gerada[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    )


def render_history(history: list["QueryRecord"]) -> RenderableType:
    """Render query history as a table.

    Args:
        history: List of QueryRecord objects.

    Returns:
        Rich Table with history entries.

    Example:
        >>> table = render_history(session.get_history())
        >>> console.print(table)
    """
    table = Table(
        title="📜 Histórico de Queries",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Prompt", style="white")
    table.add_column("Status", style="green", width=10)
    table.add_column("Hora", style="dim", width=10)

    if not history:
        return Panel(
            Text("Nenhuma query no histórico.", style="dim italic"),
            title="[bold cyan]📜 Histórico[/bold cyan]",
            border_style="cyan",
        )

    for idx, record in enumerate(history, start=1):
        status = "✅" if record.was_successful else "❌"
        time_str = record.timestamp.strftime("%H:%M:%S")
        # Truncate long prompts
        prompt = (
            record.prompt[:50] + "..." if len(record.prompt) > 50 else record.prompt
        )

        table.add_row(str(idx), prompt, status, time_str)

    return Panel(
        table,
        border_style="cyan",
        padding=(0, 1),
    )


def render_help() -> RenderableType:
    """Render help panel with all available commands.

    Returns:
        Rich Panel with command descriptions.

    Example:
        >>> panel = render_help()
        >>> console.print(panel)
    """
    help_text = Text()

    help_text.append("🔍 ", style="bold")
    help_text.append("Comandos Disponíveis:\n\n", style="bold underline")

    commands = [
        ("/help", "Exibe esta mensagem de ajuda"),
        ("/history", "Mostra o histórico de queries da sessão"),
        ("/clear", "Limpa o histórico e última interpretação"),
        ("/execute", "Executa a última query gerada (simulação v1)"),
        ("/mock", "Alterna entre modo mock (offline) e real"),
        ("/exit, /quit", "Encerra o chat"),
    ]

    for cmd, description in commands:
        help_text.append(f"  {cmd:<15}", style="bold cyan")
        help_text.append(f" {description}\n", style="white")

    help_text.append("\n")
    help_text.append("💡 ", style="bold")
    help_text.append("Dicas:\n\n", style="bold underline")

    tips = [
        "Descreva o que você procura em linguagem natural",
        'Exemplo: "usuários com cartão ativo nos últimos 30 dias"',
        "Use termos específicos como: usuário, cartão, conta, transação",
        "Ctrl+C interrompe a operação atual sem sair do chat",
    ]

    for tip in tips:
        help_text.append(f"  • {tip}\n", style="dim")

    return Panel(
        help_text,
        title="[bold yellow]❓ Ajuda[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    )


def render_error(error: "ErrorResponse") -> RenderableType:
    """Render error panel with details and suggestions.

    Args:
        error: The error response to render.

    Returns:
        Rich Panel with error details and suggestions.

    Example:
        >>> panel = render_error(error_response)
        >>> console.print(panel)
    """
    content = Text()

    # Error code and message
    content.append("❌ Código: ", style="bold")
    content.append(f"{error.code}\n\n", style="bold red")

    content.append("📝 Mensagem:\n", style="bold")
    content.append(f"   {error.message}\n\n", style="red")

    # Details (if present)
    if error.details:
        content.append("📋 Detalhes:\n", style="bold")
        for key, value in error.details.items():
            content.append(f"   {key}: ", style="dim")
            content.append(f"{value}\n", style="white")
        content.append("\n")

    # Suggestions
    if error.suggestions:
        content.append("💡 Sugestões:\n", style="bold")
        for suggestion in error.suggestions:
            content.append(f"   • {suggestion}\n", style="yellow")

    return Panel(
        content,
        title="[bold red]⚠️  Erro[/bold red]",
        border_style="red",
        padding=(1, 2),
    )
