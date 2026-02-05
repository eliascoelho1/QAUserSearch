# Implementation Plan: Infraestrutura Compartilhada de CLI UI

**Branch**: `01-cli-shared-ui` | **Date**: 2026-02-04 | **Spec**: `.specify/specs/01S-cli-shared-ui.md`  
**Input**: Feature specification clarificada com 7 User Stories e 14 Functional Requirements

---

## Summary

Implementar infraestrutura compartilhada de UI para todos os CLIs do QAUserSearch, incluindo:
- Sistema de tema unificado (cores, estilos Rich/Questionary)
- Painéis estilizados (info, success, warning, error) com fallback para ambientes limitados
- Indicadores de progresso (spinner, progress bar, PhaseSpinner)
- Prompts interativos com estilo consistente e tratamento de Ctrl+C
- Utilitários de detecção de capacidades do terminal

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Rich ^13.9.0 (já instalado v14.3.2), Questionary ^2.0.0 (já instalado v2.1.1), Typer >=0.15.0  
**Storage**: N/A (sem persistência)  
**Testing**: pytest 8.3+, pytest-asyncio  
**Target Platform**: CLI multiplataforma (Linux, macOS, Windows com Windows Terminal)  
**Project Type**: Single project - módulo compartilhado  
**Performance Goals**: Spinner refresh ≤100ms, prompt response <50ms  
**Constraints**: Funcionar em ambientes sem cores (NO_COLOR), sem unicode, sem TTY (CI)  
**Scale/Scope**: Base para 3+ CLIs (catalog, chat, enrichment)

---

## Constitution Check

*GATE: Verificação obrigatória antes da implementação*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| **I. Qualidade de Código** | ✅ PASS | Funções com responsabilidade única, docstrings Google-style, type hints completos |
| **II. TDD** | ✅ PASS | Testes unitários para lógica crítica (PhaseSpinner, Ctrl+C). Componentes visuais verificados manualmente |
| **III. Consistência UX** | ✅ PASS | Tema centralizado único, componentes padronizados, fallback gracioso, mensagens em português |
| **IV. Performance** | ✅ PASS | Spinner ≤100ms refresh, prompts <50ms response |
| **Quality Gates** | ✅ PASS | Zero warnings lint/mypy, testes passando, cobertura em lógica crítica |

**Compliance Notes**:
- Testes de renderização visual têm baixo ROI (Constitution permite foco em lógica crítica)
- Cobertura de 80% aplicada a lógica de negócio, não a wrappers de UI

---

## Project Structure

### Documentation (this feature)

```text
.specify/
├── specs/01S-cli-shared-ui.md    # Spec clarificada
├── plans/01P-cli-shared-ui.md    # Este arquivo
└── tasks/01T-cli-shared-ui.md    # Tarefas TDD (gerado por /speckit.tasks)
```

### Source Code (repository root)

```text
src/cli/
├── __init__.py                    # Existente
├── catalog.py                     # CLI existente (não modificar)
│
└── shared/                        # ← NOVO
    ├── __init__.py                # Re-exports públicos
    ├── ui/
    │   ├── __init__.py            # from .theme import *; from .panels import *; etc.
    │   ├── theme.py               # COLORS, get_rich_theme(), get_questionary_style()
    │   ├── panels.py              # create_panel(), info_panel(), success_panel(), etc.
    │   ├── progress.py            # spinner(), create_bar_progress(), PhaseSpinner, Phase
    │   └── prompts.py             # ask_*, ApprovalResult, ask_approval()
    └── utils/
        ├── __init__.py            # Re-exports
        └── terminal.py            # supports_color(), supports_unicode(), create_console()

tests/unit/cli/shared/
├── __init__.py
├── test_theme.py                  # Testes de ColorPalette e estilos
├── test_progress.py               # Testes de PhaseSpinner (lógica)
└── test_prompts.py                # Testes de Ctrl+C handling (mock)
```

**Structure Decision**: Single project com módulo compartilhado em `src/cli/shared/`. Segue padrão existente do projeto (src/services, src/core, etc).

---

## Component Architecture

