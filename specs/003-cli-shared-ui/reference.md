# Plan 00: Infraestrutura Compartilhada de CLI UI

**Data**: 2026-02-04  
**Status**: Draft  
**Autor**: Claude (AI Assistant)  
**Pré-requisito para**: `02P-catalog-ai-enrichment.md`, `03P-cli-chat.md`

---

## Objetivo

Estabelecer uma infraestrutura compartilhada de UI para todos os CLIs do QAUserSearch, garantindo consistência visual, reutilização de código e manutenibilidade.

---

## Motivação

Múltiplos planos do projeto requerem componentes de UI para terminal:

| Plano | Componentes Necessários |
|-------|------------------------|
| `03P-cli-chat.md` | Welcome panel, spinners, painéis de resultado, prompts interativos |
| `02P-catalog-ai-enrichment.md` | Progress bars, painéis de aprovação, prompts de edição |

Sem uma base compartilhada, teríamos:
- Duplicação de código (tema, componentes, prompts)
- Inconsistência visual entre CLIs
- Maior custo de manutenção

---

## Stack Tecnológica

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Output Visual** | Rich | ^13.9.0 | Formatação terminal avançada (panels, tables, spinners, markdown, syntax highlighting) |
| **Input Interativo** | Questionary | ^2.0.0 | Prompts elegantes com seleção por setas, checkboxes, text input |
| **CLI Framework** | Typer | >=0.15.0 | Já instalado, integração nativa com Rich |

---

## Arquitetura

### Estrutura de Diretórios

```
src/cli/
├── __init__.py
├── catalog.py                    # CLI existente (catálogo)
├── chat.py                       # CLI chat (futuro)
│
└── shared/                       # ← NOVO: Módulo compartilhado
    ├── __init__.py
    ├── ui/
    │   ├── __init__.py
    │   ├── theme.py              # Paleta de cores e estilos
    │   ├── components.py         # Componentes Rich reutilizáveis
    │   ├── panels.py             # Painéis especializados
    │   ├── progress.py           # Spinners e barras de progresso
    │   └── prompts.py            # Prompts Questionary customizados
    └── utils/
        ├── __init__.py
        └── terminal.py           # Utilitários de terminal (tamanho, cores, etc.)
```

### Diagrama de Dependências

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI Applications                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │   qa-catalog    │    │    qa-chat      │    │   (futuro CLI)  │        │
│   │   (catalog.py)  │    │   (chat.py)     │    │                 │        │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│            │                      │                      │                  │
│            └──────────────────────┼──────────────────────┘                  │
│                                   │                                          │
│                                   ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        src/cli/shared/                               │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │                         ui/                                  │    │   │
│   │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │   │
│   │  │  │  theme   │ │components│ │  panels  │ │ progress │       │    │   │
│   │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │    │   │
│   │  │  ┌──────────┐                                               │    │   │
│   │  │  │ prompts  │                                               │    │   │
│   │  │  └──────────┘                                               │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │                        utils/                                │    │   │
│   │  │  ┌──────────┐                                               │    │   │
│   │  │  │ terminal │                                               │    │   │
│   │  │  └──────────┘                                               │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design System

### Paleta de Cores (Tema "Vibrant Modern")

