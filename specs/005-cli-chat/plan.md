# Implementation Plan: CLI Chat Interativo para QAUserSearch

**Branch**: `005-cli-chat` | **Date**: 2026-02-05 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification clarificada com 7 User Stories e 26 Functional Requirements

---

## Summary

Implementar um CLI chat interativo que permite aos usuários fazer queries em linguagem natural via WebSocket. O chat fornecerá feedback visual em tempo real através de spinners e painéis Rich, processará comandos especiais (/exit, /help, /clear, /history, /execute, /mock), e incluirá modo mock para desenvolvimento offline. O sistema utilizará a infraestrutura compartilhada do [003-cli-shared-ui](../003-cli-shared-ui/spec.md) e consumirá o endpoint WebSocket já existente em `/ws/query/interpret`.

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: websockets >=12.0, Typer >=0.15.0, Rich ^13.9.0, Questionary ^2.0.0 (via shared UI)  
**Storage**: N/A (sessão em memória, sem persistência entre sessões)  
**Testing**: pytest 8.3+, pytest-asyncio  
**Target Platform**: CLI multiplataforma (Linux, macOS, Windows com Windows Terminal)  
**Project Type**: Single project - módulo específico em `src/cli/chat/`  
**Performance Goals**: Feedback visual <100ms após input, resposta a navegação <50ms  
**Constraints**: Terminais 60+ colunas, funcionar com NO_COLOR=1, Ctrl+C graceful  
**Scale/Scope**: 1 CLI chat, ~8 módulos Python, integração com 1 endpoint WebSocket

---

## Constitution Check

*GATE: Verificação obrigatória antes da implementação. Re-check após Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| **I. Qualidade de Código** | PASS | Funções com responsabilidade única (WSChatClient, MockChatClient, MessageHandler separados), type hints completos, docstrings Google-style |
| **II. TDD** | PASS | Ciclo Red-Green-Refactor planejado, >80% cobertura para lógica de negócio (client, session, handlers), 100% para parsing de mensagens WS |
| **III. Consistência UX** | PASS | Usa componentes padronizados de shared UI (PhaseSpinner, create_panel, ask_select), feedback <100ms, mensagens em português, Ctrl+C tratado |
| **IV. Performance** | PASS | Feedback visual <100ms, prompts <50ms, sem persistência em memória longa |
| **Quality Gates** | PASS | Zero warnings lint/mypy/black, testes passando, cobertura em lógica crítica |

**Compliance Notes**:
- Testes de renderização visual têm baixo ROI (mesmo padrão do 003-cli-shared-ui)
- Testes de WebSocket real requerem servidor rodando (opcional para CI)
- MockChatClient garante 100% testabilidade offline

---

## Project Structure

### Documentation (this feature)

```text
specs/005-cli-chat/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (não aplicável - consume WS existente)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/cli/
├── __init__.py                    # Existente
├── main.py                        # NOVO: Entry point unificado (qa)
├── catalog.py                     # CLI existente (migrar para subcomando)
├── chat.py                        # NOVO: Subcomando (qa chat)
│
├── shared/                        # Existente (do [003-cli-shared-ui](../003-cli-shared-ui/spec.md))
│   ├── ui/
│   │   ├── theme.py
│   │   ├── panels.py
│   │   ├── progress.py
│   │   └── prompts.py
│   └── utils/
│       └── terminal.py
│
└── chat/                          # NOVO: Módulo específico do chat
    ├── __init__.py                # Re-exports públicos
    ├── client.py                  # WSChatClient async
    ├── mock_client.py             # MockChatClient com mesma interface
    ├── session.py                 # ChatSession state management
    ├── commands.py                # Processador de comandos especiais
    ├── renderer.py                # WelcomePanel, InterpretationPanel, QueryPanel
    └── handlers/
        ├── __init__.py
        ├── message_handler.py     # Processa mensagens WS por tipo
        └── suggestion_handler.py  # Gerencia prompts de sugestão/ambiguidade

tests/unit/cli/chat/
├── __init__.py
├── conftest.py                    # Fixtures: mock_ws, mock_session, mock_console
├── test_client.py                 # Testes WSChatClient
├── test_mock_client.py            # Testes MockChatClient
├── test_session.py                # Testes ChatSession
├── test_commands.py               # Testes de comandos especiais
├── test_handlers.py               # Testes MessageHandler, SuggestionHandler
└── test_renderer.py               # Testes de renderização (lógica, não visual)
```