### Diagrama de Dependências entre Módulos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           src/cli/shared/                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          utils/                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ terminal.py                                                  │    │    │
│  │  │ • supports_color() → bool                                   │    │    │
│  │  │ • supports_unicode() → bool                                 │    │    │
│  │  │ • get_terminal_size() → tuple[int, int]                     │    │    │
│  │  │ • is_interactive() → bool                                   │    │    │
│  │  │ • create_console() → Console                                │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           ui/                                        │    │
│  │                                                                      │    │
│  │  ┌───────────────┐                                                  │    │
│  │  │ theme.py      │◄────────────────────────────────────────────┐   │    │
│  │  │ • COLORS      │                                              │   │    │
│  │  │ • get_rich_theme()                                          │   │    │
│  │  │ • get_questionary_style()                                   │   │    │
│  │  │ • get_icon()  │                                              │   │    │
│  │  └───────┬───────┘                                              │   │    │
│  │          │                                                       │   │    │
│  │          ▼                                                       │   │    │
│  │  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐  │   │    │
│  │  │ panels.py     │     │ progress.py   │     │ prompts.py    │──┘   │    │
│  │  │ • create_panel│     │ • spinner()   │     │ • ask_text    │      │    │
│  │  │ • info_panel  │     │ • PhaseSpinner│     │ • ask_confirm │      │    │
│  │  │ • success_... │     │ • Phase       │     │ • ask_select  │      │    │
│  │  │ • warning_... │     │ • create_bar_ │     │ • ask_checkbox│      │    │
│  │  │ • error_panel │     │   progress    │     │ • ask_approval│      │    │
│  │  └───────────────┘     └───────────────┘     │ • ApprovalRes │      │    │
│  │          │                     │             └───────────────┘      │    │
│  │          │                     │                     │              │    │
│  │          └─────────────────────┴─────────────────────┘              │    │
│  │                                │                                     │    │
│  │                                ▼                                     │    │
│  │                    ┌───────────────────┐                            │    │
│  │                    │ __init__.py       │                            │    │
│  │                    │ (public exports)  │                            │    │
│  │                    └───────────────────┘                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ordem de Implementação (por dependência)

1. `utils/terminal.py` - sem dependências internas
2. `ui/theme.py` - sem dependências internas
3. `ui/panels.py` - depende de theme.py, terminal.py
4. `ui/progress.py` - depende de theme.py, terminal.py
5. `ui/prompts.py` - depende de theme.py
6. `__init__.py` files - re-exports

---

## Contracts & Interfaces

### 1. Theme Module (`ui/theme.py`)

```python
"""Sistema de tema unificado para CLI UI."""
from __future__ import annotations

from enum import Enum
from rich.style import Style
from rich.theme import Theme
from questionary import Style as QStyle


class COLORS:
    """Namespace de cores do QAUserSearch CLI."""
    
    # Brand
    PRIMARY: str = "#7C3AED"       # Roxo vibrante
    SECONDARY: str = "#06B6D4"    # Cyan
    ACCENT: str = "#F59E0B"       # Âmbar
    
    # Status
    SUCCESS: str = "#10B981"      # Verde esmeralda
    ERROR: str = "#EF4444"        # Vermelho coral
    WARNING: str = "#F59E0B"      # Âmbar
    INFO: str = "#3B82F6"         # Azul
    
    # Confidence (para barras semânticas)
    CONFIDENCE_HIGH: str = "#10B981"
    CONFIDENCE_MEDIUM: str = "#F59E0B"
    CONFIDENCE_LOW: str = "#EF4444"
    
    # Text
    TEXT: str = "#F9FAFB"
    TEXT_DIM: str = "#9CA3AF"
    TEXT_MUTED: str = "#6B7280"
    BORDER: str = "#374151"


class IconType(str, Enum):
    """Tipos de ícones com fallback ASCII."""
    
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SPINNER = "spinner"
    CHECK = "check"
    CROSS = "cross"


# Mapeamento emoji → ASCII
ICONS_EMOJI: dict[IconType, str] = {
    IconType.SUCCESS: "✅",
    IconType.ERROR: "❌",
    IconType.WARNING: "⚠️",
    IconType.INFO: "ℹ️",
    IconType.CHECK: "✓",
    IconType.CROSS: "✗",
}

ICONS_ASCII: dict[IconType, str] = {
    IconType.SUCCESS: "[OK]",
    IconType.ERROR: "[X]",
    IconType.WARNING: "[!]",
    IconType.INFO: "[i]",
    IconType.CHECK: "[OK]",
    IconType.CROSS: "[X]",
}


def get_icon(icon_type: IconType, use_unicode: bool = True) -> str:
    """Retorna ícone apropriado baseado em suporte unicode."""
    ...


def get_rich_theme() -> Theme:
    """Retorna tema Rich configurado com a paleta COLORS."""
    ...


def get_questionary_style() -> QStyle:
    """Retorna estilo Questionary alinhado com a paleta."""
    ...
```

### 2. Terminal Utils (`utils/terminal.py`)