```python
# src/cli/shared/ui/theme.py

from dataclasses import dataclass
from rich.style import Style
from rich.theme import Theme

@dataclass(frozen=True)
class ColorPalette:
    """Paleta de cores do QAUserSearch CLI."""
    
    # Cores primárias
    PRIMARY: str = "#7C3AED"       # Roxo vibrante (brand)
    SECONDARY: str = "#06B6D4"    # Cyan (destaques)
    ACCENT: str = "#F59E0B"       # Âmbar (warnings/ênfase)
    
    # Status
    SUCCESS: str = "#10B981"      # Verde esmeralda
    ERROR: str = "#EF4444"        # Vermelho coral
    WARNING: str = "#F59E0B"      # Âmbar
    INFO: str = "#3B82F6"         # Azul
    
    # Confiança (para barras de progresso semânticas)
    CONFIDENCE_HIGH: str = "#10B981"    # Verde (>70%)
    CONFIDENCE_MEDIUM: str = "#F59E0B"  # Âmbar (50-70%)
    CONFIDENCE_LOW: str = "#EF4444"     # Vermelho (<50%)
    
    # Neutros
    TEXT: str = "#F9FAFB"         # Branco suave
    TEXT_DIM: str = "#9CA3AF"     # Cinza para texto secundário
    TEXT_MUTED: str = "#6B7280"   # Cinza mais escuro
    BACKGROUND: str = "#111827"   # Fundo escuro
    BORDER: str = "#374151"       # Bordas sutis


COLORS = ColorPalette()


def get_rich_theme() -> Theme:
    """Retorna tema Rich configurado com a paleta."""
    return Theme({
        "primary": Style(color=COLORS.PRIMARY),
        "secondary": Style(color=COLORS.SECONDARY),
        "accent": Style(color=COLORS.ACCENT, bold=True),
        "success": Style(color=COLORS.SUCCESS),
        "error": Style(color=COLORS.ERROR, bold=True),
        "warning": Style(color=COLORS.WARNING),
        "info": Style(color=COLORS.INFO),
        "dim": Style(color=COLORS.TEXT_DIM),
        "muted": Style(color=COLORS.TEXT_MUTED),
        "heading": Style(color=COLORS.PRIMARY, bold=True),
        "label": Style(color=COLORS.TEXT_DIM),
        "value": Style(color=COLORS.TEXT),
        "highlight": Style(color=COLORS.SECONDARY, bold=True),
    })
```

### Estilos Questionary

```python
# src/cli/shared/ui/theme.py (continuação)

from questionary import Style as QStyle

def get_questionary_style() -> QStyle:
    """Retorna estilo Questionary alinhado com o tema."""
    return QStyle([
        ("qmark", f"fg:{COLORS.PRIMARY} bold"),           # ?
        ("question", f"fg:{COLORS.TEXT} bold"),           # Texto da pergunta
        ("answer", f"fg:{COLORS.SECONDARY} bold"),        # Resposta selecionada
        ("pointer", f"fg:{COLORS.PRIMARY} bold"),         # ❯
        ("highlighted", f"fg:{COLORS.PRIMARY} bold"),     # Item destacado
        ("selected", f"fg:{COLORS.SUCCESS}"),             # Item selecionado (checkbox)
        ("separator", f"fg:{COLORS.BORDER}"),             # Separadores
        ("instruction", f"fg:{COLORS.TEXT_DIM}"),         # Instruções
        ("text", f"fg:{COLORS.TEXT}"),                    # Texto normal
        ("disabled", f"fg:{COLORS.TEXT_MUTED} italic"),   # Opções desabilitadas
    ])
```

---

## Componentes Compartilhados

### 1. Painéis Base (`panels.py`)

```python
# src/cli/shared/ui/panels.py

from rich.panel import Panel
from rich.console import Console, RenderableType
from .theme import COLORS

def create_panel(
    content: RenderableType,
    title: str,
    *,
    icon: str = "",
    style: str = "primary",
    subtitle: str | None = None,
) -> Panel:
    """Cria um painel estilizado padrão."""
    full_title = f"{icon} {title}".strip() if icon else title
    return Panel(
        content,
        title=full_title,
        subtitle=subtitle,
        border_style=style,
        padding=(1, 2),
    )


def info_panel(content: RenderableType, title: str = "Info") -> Panel:
    """Painel de informação."""
    return create_panel(content, title, icon="ℹ️", style="info")


def success_panel(content: RenderableType, title: str = "Sucesso") -> Panel:
    """Painel de sucesso."""
    return create_panel(content, title, icon="✅", style="success")


def warning_panel(content: RenderableType, title: str = "Atenção") -> Panel:
    """Painel de aviso."""
    return create_panel(content, title, icon="⚠️", style="warning")


def error_panel(content: RenderableType, title: str = "Erro") -> Panel:
    """Painel de erro."""
    return create_panel(content, title, icon="❌", style="error")
```

### 2. Barras de Progresso e Spinners (`progress.py`)