**Structure Decision**: Single project com módulo específico em `src/cli/chat/`. Segue padrão existente do projeto e reutiliza infraestrutura de `src/cli/shared/`.

---

## Component Architecture

### Diagrama de Dependências entre Módulos

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              src/cli/chat/                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Clients                                        │    │
│  │  ┌─────────────────────────────┐     ┌─────────────────────────────┐    │    │
│  │  │ client.py (WSChatClient)    │     │ mock_client.py (MockClient) │    │    │
│  │  │ • connect() → AsyncIterator │     │ • Mesma interface async     │    │    │
│  │  │ • send_prompt(str)          │     │ • Simula delays realistas   │    │    │
│  │  │ • disconnect()              │     │ • Cenários de erro/ambig.   │    │    │
│  │  └──────────────┬──────────────┘     └──────────────┬──────────────┘    │    │
│  └─────────────────│────────────────────────────────────│──────────────────┘    │
│                    │                                    │                        │
│                    └────────────────┬───────────────────┘                        │
│                                     │ ChatClientProtocol                         │
│                                     ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                            Session                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ session.py (ChatSession)                                        │    │    │
│  │  │ • history: list[QueryRecord]  (últimas 10)                     │    │    │
│  │  │ • last_interpretation: InterpretationResponse | None           │    │    │
│  │  │ • last_query: QueryResponse | None                             │    │    │
│  │  │ • is_mock_mode: bool                                            │    │    │
│  │  │ • add_query(), get_history(), clear()                          │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                     │                                            │
│                                     ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Handlers                                       │    │
│  │  ┌────────────────────────┐          ┌────────────────────────┐         │    │
│  │  │ message_handler.py     │          │ suggestion_handler.py  │         │    │
│  │  │ • handle_status()      │          │ • handle_ambiguities() │         │    │
│  │  │ • handle_chunk()       │          │ • prompt_refinement()  │         │    │
│  │  │ • handle_interpret()   │          └───────────┬────────────┘         │    │
│  │  │ • handle_query()       │                      │                      │    │
│  │  │ • handle_error()       │                      │                      │    │
│  │  └───────────┬────────────┘                      │                      │    │
│  └──────────────│───────────────────────────────────│──────────────────────┘    │
│                 │                                   │                            │
│                 └─────────────────┬─────────────────┘                            │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Rendering                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ renderer.py                                                      │    │    │
│  │  │ • render_welcome() → Panel                                       │    │    │
│  │  │ • render_interpretation(InterpretationResponse) → Panel         │    │    │
│  │  │ • render_query(QueryResponse) → Panel com syntax highlight      │    │    │
│  │  │ • render_confidence_bar(float) → Progress bar colorida          │    │    │
│  │  │ • render_history(list[QueryRecord]) → Table                     │    │    │
│  │  │ • render_help() → Panel com comandos                            │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                              │
│                                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Commands                                       │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │ commands.py                                                      │    │    │
│  │  │ • is_command(str) → bool                                         │    │    │
│  │  │ • parse_command(str) → Command | None                           │    │    │
│  │  │ • execute_command(Command, ChatSession, Console) → CommandResult│    │    │
│  │  │ • Commands: EXIT, HELP, CLEAR, HISTORY, EXECUTE, MOCK          │    │    │
│  │  └─────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Depende de
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        src/cli/shared/ ([003-cli-shared-ui](../003-cli-shared-ui/spec.md))                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ theme.py   │  │ panels.py  │  │ progress.py│  │ prompts.py │                │
│  │ COLORS     │  │ info_panel │  │ PhaseSpinner│  │ ask_select │                │
│  │ get_icon() │  │ error_panel│  │ spinner()  │  │ ask_confirm│                │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Ordem de Implementação (por dependência)

1. `session.py` - sem dependências internas do chat
2. `client.py` - depende apenas de schemas do backend
3. `mock_client.py` - mesma interface de client.py
4. `commands.py` - depende de session.py, shared/ui
5. `renderer.py` - depende de shared/ui, schemas
6. `handlers/message_handler.py` - depende de renderer, session
7. `handlers/suggestion_handler.py` - depende de shared/ui/prompts
8. `chat.py` - orquestra todos os módulos
9. `main.py` - entry point unificado

---

## Contracts & Interfaces

### 1. Chat Client Protocol (`client.py`)

