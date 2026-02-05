# Data Model: CLI Chat Interativo

**Feature**: 005-cli-chat  
**Date**: 2026-02-05

---

## Overview

Este documento define os modelos de dados internos do CLI Chat. Note que o CLI **consome** schemas existentes do backend (`src/schemas/`) e não persiste dados - todos os modelos são em memória durante a sessão.

---

## 1. Session State Models

### QueryRecord

Registro de uma query na sessão para histórico.

```python
@dataclass
class QueryRecord:
    """Registro de query para histórico da sessão."""
    
    prompt: str                              # Texto original do usuário
    timestamp: datetime                      # Quando foi enviada
    interpretation_summary: str | None       # Resumo da interpretação
    sql: str | None                          # SQL gerado (se sucesso)
    confidence: float | None                 # Confiança (0.0-1.0)
    
    # Derivado
    @property
    def was_successful(self) -> bool:
        """True se gerou SQL válido."""
        return self.sql is not None
```

**Constraints**:
- `prompt`: 1-2000 caracteres
- `confidence`: 0.0 <= x <= 1.0
- `timestamp`: UTC

### ChatSession

Estado completo da sessão de chat.

```python
@dataclass
class ChatSession:
    """Estado da sessão de chat."""
    
    # Histórico (max 10 itens)
    history: list[QueryRecord] = field(default_factory=list)
    
    # Última operação (para /execute)
    last_interpretation: InterpretationResponse | None = None
    last_query: QueryResponse | None = None
    
    # Modo de operação
    is_mock_mode: bool = False
    
    # Configuração interna
    _max_history: int = 10
```

**Invariants**:
- `len(history) <= _max_history`
- Se `last_query` existe, `last_interpretation` também existe

---

## 2. Command Models

### CommandType

Enum de comandos especiais reconhecidos.

```python
class CommandType(str, Enum):
    """Tipos de comandos especiais do chat."""
    
    EXIT = "exit"      # Encerrar sessão
    QUIT = "quit"      # Alias para exit
    HELP = "help"      # Exibir ajuda
    CLEAR = "clear"    # Limpar tela
    HISTORY = "history"  # Listar histórico
    EXECUTE = "execute"  # Executar última query
    MOCK = "mock"      # Toggle modo mock
```

**Parsing Rules**:
- Comando deve começar com `/`
- Case-insensitive
- Aliases: `/exit` = `/quit`

### CommandResult

Resultado da execução de um comando.

```python
@dataclass
class CommandResult:
    """Resultado de comando especial."""
    
    should_exit: bool = False      # Encerrar loop principal
    should_clear: bool = False     # Limpar console
    message: str | None = None     # Mensagem a exibir (se houver)
```

---

## 3. Backend Schemas (Consumed)

O CLI **consome** os seguintes schemas do backend (não modifica):

### From `src/schemas/interpreter.py`

```python
class InterpretationResponse(BaseModel):
    id: UUID
    status: InterpretationStatus
    summary: str
    entities: list[EntityResponse]
    filters: list[FilterResponse]
    confidence: float
    ambiguities: list[AmbiguityResponse] | None = None

class QueryResponse(BaseModel):
    id: UUID
    sql: str
    is_valid: bool
    validation_errors: list[str]

class EntityResponse(BaseModel):
    name: str
    table_name: str
    alias: str | None = None

class FilterResponse(BaseModel):
    field: str
    operator: FilterOperator
    value: Any
    is_temporal: bool = False
```

### From `src/schemas/websocket.py`

```python
class WSStatusMessage(BaseModel):
    type: Literal["status"] = "status"
    data: dict[str, Any]  # {"status": str, "message": str}
    timestamp: datetime

class WSChunkMessage(BaseModel):
    type: Literal["chunk"] = "chunk"
    data: dict[str, Any]  # {"content": str, "agent": str}
    timestamp: datetime

class WSInterpretationMessage(BaseModel):
    type: Literal["interpretation"] = "interpretation"
    data: InterpretationResponse
    timestamp: datetime

class WSQueryMessage(BaseModel):
    type: Literal["query"] = "query"
    data: QueryResponse
    timestamp: datetime

class WSErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    data: ErrorResponse
    timestamp: datetime
```

---

## 4. Entity Relationships