```python
# src/cli/shared/ui/progress.py

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.console import Console
from contextlib import contextmanager
from typing import Generator
from .theme import COLORS


def create_spinner_progress(console: Console | None = None) -> Progress:
    """Cria progress bar com spinner para operações indeterminadas."""
    return Progress(
        SpinnerColumn(style=f"bold {COLORS.PRIMARY}"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def create_bar_progress(console: Console | None = None) -> Progress:
    """Cria progress bar para operações com progresso conhecido."""
    return Progress(
        SpinnerColumn(style=f"bold {COLORS.PRIMARY}"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style=COLORS.SUCCESS,
            finished_style=COLORS.SUCCESS,
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


@contextmanager
def spinner(
    description: str,
    console: Console | None = None,
) -> Generator[None, None, None]:
    """Context manager para exibir spinner durante operação."""
    progress = create_spinner_progress(console)
    with progress:
        progress.add_task(description, total=None)
        yield


class PhaseSpinner:
    """Spinner com múltiplas fases de progresso."""
    
    def __init__(self, phases: list[str], console: Console | None = None):
        self.phases = phases
        self.console = console or Console()
        self.current_phase = 0
        self.completed_phases: set[int] = set()
    
    def render(self) -> str:
        """Renderiza o estado atual das fases."""
        lines = []
        for i, phase in enumerate(self.phases):
            if i in self.completed_phases:
                prefix = f"[{COLORS.SUCCESS}]✓[/]"
            elif i == self.current_phase:
                prefix = f"[{COLORS.PRIMARY}]⠙[/]"
            else:
                prefix = f"[{COLORS.TEXT_DIM}]○[/]"
            lines.append(f"  {prefix} {phase}")
        return "\n".join(lines)
    
    def complete_phase(self) -> None:
        """Marca fase atual como completa e avança."""
        self.completed_phases.add(self.current_phase)
        self.current_phase += 1
```

### 3. Prompts Interativos (`prompts.py`)

```python
# src/cli/shared/ui/prompts.py

import questionary
from typing import Any
from .theme import get_questionary_style

_style = get_questionary_style()


def ask_text(
    message: str,
    *,
    default: str = "",
    validate: Any = None,
) -> str | None:
    """Prompt para entrada de texto."""
    return questionary.text(
        message,
        default=default,
        validate=validate,
        style=_style,
    ).ask()


def ask_confirm(
    message: str,
    *,
    default: bool = True,
) -> bool | None:
    """Prompt de confirmação sim/não."""
    return questionary.confirm(
        message,
        default=default,
        style=_style,
    ).ask()


def ask_select(
    message: str,
    choices: list[str | questionary.Choice],
    *,
    default: str | None = None,
    instruction: str = "Use ↑↓ para navegar, Enter para selecionar",
) -> str | None:
    """Prompt de seleção única."""
    return questionary.select(
        message,
        choices=choices,
        default=default,
        instruction=instruction,
        style=_style,
    ).ask()


def ask_checkbox(
    message: str,
    choices: list[str | questionary.Choice],
    *,
    instruction: str = "Use ↑↓ para navegar, Espaço para selecionar, Enter para confirmar",
) -> list[str] | None:
    """Prompt de seleção múltipla."""
    return questionary.checkbox(
        message,
        choices=choices,
        instruction=instruction,
        style=_style,
    ).ask()


# Prompts específicos reutilizáveis

def ask_approval(
    item_name: str,
    *,
    allow_edit: bool = True,
    allow_skip: bool = True,
) -> str | None:
    """
    Prompt padrão de aprovação para workflows de revisão.
    
    Retorna: 'approve', 'edit', 'reject', 'skip', ou None (cancelado)
    """
    choices = [
        questionary.Choice("✓ Aprovar", value="approve"),
    ]
    
    if allow_edit:
        choices.append(questionary.Choice("✏️  Editar", value="edit"))
    
    choices.append(questionary.Choice("✗ Rejeitar", value="reject"))
    
    if allow_skip:
        choices.append(questionary.Choice("⏭️  Pular", value="skip"))
    
    choices.append(questionary.Choice("🛑 Cancelar", value="cancel"))
    
    return ask_select(
        f"O que deseja fazer com '{item_name}'?",
        choices=choices,
    )
```

### 4. Utilitários de Terminal (`terminal.py`)