```python
"""Cliente WebSocket para comunicação com backend de interpretação."""
from __future__ import annotations

from abc import abstractmethod
from typing import AsyncIterator, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.websocket import WSMessageType


class ChatClientProtocol(Protocol):
    """Interface compartilhada entre WSChatClient e MockChatClient."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Estabelece conexão com o servidor."""
        ...
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Encerra conexão graciosamente."""
        ...
    
    @abstractmethod
    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Envia prompt e retorna iterador de mensagens de resposta.
        
        Args:
            prompt: Texto em linguagem natural
            
        Yields:
            Mensagens WebSocket (status, chunk, interpretation, query, error)
        """
        ...
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Indica se há conexão ativa."""
        ...


class WSChatClient:
    """Cliente WebSocket real para o endpoint /ws/query/interpret.
    
    Implementa reconexão automática com backoff exponencial.
    """
    
    def __init__(
        self,
        server_url: str = "ws://localhost:8000/ws/query/interpret",
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        ...
    
    async def connect(self) -> None:
        """Conecta ao servidor WebSocket."""
        ...
    
    async def disconnect(self) -> None:
        """Desconecta graciosamente."""
        ...
    
    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Envia prompt e processa respostas streaming."""
        ...
    
    @property
    def is_connected(self) -> bool:
        ...
```

### 2. Mock Client (`mock_client.py`)

```python
"""Cliente mock para desenvolvimento e testes offline."""
from __future__ import annotations

import asyncio
import random
from typing import AsyncIterator

from src.schemas.websocket import WSMessageType


class MockChatClient:
    """Cliente mock com mesma interface do WSChatClient.
    
    Simula delays realistas e cenários variados:
    - Interpretação normal (confiança alta)
    - Interpretação com ambiguidades
    - Erros de timeout
    - Erros de validação
    """
    
    def __init__(self, delay_range: tuple[float, float] = (0.5, 2.0)) -> None:
        """Inicializa mock client.
        
        Args:
            delay_range: Tupla (min, max) para delays simulados em segundos
        """
        ...
    
    async def connect(self) -> None:
        """Simula conexão (sempre sucede)."""
        ...
    
    async def disconnect(self) -> None:
        """Simula desconexão."""
        ...
    
    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        """Processa prompt e retorna respostas simuladas.
        
        Detecta palavras-chave para cenários especiais:
        - "erro" → simula erro
        - "ambiguidade" → simula resposta com ambiguidades
        - "timeout" → simula timeout
        - outros → interpretação normal
        """
        ...
    
    @property
    def is_connected(self) -> bool:
        ...
```

### 3. Chat Session (`session.py`)

```python
"""Gerenciamento de estado da sessão de chat."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.interpreter import InterpretationResponse, QueryResponse


@dataclass
class QueryRecord:
    """Registro de uma query na sessão."""
    
    prompt: str
    timestamp: datetime
    interpretation_summary: str | None = None
    sql: str | None = None
    confidence: float | None = None


@dataclass
class ChatSession:
    """Estado da sessão de chat interativo.
    
    Mantém histórico das últimas 10 queries e referências
    à última interpretação/query para comandos como /execute.
    """
    
    history: list[QueryRecord] = field(default_factory=list)
    last_interpretation: InterpretationResponse | None = None
    last_query: QueryResponse | None = None
    is_mock_mode: bool = False
    
    _max_history: int = field(default=10, repr=False)
    
    def add_query(
        self,
        prompt: str,
        interpretation: InterpretationResponse | None = None,
        query: QueryResponse | None = None,
    ) -> None:
        """Adiciona query ao histórico.
        
        Mantém apenas as últimas _max_history queries.
        """
        ...
    
    def get_history(self) -> list[QueryRecord]:
        """Retorna histórico de queries."""
        ...
    
    def clear(self) -> None:
        """Limpa histórico e estado."""
        ...
    
    def toggle_mock_mode(self) -> bool:
        """Alterna modo mock e retorna novo estado."""
        ...
```

### 4. Commands (`commands.py`)