```
┌─────────────────┐
│   ChatSession   │
│─────────────────│
│ history[]       │────────────┐
│ last_interpret. │            │
│ last_query      │            │
│ is_mock_mode    │            │
└─────────────────┘            │
                               │
                               ▼
                    ┌─────────────────┐
                    │   QueryRecord   │
                    │─────────────────│
                    │ prompt          │
                    │ timestamp       │
                    │ summary         │
                    │ sql             │
                    │ confidence      │
                    └─────────────────┘
                    
┌─────────────────┐
│   CommandType   │──────▶ ┌─────────────────┐
│ (enum)          │        │  CommandResult  │
└─────────────────┘        │─────────────────│
                           │ should_exit     │
                           │ should_clear    │
                           │ message         │
                           └─────────────────┘
```

---

## 5. State Transitions

### Session States

```
┌─────────────────────────────────────────────────────────────────┐
│                         IDLE                                     │
│  - Aguardando input do usuário                                  │
│  - history pode estar vazio ou não                              │
└─────────────────────────────────────────────────────────────────┘
        │                                    │
        │ User sends prompt                  │ User sends /command
        ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│   PROCESSING    │                 │ COMMAND_EXEC    │
│                 │                 │                 │
│ - PhaseSpinner  │                 │ - Executa cmd   │
│ - WS messages   │                 │ - Retorna result│
└────────┬────────┘                 └────────┬────────┘
         │                                   │
         │ interpretation/query/error        │ CommandResult
         ▼                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         IDLE                                     │
│  - Exibe resultado                                              │
│  - Atualiza history (se sucesso)                                │
│  - Aguarda próximo input                                        │
└─────────────────────────────────────────────────────────────────┘
         │
         │ /exit ou Ctrl+C
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       TERMINATED                                 │
│  - Conexão fechada                                              │
│  - Recursos liberados                                           │
└─────────────────────────────────────────────────────────────────┘
```

### History Management

```python
# Máximo de 10 itens
def add_query(self, record: QueryRecord) -> None:
    self.history.append(record)
    if len(self.history) > self._max_history:
        self.history.pop(0)  # Remove mais antigo (FIFO)
```

---

## 6. Validation Rules

### Prompt Validation

| Rule | Constraint | Error Message |
|------|------------|---------------|
| Non-empty | `len(prompt.strip()) > 0` | "Prompt não pode estar vazio" |
| Max length | `len(prompt) <= 2000` | "Prompt excede limite de 2000 caracteres" |

### Command Validation

| Rule | Constraint | Error Message |
|------|------------|---------------|
| Format | `text.startswith("/")` | N/A (não é comando) |
| Known | `text[1:] in CommandType` | "Comando desconhecido: /xxx" |

### Confidence Display

| Range | Label | Color |
|-------|-------|-------|
| >= 0.9 | "muito alta" | Verde |
| >= 0.7 | "alta" | Verde |
| >= 0.5 | "média" | Âmbar |
| >= 0.3 | "baixa" | Vermelho |
| < 0.3 | "muito baixa" | Vermelho |

---

## 7. Mock Data Examples

### Normal Interpretation

```python
InterpretationResponse(
    id=UUID("..."),
    status=InterpretationStatus.READY,
    summary="Buscar usuários com cartão de crédito ativo",
    entities=[
        EntityResponse(name="users", table_name="credit.users", alias="u"),
        EntityResponse(name="cards", table_name="credit.cards", alias="c"),
    ],
    filters=[
        FilterResponse(
            field="card_status",
            operator=FilterOperator.EQUALS,
            value="active",
            is_temporal=False,
        ),
    ],
    confidence=0.85,
)
```

### With Ambiguities

```python
InterpretationResponse(
    id=UUID("..."),
    status=InterpretationStatus.READY,
    summary="Buscar usuários ativos (ambíguo: conta ou cartão?)",
    entities=[...],
    filters=[...],
    confidence=0.5,
    ambiguities=[
        AmbiguityResponse(
            term="ativo",
            options=["status da conta", "status do cartão"],
            context="Pode se referir ao status da conta ou do cartão",
        ),
    ],
)
```

---

## Summary

| Model | Persisted | Source |
|-------|-----------|--------|
| ChatSession | No (memory) | New |
| QueryRecord | No (memory) | New |
| CommandType | N/A (enum) | New |
| CommandResult | No (transient) | New |
| InterpretationResponse | No | Backend schema |
| QueryResponse | No | Backend schema |
| WS*Message | No | Backend schema |

---

**Next Step**: Criar `quickstart.md` com instruções de desenvolvimento
