# Research: CLI Chat Interativo

**Feature**: 005-cli-chat  
**Date**: 2026-02-05  
**Status**: Completo

---

## Overview

Este documento consolida a pesquisa técnica necessária para implementar o CLI Chat interativo. A maioria das tecnologias já está em uso no projeto, portanto o foco é em padrões específicos e integração.

---

## 1. WebSocket Client Async (websockets library)

### Decision
Usar a biblioteca `websockets` (já instalada v12+) com padrão async/await nativo.

### Rationale
- Já utilizada no projeto (backend WebSocket endpoint)
- API simples e bem documentada
- Suporte nativo a asyncio
- Reconexão pode ser implementada manualmente com backoff

### Implementation Pattern

```python
import asyncio
import websockets
from typing import AsyncIterator

class WSChatClient:
    def __init__(self, url: str, max_retries: int = 3):
        self._url = url
        self._max_retries = max_retries
        self._ws: websockets.WebSocketClientProtocol | None = None
    
    async def connect(self) -> None:
        """Conecta com retry e backoff exponencial."""
        for attempt in range(self._max_retries):
            try:
                self._ws = await websockets.connect(self._url)
                return
            except Exception:
                if attempt == self._max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
    
    async def send_and_receive(self, prompt: str) -> AsyncIterator[dict]:
        """Envia prompt e yield mensagens até 'query' ou 'error'."""
        if not self._ws:
            raise RuntimeError("Not connected")
        
        await self._ws.send(json.dumps({"type": "interpret", "prompt": prompt}))
        
        while True:
            raw = await self._ws.recv()
            msg = json.loads(raw)
            yield msg
            if msg["type"] in ("query", "error"):
                break
```

### Alternatives Considered
- **aiohttp WebSocket**: Mais overhead, menos especializado
- **socketio**: Overkill para nosso caso simples

---

## 2. SQL Syntax Highlighting (Rich)

### Decision
Usar `rich.syntax.Syntax` com lexer "sql" para highlighting de queries.

### Rationale
- Rich já está instalado e configurado no projeto
- Syntax highlighting built-in para SQL
- Integra nativamente com Panels

### Implementation Pattern

```python
from rich.syntax import Syntax
from rich.panel import Panel

def render_query(sql: str) -> Panel:
    """Renderiza SQL com syntax highlighting."""
    syntax = Syntax(
        sql,
        "sql",
        theme="monokai",  # Ou usar tema custom baseado em COLORS
        line_numbers=False,
        word_wrap=True,
    )
    return Panel(syntax, title="Query SQL", border_style="primary")
```

### Color Mapping
- Keywords (SELECT, FROM, WHERE): Azul (`COLORS.INFO`)
- Strings ('value'): Verde (`COLORS.SUCCESS`)
- Numbers: Amarelo/Âmbar (`COLORS.ACCENT`)
- Comments: Cinza (`COLORS.TEXT_DIM`)

---

## 3. Integração com Shared UI

### Decision
Reutilizar componentes de `src/cli/shared/ui/` sem modificações.

### Components to Use

| Component | Use Case |
|-----------|----------|
| `COLORS` | Paleta de cores para painéis custom |
| `get_icon()` | Ícones em mensagens de status |
| `info_panel()` | Painel de boas-vindas |
| `error_panel()` | Erros de conexão/interpretação |
| `success_panel()` | Query gerada com sucesso |
| `warning_panel()` | Ambiguidades detectadas |
| `PhaseSpinner` | Fases de interpretação |
| `ask_select()` | Seleção de opções em ambiguidades |
| `supports_color()` | Verificar suporte a cores |
| `is_interactive()` | Verificar TTY para prompts |

### Rationale
- Garante consistência visual com outros CLIs
- Já testado e validado
- Reduz código duplicado

---

## 4. Input Handling com Ctrl+C

### Decision
Usar prompt-toolkit (via Rich) com tratamento de KeyboardInterrupt.

### Rationale
- Rich.Prompt já trata Ctrl+C internamente
- Questionary (para seleções) também trata
- Padrão: retornar None quando cancelado

### Implementation Pattern

```python
from rich.prompt import Prompt

def get_user_input(prompt: str = ">>> ") -> str | None:
    """Obtém input do usuário, retorna None se Ctrl+C."""
    try:
        return Prompt.ask(prompt)
    except KeyboardInterrupt:
        return None
```

Para o loop principal:

```python
async def run_chat():
    console = Console()
    while True:
        try:
            user_input = get_user_input()
            if user_input is None:
                console.print("\n[dim]Encerrando...[/dim]")
                break
            # Process input...
        except KeyboardInterrupt:
            # Durante processamento
            console.print("\n[dim]Operação cancelada[/dim]")
            continue
```