```python
"""Processador de comandos especiais do chat."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from src.cli.chat.session import ChatSession


class CommandType(str, Enum):
    """Tipos de comandos especiais."""
    
    EXIT = "exit"
    QUIT = "quit"
    HELP = "help"
    CLEAR = "clear"
    HISTORY = "history"
    EXECUTE = "execute"
    MOCK = "mock"


@dataclass
class CommandResult:
    """Resultado da execução de um comando."""
    
    should_exit: bool = False
    should_clear: bool = False
    message: str | None = None


def is_command(text: str) -> bool:
    """Verifica se texto é um comando especial (começa com /)."""
    ...


def parse_command(text: str) -> CommandType | None:
    """Parseia texto em comando.
    
    Returns:
        CommandType se comando válido, None se não reconhecido.
    """
    ...


async def execute_command(
    command: CommandType,
    session: ChatSession,
    console: Console,
) -> CommandResult:
    """Executa comando especial.
    
    Args:
        command: Tipo de comando a executar
        session: Sessão atual do chat
        console: Console Rich para output
        
    Returns:
        Resultado indicando ação a tomar (exit, clear, etc.)
    """
    ...
```

### 5. Renderer (`renderer.py`)

```python
"""Renderização de componentes visuais do chat."""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

if TYPE_CHECKING:
    from src.schemas.interpreter import InterpretationResponse, QueryResponse
    from src.cli.chat.session import QueryRecord


def render_welcome(console: Console | None = None) -> Panel:
    """Renderiza tela de boas-vindas com banner ASCII e instruções.
    
    Inclui:
    - Banner ASCII "QA Chat"
    - Instruções de uso
    - Exemplos de queries
    - Comandos disponíveis
    """
    ...


def render_interpretation(
    interpretation: InterpretationResponse,
    console: Console | None = None,
) -> Panel:
    """Renderiza painel de interpretação.
    
    Inclui:
    - Resumo da interpretação
    - Barra de confiança visual
    - Tabela de entidades
    - Tabela de filtros
    """
    ...


def render_query(
    query: QueryResponse,
    console: Console | None = None,
) -> Panel:
    """Renderiza painel de query SQL com syntax highlighting.
    
    SQL keywords em azul, strings em verde, números em amarelo.
    """
    ...


def render_confidence_bar(confidence: float) -> RenderableType:
    """Renderiza barra de confiança colorida.
    
    - Verde (>=0.7): Alta confiança
    - Âmbar (>=0.5): Média confiança  
    - Vermelho (<0.5): Baixa confiança
    """
    ...


def render_history(records: list[QueryRecord]) -> Table:
    """Renderiza tabela de histórico de queries."""
    ...


def render_help() -> Panel:
    """Renderiza painel de ajuda com comandos disponíveis."""
    ...


def render_error(message: str, suggestions: list[str] | None = None) -> Panel:
    """Renderiza painel de erro com sugestões."""
    ...
```

### 6. Message Handler (`handlers/message_handler.py`)

```python
"""Processador de mensagens WebSocket."""
from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from src.schemas.websocket import (
        WSChunkMessage,
        WSErrorMessage,
        WSInterpretationMessage,
        WSQueryMessage,
        WSStatusMessage,
    )
    from src.cli.chat.session import ChatSession


class MessageHandler:
    """Processa mensagens WebSocket e atualiza UI/sessão.
    
    Cada tipo de mensagem tem tratamento específico:
    - status: Atualiza PhaseSpinner
    - chunk: Exibe conteúdo progressivo
    - interpretation: Renderiza painel de interpretação
    - query: Renderiza painel de SQL
    - error: Renderiza erro com sugestões
    """
    
    def __init__(
        self,
        session: ChatSession,
        console: Console,
    ) -> None:
        ...
    
    async def handle_status(self, message: WSStatusMessage) -> None:
        """Processa mensagem de status."""
        ...
    
    async def handle_chunk(self, message: WSChunkMessage) -> None:
        """Processa chunk de streaming."""
        ...
    
    async def handle_interpretation(
        self,
        message: WSInterpretationMessage,
    ) -> None:
        """Processa resultado de interpretação."""
        ...
    
    async def handle_query(self, message: WSQueryMessage) -> None:
        """Processa query gerada."""
        ...
    
    async def handle_error(self, message: WSErrorMessage) -> None:
        """Processa mensagem de erro."""
        ...
```

### 7. Suggestion Handler (`handlers/suggestion_handler.py`)

```python
"""Gerenciador de prompts de sugestão para ambiguidades."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.interpreter import InterpretationResponse


class SuggestionHandler:
    """Detecta ambiguidades e gerencia prompts interativos.
    
    Quando a interpretação contém ambiguidades críticas,
    apresenta opções ao usuário via Questionary select.
    """
    
    def has_critical_ambiguities(
        self,
        interpretation: InterpretationResponse,
    ) -> bool:
        """Verifica se há ambiguidades que requerem clarificação."""
        ...
    
    async def prompt_for_clarification(
        self,
        interpretation: InterpretationResponse,
    ) -> str | None:
        """Apresenta opções e retorna refinamento selecionado.
        
        Returns:
            String com clarificação, ou None se cancelado.
        """
        ...
```