```python
"""Utilitários de detecção de capacidades do terminal."""
from __future__ import annotations

from rich.console import Console


def get_terminal_size() -> tuple[int, int]:
    """Retorna (largura, altura) do terminal.
    
    Returns:
        Tupla (columns, lines). Fallback para (80, 24) se não detectável.
    """
    ...


def supports_color() -> bool:
    """Verifica se o terminal suporta cores ANSI.
    
    Considera:
        - NO_COLOR env var (força False)
        - FORCE_COLOR env var (força True)
        - isatty() check
    """
    ...


def supports_unicode() -> bool:
    """Verifica se o terminal suporta Unicode/emoji.
    
    Em Windows, requer Windows Terminal ou VS Code.
    Unix assume suporte por padrão.
    """
    ...


def is_interactive() -> bool:
    """Verifica se o terminal é interativo (TTY).
    
    Returns:
        False se stdin/stdout não são TTY (pipe, redirect, CI).
    """
    ...


def create_console(
    *,
    force_terminal: bool | None = None,
    no_color: bool | None = None,
    emoji: bool | None = None,
) -> Console:
    """Factory para criar Console Rich pré-configurado.
    
    Auto-detecta capacidades se parâmetros não fornecidos.
    Aplica tema Rich automaticamente.
    """
    ...
```

### 3. Panels Module (`ui/panels.py`)

```python
"""Painéis estilizados para feedback visual."""
from __future__ import annotations

from rich.panel import Panel
from rich.console import RenderableType


def create_panel(
    content: RenderableType,
    title: str,
    *,
    icon: str = "",
    style: str = "primary",
    subtitle: str | None = None,
    expand: bool = True,
) -> Panel:
    """Cria painel estilizado com tema.
    
    Args:
        content: Conteúdo renderizável (str, Text, Markdown, etc.)
        title: Título do painel
        icon: Ícone opcional (emoji ou ASCII)
        style: Nome do estilo do tema (primary, success, error, etc.)
        subtitle: Subtítulo opcional
        expand: Se True, expande para largura do terminal
    """
    ...


def info_panel(content: RenderableType, title: str = "Info") -> Panel:
    """Painel de informação (azul, ícone ℹ️)."""
    ...


def success_panel(content: RenderableType, title: str = "Sucesso") -> Panel:
    """Painel de sucesso (verde, ícone ✅)."""
    ...


def warning_panel(content: RenderableType, title: str = "Atenção") -> Panel:
    """Painel de aviso (âmbar, ícone ⚠️)."""
    ...


def error_panel(content: RenderableType, title: str = "Erro") -> Panel:
    """Painel de erro (vermelho, ícone ❌).
    
    NUNCA inclui stack traces - apenas mensagens user-friendly.
    """
    ...
```

### 4. Progress Module (`ui/progress.py`)

```python
"""Indicadores de progresso e spinners."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

from rich.console import Console
from rich.progress import Progress


@dataclass(frozen=True)
class Phase:
    """Definição de uma fase do PhaseSpinner.
    
    Attributes:
        key: Identificador único da fase
        label: Texto exibido ao usuário
        icon: Emoji ou ASCII para a fase
    """
    
    key: str
    label: str
    icon: str = "🔄"


@contextmanager
def spinner(
    description: str,
    console: Console | None = None,
) -> Generator[None, None, None]:
    """Context manager para exibir spinner durante operação.
    
    Em terminais não-interativos, imprime mensagem estática.
    
    Args:
        description: Texto exibido ao lado do spinner
        console: Console Rich opcional
        
    Example:
        with spinner("Conectando ao banco..."):
            await connect()
    """
    ...


def create_spinner_progress(console: Console | None = None) -> Progress:
    """Cria Progress com spinner para operações indeterminadas."""
    ...


def create_bar_progress(console: Console | None = None) -> Progress:
    """Cria Progress com barra para operações com total conhecido.
    
    Inclui: spinner, descrição, barra, porcentagem, tempo decorrido.
    """
    ...


class PhaseSpinner:
    """Spinner com múltiplas fases de progresso.
    
    Exibe lista de fases com status visual:
    - ○ Pendente (cinza)
    - ⠙ Em andamento (roxo, animado)
    - ✓ Completo (verde)
    
    Em terminais não-interativos, imprime cada fase como linha.
    
    Example:
        phases = [
            Phase("connect", "Conectando", "🔗"),
            Phase("extract", "Extraindo", "📦"),
            Phase("save", "Salvando", "💾"),
        ]
        spinner = PhaseSpinner(phases)
        with spinner.live():
            spinner.advance()  # Completa "connect", inicia "extract"
            spinner.advance()  # Completa "extract", inicia "save"
            spinner.complete() # Completa todas
    """
    
    def __init__(
        self,
        phases: list[Phase],
        console: Console | None = None,
    ) -> None:
        ...
    
    @contextmanager
    def live(self) -> Generator[PhaseSpinner, None, None]:
        """Context manager para Live display."""
        ...
    
    def advance(self) -> None:
        """Marca fase atual como completa e avança para próxima."""
        ...
    
    def complete(self) -> None:
        """Marca todas as fases como completas."""
        ...
    
    def fail(self, message: str | None = None) -> None:
        """Marca fase atual como falha."""
        ...
```