---

## 5. Mock Client Scenarios

### Decision
Implementar MockChatClient com detecção de keywords para cenários.

### Scenarios

| Keyword | Comportamento |
|---------|--------------|
| (default) | Interpretação normal, confiança 0.85 |
| "erro" | Retorna WSErrorMessage |
| "ambiguidade" ou "ambíguo" | Confiança 0.5, dados ambíguos |
| "timeout" | Delay de 35s (excede timeout) |
| "baixa confiança" | Confiança 0.3 |

### Implementation Pattern

```python
class MockChatClient:
    async def send_prompt(self, prompt: str) -> AsyncIterator[WSMessageType]:
        prompt_lower = prompt.lower()
        
        # Simular delay realista
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Status messages
        yield WSStatusMessage.create("interpreting", "Analisando prompt...")
        await asyncio.sleep(0.3)
        
        yield WSStatusMessage.create("validating", "Validando...")
        await asyncio.sleep(0.2)
        
        yield WSStatusMessage.create("refining", "Otimizando...")
        await asyncio.sleep(0.2)
        
        # Scenario-based response
        if "erro" in prompt_lower:
            yield WSErrorMessage.create(
                code="MOCK_ERROR",
                message="Erro simulado para testes",
                suggestions=["Remova 'erro' do prompt para continuar"]
            )
            return
        
        # ... outros cenários
        
        yield WSInterpretationMessage(data=self._create_interpretation(prompt))
        yield WSQueryMessage(data=self._create_query(prompt))
```

---

## 6. Entry Point Unificado

### Decision
Criar `src/cli/main.py` com Typer app que agrega subcomandos.

### Rationale
- Typer já é usado para catalog CLI
- Padrão moderno (similar a `git`, `docker`)
- Fácil adicionar novos subcomandos futuramente

### Implementation Pattern

```python
# src/cli/main.py
import typer

app = typer.Typer(name="qa", help="QAUserSearch CLI", no_args_is_help=True)

# Subcomando catalog (existente)
from src.cli.catalog import app as catalog_app
app.add_typer(catalog_app, name="catalog")

# Subcomando chat (novo)
@app.command()
def chat(
    mock: bool = typer.Option(False, "--mock", "-m"),
    server: str = typer.Option("ws://localhost:8000/ws/query/interpret", "--server", "-s"),
):
    """Inicia chat interativo."""
    import asyncio
    from src.cli.chat import run_chat
    asyncio.run(run_chat(mock=mock, server_url=server))
```

### pyproject.toml Update

```toml
[project.scripts]
qa = "src.cli.main:app"
qa-catalog = "src.cli.catalog:app"  # Manter para retrocompatibilidade
```

---

## 7. Confidence Bar Rendering

### Decision
Usar Rich Progress bar customizada com cores semânticas.

### Implementation Pattern

```python
from rich.progress import Progress, BarColumn, TextColumn
from rich.style import Style

def render_confidence_bar(confidence: float) -> str:
    """Renderiza barra de confiança inline."""
    # Determinar cor
    if confidence >= 0.7:
        color = COLORS.CONFIDENCE_HIGH  # Verde
    elif confidence >= 0.5:
        color = COLORS.CONFIDENCE_MEDIUM  # Âmbar
    else:
        color = COLORS.CONFIDENCE_LOW  # Vermelho
    
    # Criar barra simples (20 chars)
    filled = int(confidence * 20)
    bar = "█" * filled + "░" * (20 - filled)
    percentage = f"{int(confidence * 100)}%"
    
    return f"[{color}]{bar}[/] {percentage}"
```

### Visual Example

```
Confiança: ████████████████░░░░ 80%  (verde)
Confiança: ██████████░░░░░░░░░░ 50%  (âmbar)
Confiança: ██████░░░░░░░░░░░░░░ 30%  (vermelho)
```

---

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| WebSocket library | `websockets` com async/await |
| SQL highlighting | `rich.syntax.Syntax` lexer "sql" |
| Shared UI | Reutilizar sem modificações |
| Input handling | Rich.Prompt + KeyboardInterrupt → None |
| Mock scenarios | Keyword detection no prompt |
| Entry point | Typer app com subcomandos |
| Confidence bar | Rich inline com cores semânticas |

---

## Open Questions (Resolved)

1. **Q**: Persistir histórico entre sessões?  
   **A**: Não (out of scope para v1)

2. **Q**: Timeout padrão para WebSocket?  
   **A**: 30 segundos (alinhado com backend)

3. **Q**: Limite de caracteres no prompt?  
   **A**: 2000 (validado no frontend e backend)

---

**Next Step**: Implementar `data-model.md` e `quickstart.md`