### 8. Entry Point (`main.py` e `chat.py`)

```python
# main.py - Entry point unificado
"""Entry point unificado para CLI do QAUserSearch."""
import typer

from src.cli.catalog import app as catalog_app

app = typer.Typer(
    name="qa",
    help="QAUserSearch - Busca de massas de usuários em QA",
    no_args_is_help=True,
)

# Registra subcomandos
app.add_typer(catalog_app, name="catalog")

# chat será adicionado via lazy import para evitar carregar WebSocket desnecessariamente
@app.command()
def chat(
    mock: bool = typer.Option(False, "--mock", "-m", help="Usar modo mock (offline)"),
    server: str = typer.Option(
        "ws://localhost:8000/ws/query/interpret",
        "--server",
        "-s",
        help="URL do servidor WebSocket",
    ),
) -> None:
    """Inicia sessão de chat interativa."""
    from src.cli.chat import run_chat
    import asyncio
    asyncio.run(run_chat(mock=mock, server_url=server))


if __name__ == "__main__":
    app()
```

```python
# chat.py - Subcomando chat
"""Subcomando de chat interativo."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from src.cli.chat.client import ChatClientProtocol


async def run_chat(
    mock: bool = False,
    server_url: str = "ws://localhost:8000/ws/query/interpret",
) -> None:
    """Executa loop principal do chat interativo.
    
    Args:
        mock: Se True, usa MockChatClient
        server_url: URL do WebSocket (ignorado em modo mock)
    """
    ...
```

---

## WebSocket Protocol Reference

O CLI consome mensagens do endpoint existente `ws://localhost:8000/ws/query/interpret`:

```python
# Mensagem enviada pelo CLI
{
    "type": "interpret",
    "prompt": "usuários com cartão de crédito ativo"
}

# Mensagens recebidas (em ordem)
WSStatusMessage:    {"type": "status", "data": {"status": "interpreting|validating|refining|ready", "message": str}}
WSChunkMessage:     {"type": "chunk", "data": {"content": str, "agent": str}}
WSInterpretationMessage: {"type": "interpretation", "data": InterpretationResponse}
WSQueryMessage:     {"type": "query", "data": QueryResponse}
WSErrorMessage:     {"type": "error", "data": ErrorResponse}
```

Schemas referenciados de `src/schemas/interpreter.py` e `src/schemas/websocket.py`.

---

## Testability Considerations

### Estratégia de Testes (TDD-compliant)

| Componente | Tipo de Teste | Abordagem |
|------------|--------------|-----------|
| `ChatSession` | Unit | Estado isolado, histórico, limites |
| `WSChatClient` | Unit | Mock websockets, verificar mensagens |
| `MockChatClient` | Unit | Verificar cenários (normal, erro, ambiguidade) |
| `commands.py` | Unit | Parsing e execução de cada comando |
| `MessageHandler` | Unit | Mock console, verificar renderização chamada |
| `SuggestionHandler` | Unit | Mock questionary, verificar prompts |
| `renderer.py` | Unit | Verificar estrutura de outputs (não visual) |
| Fluxo completo | Integration | Mock server, verificar ciclo end-to-end |

### Fixtures Necessárias (`conftest.py`)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console