### 5. Prompts Module (`ui/prompts.py`)

```python
"""Prompts interativos padronizados."""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable

import questionary


class ApprovalResult(str, Enum):
    """Resultado de prompt de aprovação.
    
    Herda de str para compatibilidade com JSON/match statements.
    """
    
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    SKIP = "skip"
    CANCEL = "cancel"


def ask_text(
    message: str,
    *,
    default: str = "",
    validate: Callable[[str], bool | str] | None = None,
    multiline: bool = False,
) -> str | None:
    """Prompt para entrada de texto.
    
    Returns:
        Texto digitado, ou None se Ctrl+C/não-interativo.
    """
    ...


def ask_confirm(
    message: str,
    *,
    default: bool = True,
) -> bool | None:
    """Prompt de confirmação sim/não.
    
    Returns:
        True/False, ou None se Ctrl+C/não-interativo.
    """
    ...


def ask_select(
    message: str,
    choices: list[str | questionary.Choice],
    *,
    default: str | None = None,
    instruction: str = "Use ↑↓ para navegar, Enter para selecionar",
) -> str | None:
    """Prompt de seleção única.
    
    Returns:
        Valor selecionado, ou None se Ctrl+C/não-interativo.
    """
    ...


def ask_checkbox(
    message: str,
    choices: list[str | questionary.Choice],
    *,
    instruction: str = "Use ↑↓ para navegar, Espaço para selecionar, Enter para confirmar",
) -> list[str] | None:
    """Prompt de seleção múltipla.
    
    Returns:
        Lista de valores selecionados, ou None se Ctrl+C/não-interativo.
    """
    ...


def ask_approval(
    item_name: str,
    *,
    allow_edit: bool = True,
    allow_skip: bool = True,
) -> ApprovalResult | None:
    """Prompt padrão de aprovação para workflows de revisão.
    
    Opções:
        - ✓ Aprovar
        - ✏️ Editar (se allow_edit=True)
        - ✗ Rejeitar
        - ⏭️ Pular (se allow_skip=True)
        - 🛑 Cancelar
    
    Args:
        item_name: Nome do item sendo aprovado (exibido na pergunta)
        allow_edit: Se True, inclui opção de editar
        allow_skip: Se True, inclui opção de pular
        
    Returns:
        ApprovalResult enum, ou None se Ctrl+C/não-interativo.
    """
    ...
```

### 6. Public Exports (`ui/__init__.py`)

```python
"""Componentes de UI compartilhados para CLIs do QAUserSearch.

Usage:
    from src.cli.shared.ui import (
        # Theme
        COLORS,
        get_rich_theme,
        get_questionary_style,
        get_icon,
        IconType,
        
        # Panels
        create_panel,
        info_panel,
        success_panel,
        warning_panel,
        error_panel,
        
        # Progress
        spinner,
        create_spinner_progress,
        create_bar_progress,
        Phase,
        PhaseSpinner,
        
        # Prompts
        ask_text,
        ask_confirm,
        ask_select,
        ask_checkbox,
        ask_approval,
        ApprovalResult,
    )
"""
from .theme import (
    COLORS,
    IconType,
    get_icon,
    get_questionary_style,
    get_rich_theme,
)
from .panels import (
    create_panel,
    error_panel,
    info_panel,
    success_panel,
    warning_panel,
)
from .progress import (
    Phase,
    PhaseSpinner,
    create_bar_progress,
    create_spinner_progress,
    spinner,
)
from .prompts import (
    ApprovalResult,
    ask_approval,
    ask_checkbox,
    ask_confirm,
    ask_select,
    ask_text,
)

__all__ = [
    # Theme
    "COLORS",
    "IconType",
    "get_icon",
    "get_questionary_style",
    "get_rich_theme",
    # Panels
    "create_panel",
    "error_panel",
    "info_panel",
    "success_panel",
    "warning_panel",
    # Progress
    "Phase",
    "PhaseSpinner",
    "create_bar_progress",
    "create_spinner_progress",
    "spinner",
    # Prompts
    "ApprovalResult",
    "ask_approval",
    "ask_checkbox",
    "ask_confirm",
    "ask_select",
    "ask_text",
]
```