```python
# src/cli/shared/utils/terminal.py

import os
import sys
from rich.console import Console


def get_terminal_size() -> tuple[int, int]:
    """Retorna (largura, altura) do terminal."""
    size = os.get_terminal_size()
    return size.columns, size.lines


def supports_color() -> bool:
    """Verifica se o terminal suporta cores."""
    # Força cores se NO_COLOR não estiver definido
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def supports_unicode() -> bool:
    """Verifica se o terminal suporta Unicode."""
    # Windows com Windows Terminal ou VS Code suporta
    if sys.platform == "win32":
        return os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") == "vscode"
    return True


def create_console() -> Console:
    """Cria console Rich configurado para o ambiente."""
    return Console(
        force_terminal=supports_color(),
        no_color=not supports_color(),
        emoji=supports_unicode(),
    )
```

---

## Implementação

### Fase 1: Setup Base (1-2h)

| ID | Tarefa | Estimativa |
|----|--------|------------|
| **S1** | Adicionar `rich>=13.9.0` e `questionary>=2.0.0` ao pyproject.toml | 15min |
| **S2** | Criar estrutura de diretórios `src/cli/shared/` | 15min |
| **S3** | Implementar `theme.py` com ColorPalette e estilos | 30min |
| **S4** | Implementar `terminal.py` com utilitários | 30min |

### Fase 2: Componentes UI (2-3h)

| ID | Tarefa | Estimativa |
|----|--------|------------|
| **S5** | Implementar `panels.py` com painéis base | 45min |
| **S6** | Implementar `progress.py` com spinners e barras | 45min |
| **S7** | Implementar `prompts.py` com prompts Questionary | 45min |
| **S8** | Criar `components.py` com exports unificados | 30min |

### Fase 3: Testes (1-2h)

| ID | Tarefa | Estimativa |
|----|--------|------------|
| **S9** | Testes unitários para `theme.py` | 30min |
| **S10** | Testes unitários para `panels.py` | 30min |
| **S11** | Testes unitários para `prompts.py` (mock questionary) | 30min |
| **S12** | Teste de integração visual (manual ou snapshot) | 30min |

**Total Estimado**: 4-7 horas

---

## Critérios de Aceite

### Funcional
- [ ] Todos os componentes importáveis via `from src.cli.shared.ui import *`
- [ ] Tema Rich aplicado corretamente em painéis e progress bars
- [ ] Estilo Questionary consistente em todos os prompts
- [ ] Fallback gracioso em terminais sem suporte a cores/unicode

### Qualidade
- [ ] Cobertura de testes > 80%
- [ ] Zero erros de mypy/ruff
- [ ] Documentação de uso em docstrings

### Integração
- [ ] `03P-cli-chat.md` consegue usar componentes sem duplicação
- [ ] `02P-catalog-ai-enrichment.md` consegue usar componentes sem duplicação

---

## Uso pelos Planos Dependentes

### 03P-cli-chat.md

```python
# src/cli/chat/ui/renderer.py
from src.cli.shared.ui import (
    create_panel,
    error_panel,
    spinner,
    create_console,
    COLORS,
)
from src.cli.shared.ui.prompts import ask_select

# Uso direto dos componentes compartilhados
console = create_console()
console.print(create_panel("Conteúdo", "Título", icon="🔍"))
```

### 02P-catalog-ai-enrichment.md

```python
# src/cli/enrichment_ui.py
from src.cli.shared.ui import (
    success_panel,
    warning_panel,
    PhaseSpinner,
    create_bar_progress,
)
from src.cli.shared.ui.prompts import ask_approval, ask_text

# Workflow de aprovação
result = ask_approval("block_code", allow_edit=True)
if result == "approve":
    console.print(success_panel("Campo aprovado!", "Enriquecimento"))
```

---

## Referências

- [Rich Documentation](https://rich.readthedocs.io/)
- [Questionary Documentation](https://questionary.readthedocs.io/)
- [03P-cli-chat.md](./03P-cli-chat.md) - Plano dependente
- [02P-catalog-ai-enrichment.md](./02P-catalog-ai-enrichment.md) - Plano dependente

---

**Última Atualização**: 2026-02-04