@pytest.fixture
def mock_console() -> MagicMock:
    """Console mock para capturar output."""
    console = MagicMock(spec=Console)
    console.print = MagicMock()
    return console


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """WebSocket mock para testes de client."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def chat_session() -> ChatSession:
    """Sessão de chat limpa para testes."""
    from src.cli.chat.session import ChatSession
    return ChatSession()


@pytest.fixture
def sample_interpretation() -> InterpretationResponse:
    """Interpretação de exemplo para testes."""
    from src.schemas.interpreter import (
        InterpretationResponse,
        InterpretationStatus,
        EntityResponse,
        FilterResponse,
        FilterOperator,
    )
    from uuid import uuid4
    
    return InterpretationResponse(
        id=uuid4(),
        status=InterpretationStatus.READY,
        summary="Buscar usuários com cartão ativo",
        entities=[EntityResponse(name="users", table_name="credit.users")],
        filters=[FilterResponse(field="card_status", operator=FilterOperator.EQUALS, value="active")],
        confidence=0.85,
    )
```

### Testes Críticos (Obrigatórios)

1. **Session state management**:
   - Histórico não excede 10 itens
   - `clear()` reseta todo estado
   - `toggle_mock_mode()` alterna corretamente

2. **Command parsing**:
   - `/exit` e `/quit` reconhecidos
   - Comandos case-insensitive
   - Texto sem `/` não é comando

3. **Message handling**:
   - Cada tipo de mensagem chama renderer correto
   - Erros são exibidos com sugestões

4. **Ctrl+C handling**:
   - KeyboardInterrupt durante input retorna None
   - Não propaga exceção para caller

5. **Mock client scenarios**:
   - "erro" no prompt → WSErrorMessage
   - "ambiguidade" → interpretação com ambiguidades
   - Prompt normal → fluxo completo

---

## Implementation Phases

### Phase 0: Research (1h)

| Task | Descrição | Estimativa |
|------|-----------|------------|
| R0.1 | Validar websockets async patterns (já tem código no projeto) | 15min |
| R0.2 | Revisar Rich Syntax para SQL highlighting | 15min |
| R0.3 | Analisar integração com shared UI | 30min |

### Phase 1: Foundation (3h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T1.1 | Criar estrutura de diretórios e `__init__.py` | - | 15min |
| T1.2 | `session.py` + testes | - | 45min |
| T1.3 | `commands.py` + testes | session.py | 45min |
| T1.4 | `renderer.py` (estrutura básica) | shared/ui | 60min |

### Phase 2: Clients (2.5h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T2.1 | `mock_client.py` + testes | schemas | 60min |
| T2.2 | `client.py` (WSChatClient) + testes | schemas | 60min |
| T2.3 | Testes de reconnection logic | T2.2 | 30min |

### Phase 3: Handlers (2h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T3.1 | `handlers/message_handler.py` + testes | renderer, session | 60min |
| T3.2 | `handlers/suggestion_handler.py` + testes | shared/ui/prompts | 45min |
| T3.3 | Integração handlers com renderer | T3.1, T3.2 | 15min |

### Phase 4: Entry Points (1.5h)

| Task | Módulo | Dependência | Estimativa |
|------|--------|-------------|------------|
| T4.1 | `chat.py` (subcomando) | All chat modules | 45min |
| T4.2 | `main.py` (entry point unificado) | chat.py, catalog.py | 30min |
| T4.3 | Atualizar pyproject.toml scripts | T4.2 | 15min |

### Phase 5: Polish (1h)

| Task | Descrição | Estimativa |
|------|-----------|------------|
| T5.1 | Testes de integração end-to-end (mock) | 30min |
| T5.2 | Lint/mypy/format | 15min |
| T5.3 | Verificação manual visual | 15min |

**Total Estimado**: 11 horas

---

## Complexity Tracking

> Nenhuma violação da Constitution identificada.

| Item | Justificativa |
|------|---------------|
| Testes visuais manuais | Constitution permite: componentes visuais têm baixo ROI para testes automatizados |
| Testes WebSocket real opcionais | Requer servidor rodando, não bloqueante para CI |

---

## Success Criteria (from Spec)

- [ ] **SC-001**: Fluxo básico completo em <10s (modo mock)
- [ ] **SC-002**: 6 comandos especiais funcionando
- [ ] **SC-003**: Modo mock 100% offline
- [ ] **SC-004**: Reconexão automática funciona
- [ ] **SC-005**: Zero erros mypy/ruff/black
- [ ] **SC-006**: Cobertura >80% para `src/cli/chat/`
- [ ] **SC-007**: Ctrl+C graceful em qualquer estado
- [ ] **SC-008**: Output legível com NO_COLOR=1
- [ ] **SC-009**: Sugestões interativas funcionam
- [ ] **SC-010**: Entry point `qa` com subcomandos

---

## References

- **Spec**: [specs/005-cli-chat/spec.md](./spec.md)
- **Shared UI**: [specs/003-cli-shared-ui/plan.md](../003-cli-shared-ui/plan.md)
- **WebSocket Endpoint**: `src/api/v1/websocket/interpreter_ws.py`
- **WebSocket Schemas**: `src/schemas/websocket.py`
- **Constitution**: `.specify/memory/constitution.md`
- **Rich Docs**: https://rich.readthedocs.io/
- **websockets Docs**: https://websockets.readthedocs.io/

---

**Next Step**: Execute `/speckit.tasks` para gerar tarefas TDD detalhadas