---

## Testability Considerations

### Estratégia de Testes (TDD-compliant)

| Componente | Tipo de Teste | Abordagem |
|------------|--------------|-----------|
| `COLORS` | Unit | Verificar constantes existem e são strings hex válidas |
| `get_icon()` | Unit | Verificar mapeamento emoji/ASCII correto |
| `supports_color()` | Unit | Mock `os.environ` e `sys.stdout.isatty()` |
| `supports_unicode()` | Unit | Mock `sys.platform` e env vars |
| `PhaseSpinner` | Unit | Verificar transições de estado (pending→active→complete) |
| `ask_*` prompts | Unit | Mock questionary, verificar KeyboardInterrupt retorna None |
| `ApprovalResult` | Unit | Verificar enum values e herança de str |
| Painéis | Manual | Verificação visual em diferentes terminais |

### Mocks Necessários

```python
# tests/unit/cli/shared/conftest.py

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_questionary(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock do módulo questionary para testes de prompts."""
    mock = MagicMock()
    monkeypatch.setattr("src.cli.shared.ui.prompts.questionary", mock)
    return mock


@pytest.fixture
def mock_terminal_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula terminal interativo com cores e unicode."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)


@pytest.fixture
def mock_terminal_non_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula terminal não-interativo (CI/pipe)."""
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
```

### Testes Críticos (Obrigatórios)

1. **PhaseSpinner state machine**:
   - Fase inicial é 0
   - `advance()` incrementa corretamente
   - `complete()` marca todas como completas
   - Não avança além do total de fases

2. **Ctrl+C handling**:
   - `ask_text()` retorna None quando KeyboardInterrupt
   - `ask_select()` retorna None quando KeyboardInterrupt
   - Nenhuma exceção propagada para o caller

3. **Terminal detection**:
   - `NO_COLOR=1` → `supports_color()` returns False
   - `FORCE_COLOR=1` → `supports_color()` returns True
   - Windows sem WT_SESSION → `supports_unicode()` returns False

---

## Implementation Phases

### Phase 1: Foundation (2h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T1.1 | Criar estrutura de diretórios | - | 15min |
| T1.2 | `utils/terminal.py` | - | 30min |
| T1.3 | `ui/theme.py` | - | 30min |
| T1.4 | Testes unit theme/terminal | T1.2, T1.3 | 45min |

### Phase 2: Components (2.5h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T2.1 | `ui/panels.py` | theme.py | 45min |
| T2.2 | `ui/progress.py` + Phase + PhaseSpinner | theme.py, terminal.py | 60min |
| T2.3 | Testes unit PhaseSpinner | T2.2 | 30min |

### Phase 3: Prompts (1.5h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T3.1 | `ui/prompts.py` + ApprovalResult | theme.py | 45min |
| T3.2 | Testes unit prompts (Ctrl+C) | T3.1 | 30min |

### Phase 4: Integration (1h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T4.1 | `__init__.py` exports | All | 15min |
| T4.2 | Verificação manual visual | All | 30min |
| T4.3 | Lint/mypy/format | All | 15min |

**Total Estimado**: 7 horas

---

## Complexity Tracking

> Nenhuma violação da Constitution identificada.

| Item | Justificativa |
|------|---------------|
| Testes visuais manuais | Constitution permite (CL-007): componentes visuais têm baixo ROI para testes automatizados |

---

## Success Criteria (from Spec)

- [ ] **SC-001**: 100% dos componentes importáveis via `from src.cli.shared.ui import *`
- [ ] **SC-002**: Zero erros de mypy/ruff/black
- [ ] **SC-003**: Testes unitários cobrem lógica crítica (PhaseSpinner, Ctrl+C)
- [ ] **SC-004**: Painéis renderizam em terminais 60+ colunas (manual)
- [ ] **SC-005**: Spinners animam sem flicker (manual)
- [ ] **SC-006**: Prompts respondem sem delay perceptível (manual)
- [ ] **SC-007**: Output legível com `NO_COLOR=1` (manual)
- [ ] **SC-008**: `ask_approval()` usável por plano 02P
- [ ] **SC-009**: Painéis/spinners usáveis por plano 03P

---

## References

- **Spec**: `.specify/specs/01S-cli-shared-ui.md`
- **Design Reference**: `docs/plans/01-cli-shared-ui.md`
- **Rich Docs**: https://rich.readthedocs.io/
- **Questionary Docs**: https://questionary.readthedocs.io/
- **Constitution**: `.specify/memory/constitution.md`

---

**Next Step**: Execute `/speckit.tasks` para gerar tarefas TDD detalhadas
