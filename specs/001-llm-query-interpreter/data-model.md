# Data Model: Interpretador LLM para Geração de Queries

**Feature Branch**: `001-llm-query-interpreter`  
**Date**: 2026-01-30

## Entidades

### 1. PromptInterpretation

Representa a interpretação estruturada do prompt do usuário.

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `id` | UUID | Gerado | Identificador único da interpretação |
| `original_prompt` | str | max 2000 chars | Prompt original do usuário |
| `entities` | list[Entity] | min 1 | Entidades identificadas no prompt |
| `filters` | list[Filter] | - | Filtros extraídos |
| `interpreted_at` | datetime | auto | Timestamp da interpretação |
| `confidence` | float | 0.0-1.0 | Confiança da interpretação |

### 2. Entity

Entidade identificada no prompt mapeada para o catálogo.

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `name` | str | not empty | Nome da entidade (ex: "usuário") |
| `table_name` | str | exists in catalog | Tabela correspondente no banco |
| `alias` | str | optional | Alias para a query |

### 3. Filter

Filtro/condição extraída do prompt.

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `field` | str | not empty | Campo do filtro |
| `operator` | FilterOperator | enum | Operador (=, >, <, LIKE, IN) |
| `value` | Any | type-checked | Valor do filtro |
| `is_temporal` | bool | default False | Se é condição temporal |

### 4. GeneratedQuery

Query SQL gerada e validada.

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `id` | UUID | Gerado | Identificador único |
| `interpretation_id` | UUID | FK | Referência à interpretação |
| `sql` | str | not empty | Query SQL gerada |
| `is_valid` | bool | required | Se passou validação de segurança |
| `validation_errors` | list[str] | - | Erros de validação, se houver |
| `generated_at` | datetime | auto | Timestamp da geração |
| `execution_limit` | int | default 100 | Limite de resultados |

### 5. QueryResult

Resultado da execução da query.

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `id` | UUID | Gerado | Identificador único |
| `query_id` | UUID | FK | Referência à query |
| `rows` | list[dict] | - | Dados retornados |
| `row_count` | int | ≥0 | Quantidade de registros |
| `is_partial` | bool | default False | Se resultado foi truncado |
| `executed_at` | datetime | auto | Timestamp da execução |
| `execution_time_ms` | int | ≥0 | Tempo de execução em ms |

### 6. AuditLog

Log de auditoria para queries bloqueadas (FR-008).

| Campo | Tipo | Validação | Descrição |
|-------|------|-----------|-----------|
| `id` | UUID | Gerado | Identificador único |
| `blocked_query` | str | not empty | Query que foi bloqueada |
| `original_prompt` | str | not empty | Prompt original |
| `blocked_command` | str | not empty | Comando que causou bloqueio |
| `timestamp` | datetime | auto | Timestamp do bloqueio |
| `reason` | str | not empty | Motivo do bloqueio |

> **Nota**: Conforme FR-008, NÃO registramos identificação do usuário no log de auditoria.

---

## Enums

### FilterOperator

```python
class FilterOperator(str, Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
```

### InterpretationStatus

```python
class InterpretationStatus(str, Enum):
    PENDING = "pending"
    INTERPRETING = "interpreting"
    VALIDATING = "validating"
    REFINING = "refining"
    READY = "ready"
    BLOCKED = "blocked"
    ERROR = "error"
```

---

## Relacionamentos

```
PromptInterpretation 1──────* Entity
PromptInterpretation 1──────* Filter
PromptInterpretation 1──────1 GeneratedQuery
GeneratedQuery 1──────1 QueryResult
GeneratedQuery 1──────0..1 AuditLog (apenas se bloqueada)
```

---

## Schemas Pydantic

### CrewAI `response_format` Models

Modelos Pydantic usados como `response_format` na classe `LLM` do CrewAI ou `output_pydantic` nas Tasks para garantir outputs estruturados e tipados.

```python
from pydantic import BaseModel, Field


class QueryFilter(BaseModel):
    """Filtro individual extraído do prompt."""
    column: str = Field(..., description="Nome da coluna no banco de dados")
    operator: str = Field(..., description="Operador SQL: =, !=, >, <, >=, <=, LIKE, IN, BETWEEN")
    value: str | int | float | list | None = Field(..., description="Valor do filtro")
    is_temporal: bool = Field(default=False, description="Se é uma condição temporal (ex: últimos 30 dias)")


class InterpretedQuery(BaseModel):
    """
    Structured output do Interpreter Agent.
    Usado como response_format na LLM do CrewAI.
    """
    target_tables: list[str] = Field(
        ..., 
        min_length=1,
        description="Tabelas identificadas no formato db_name.table_name"
    )
    filters: list[QueryFilter] = Field(
        default_factory=list,
        description="Filtros extraídos do prompt"
    )
    select_columns: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Colunas a selecionar (default: todas)"
    )
    joins: list[dict] | None = Field(
        default=None,
        description="JOINs necessários entre tabelas"
    )
    natural_explanation: str = Field(
        ..., 
        description="Explicação em linguagem natural da interpretação"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confiança da interpretação (0.0 a 1.0)"
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Ambiguidades detectadas no prompt"
    )


class ValidationResult(BaseModel):
    """
    Structured output do Validator Agent.
    Usado como output_pydantic na Task de validação.
    """
    is_valid: bool = Field(..., description="Se a query é segura para execução")
    blocked_commands: list[str] = Field(
        default_factory=list,
        description="Comandos SQL bloqueados encontrados"
    )
    security_warnings: list[str] = Field(
        default_factory=list,
        description="Avisos de segurança (não bloqueantes)"
    )
    catalog_validation: dict = Field(
        default_factory=dict,
        description="Validação contra o catálogo: tabelas e colunas existentes"
    )


class RefinedQuery(BaseModel):
    """
    Structured output do Refiner Agent.
    Usado como output_pydantic na Task de refinamento.
    """
    sql_query: str = Field(..., description="Query SQL final otimizada")
    explanation: str = Field(..., description="Explicação das otimizações aplicadas")
    applied_optimizations: list[str] = Field(
        default_factory=list,
        description="Lista de otimizações aplicadas"
    )
    estimated_rows: int | None = Field(
        default=None,
        description="Estimativa de linhas retornadas"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Avisos sobre a query (ex: resultado parcial)"
    )
    suggested_limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Limite sugerido de resultados"
    )


class InterpreterCrewOutput(BaseModel):
    """
    Output final do Crew de interpretação.
    Combina os outputs dos 3 agents.
    """
    interpretation: InterpretedQuery
    validation: ValidationResult
    refined_query: RefinedQuery
    status: str = Field(..., description="Status final: ready, blocked, error")
```

### Exemplo de Uso com CrewAI LLM

```python
from crewai import LLM

# LLM com response_format para output estruturado
interpreter_llm = LLM(
    model="openai/gpt-4o",
    temperature=0.3,
    timeout=15.0,
    max_retries=3,
    response_format=InterpretedQuery  # Garante output tipado
)

# Resultado é InterpretedQuery, não string
result = interpreter_llm.call(prompt_with_catalog_context)
print(result.target_tables)      # ["credit.invoice"]
print(result.filters[0].column)  # "status"
print(result.confidence)         # 0.85
```

### Exemplo de Uso com CrewAI Task

```python
from crewai import Task

interpret_task = Task(
    description="Interprete o prompt: {user_prompt}",
    expected_output="Estrutura com tabelas, filtros e explicação",
    agent=interpreter_agent,
    output_pydantic=InterpretedQuery  # Structured output garantido
)

# Após crew.kickoff()
result = crew.kickoff(inputs={"user_prompt": "..."})
print(result.pydantic.target_tables)  # Acesso tipado via .pydantic
print(result["confidence"])           # Acesso dict-style também funciona
```

---

### Request Schemas

```python
class InterpretPromptRequest(BaseModel):
    prompt: str = Field(..., max_length=2000, description="Prompt em linguagem natural")
    
class ExecuteQueryRequest(BaseModel):
    query_id: UUID
    limit: int = Field(default=100, ge=1, le=1000)
```

### Response Schemas

```python
class InterpretationResponse(BaseModel):
    id: UUID
    status: InterpretationStatus
    summary: str  # Resumo da interpretação para o usuário
    entities: list[EntityResponse]
    filters: list[FilterResponse]
    confidence: float

class QueryResponse(BaseModel):
    id: UUID
    sql: str
    is_valid: bool
    validation_errors: list[str] = []

class QueryResultResponse(BaseModel):
    query_id: UUID
    rows: list[dict]
    row_count: int
    is_partial: bool
    execution_time_ms: int
    
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None
    suggestions: list[str] = []
```

### WebSocket Message Schemas

```python
class WSMessage(BaseModel):
    type: str  # "status" | "chunk" | "interpretation" | "result" | "error"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class WSStatusMessage(WSMessage):
    type: Literal["status"] = "status"
    data: dict  # {"status": InterpretationStatus, "message": str}

class WSChunkMessage(WSMessage):
    type: Literal["chunk"] = "chunk"
    data: dict  # {"content": str, "agent": str}

class WSInterpretationMessage(WSMessage):
    type: Literal["interpretation"] = "interpretation"
    data: InterpretationResponse

class WSErrorMessage(WSMessage):
    type: Literal["error"] = "error"
    data: ErrorResponse
```

---

## State Transitions

### Interpretation Flow

```
                    ┌─────────┐
                    │ PENDING │
                    └────┬────┘
                         │ start
                         ▼
                ┌─────────────────┐
                │  INTERPRETING   │◄────┐
                └────────┬────────┘     │ retry (max 3)
                         │              │
        ┌────────────────┼──────────────┘
        │ LLM error      │ success
        ▼                ▼
    ┌───────┐    ┌─────────────┐
    │ ERROR │    │  VALIDATING │
    └───────┘    └──────┬──────┘
                        │
          ┌─────────────┼─────────────┐
          │ blocked     │ valid       │
          ▼             ▼             │
    ┌─────────┐   ┌─────────────┐     │
    │ BLOCKED │   │   REFINING  │     │
    └─────────┘   └──────┬──────┘     │
                         │ done       │
                         ▼            │
                    ┌─────────┐       │
                    │  READY  │◄──────┘ (skip refine if simple)
                    └─────────┘
```

---

## Índices Recomendados

```sql
-- AuditLog: busca por timestamp para análise
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);

-- AuditLog: busca por comando bloqueado para relatórios
CREATE INDEX idx_audit_log_blocked_command ON audit_log(blocked_command);
```

---

## Validações Críticas

| Entidade | Campo | Validação | Erro |
|----------|-------|-----------|------|
| PromptInterpretation | original_prompt | max 2000 chars | PROMPT_TOO_LONG |
| PromptInterpretation | entities | min 1 entity | NO_ENTITIES_FOUND |
| GeneratedQuery | sql | no forbidden commands | SQL_COMMAND_BLOCKED |
| GeneratedQuery | sql | valid SQL syntax | INVALID_SQL_SYNTAX |
| QueryResult | row_count | if > 100, is_partial=True | - |
| AuditLog | * | NO user identification | PRIVACY_VIOLATION |
