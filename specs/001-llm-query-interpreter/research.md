# Research: Interpretador LLM para Geração de Queries

**Feature Branch**: `001-llm-query-interpreter`  
**Date**: 2026-01-30

## 1. WebSocket com FastAPI

### Decision
Utilizar WebSocket nativo do FastAPI com padrão `ConnectionManager` para gerenciar conexões e streaming de respostas LLM.

### Rationale
- FastAPI suporta WebSocket nativamente via `@app.websocket()` decorator
- Padrão `ConnectionManager` recomendado pela documentação oficial para múltiplas conexões
- Permite streaming progressivo de tokens da LLM para feedback em tempo real (<100ms)
- Compatível com arquitetura async existente do projeto (asyncpg, SQLAlchemy async)

### Alternatives Considered
1. **Server-Sent Events (SSE)**: Mais simples, mas unidirecional; não permite interação durante streaming
2. **Long Polling**: Overhead de conexões HTTP repetidas; latência maior
3. **Fast Channels (Django-style)**: Overhead adicional; projeto já usa FastAPI puro

### Implementation Pattern

```python
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    async def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_stream(self, session_id: str, data: dict):
        if ws := self.active_connections.get(session_id):
            await ws.send_json(data)
```

---

## 2. CrewAI para Encadeamento de Agentes

### Decision
Utilizar CrewAI com processo sequencial, 3 agentes especializados e **structured output via `response_format`** com modelos Pydantic.

### Rationale
- CrewAI permite definir agentes com roles claros (role, goal, backstory)
- Processo sequencial garante que cada etapa depende da anterior
- **`response_format` com Pydantic** garante saídas tipadas e validadas automaticamente
- Separação de responsabilidades:
  - **Interpretador**: Converte linguagem natural → estrutura de query
  - **Validador**: Verifica segurança (blacklist) e conformidade com catálogo
  - **Refinador**: Ajusta query para performance e clareza
- YAML config recomendado para manutenibilidade

### Alternatives Considered
1. **LangGraph**: Mais flexível para workflows complexos, mas overhead maior para este caso
2. **Agente único com prompt longo**: Difícil debug, sem separação de responsabilidades
3. **Pipeline manual com funções**: Menos estruturado, harder to test

### Implementation Pattern - LLM Client com `response_format`

A partir da documentação oficial do CrewAI, a criação do client LLM deve usar a classe `LLM` do CrewAI (não OpenAI SDK diretamente) com o parâmetro `response_format` para outputs estruturados:

```python
from crewai import LLM
from pydantic import BaseModel


# Modelos Pydantic para structured output
class InterpretedQuery(BaseModel):
    """Resultado da interpretação do prompt pelo LLM."""
    target_table: str
    filters: list[dict]
    select_columns: list[str]
    explanation: str
    confidence: float


class ValidationResult(BaseModel):
    """Resultado da validação de segurança."""
    is_valid: bool
    blocked_command: str | None = None
    security_notes: list[str]


class RefinedQuery(BaseModel):
    """Query refinada e otimizada."""
    sql_query: str
    explanation: str
    estimated_rows: int | None = None
    warnings: list[str]


# Criação do LLM Client com response_format
llm = LLM(
    model="openai/gpt-4o",
    api_key="your-api-key",        # Via env var OPENAI_API_KEY
    temperature=0.3,                # Baixo para consistência
    timeout=15.0,                   # 15s conforme spec
    max_retries=3,                  # 3 tentativas conforme spec
    max_tokens=4000,
    response_format=InterpretedQuery  # Structured output via Pydantic
)

# Chamada direta ao LLM com output tipado
response = llm.call(
    "Usuários com cartão de crédito ativo e fatura vencida há mais de 30 dias"
)
# response é do tipo InterpretedQuery com campos validados
print(response.target_table)  # "credit.invoice"
print(response.filters)       # [{"column": "status", "op": "=", "value": "overdue"}]
```

### Implementation Pattern - Task com `output_pydantic`

Para Tasks do CrewAI, usar o parâmetro `output_pydantic` ou `output_json`:

```python
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel


class QueryInterpretation(BaseModel):
    """Schema de saída estruturada da task de interpretação."""
    target_tables: list[str]
    filters: list[dict]
    select_columns: list[str]
    natural_explanation: str
    suggested_limit: int


# Agent com LLM configurado
interpreter_agent = Agent(
    role="Interpretador de Linguagem Natural",
    goal="Converter descrição em linguagem natural para estrutura de query SQL",
    backstory="""Você é um especialista em processamento de linguagem natural com
    profundo conhecimento do domínio bancário e de QA. Você entende
    o catálogo de dados e consegue mapear termos de negócio para
    entidades técnicas.""",
    llm="openai/gpt-4o",  # Ou instância LLM com response_format
    verbose=True
)

# Task com output estruturado
interpret_task = Task(
    description="""Interprete o seguinte prompt do usuário e identifique:
    1. Quais tabelas devem ser consultadas
    2. Quais filtros aplicar (coluna, operador, valor)
    3. Quais colunas selecionar
    
    Prompt: {user_prompt}
    
    Catálogo disponível:
    {catalog_context}
    """,
    expected_output="Estrutura JSON com tabelas, filtros e colunas identificados",
    agent=interpreter_agent,
    output_pydantic=QueryInterpretation  # Structured output garantido
)

# Crew com tasks estruturadas
crew = Crew(
    agents=[interpreter_agent],
    tasks=[interpret_task],
    process=Process.sequential,
    verbose=True
)

# Execução
result = crew.kickoff(inputs={
    "user_prompt": "usuários com cartão bloqueado por fraude",
    "catalog_context": catalog_markdown
})

# Acesso aos dados estruturados
print(result.pydantic.target_tables)  # ["card_account_authorization.card_main"]
print(result.pydantic.filters)        # [{"column": "block_reason", "op": "=", "value": "fraud"}]
print(result["natural_explanation"])  # Via dict-style também funciona
```

### YAML Config (Agents e Tasks)

```yaml
# config/agents.yaml
interpreter:
  role: "Interpretador de Linguagem Natural"
  goal: "Converter descrição em linguagem natural para estrutura de query SQL"
  backstory: |
    Você é um especialista em processamento de linguagem natural com
    profundo conhecimento do domínio bancário e de QA. Você entende
    o catálogo de dados e consegue mapear termos de negócio para
    entidades técnicas.
  verbose: true

validator:
  role: "Validador de Segurança SQL"
  goal: "Garantir que a query gerada é segura e não contém comandos proibidos"
  backstory: |
    Você é um especialista em segurança de banco de dados. Sua missão
    é garantir que nenhuma query maliciosa ou perigosa seja executada.
    Você conhece os comandos SQL que podem causar danos.

refiner:
  role: "Refinador de Queries"
  goal: "Otimizar a query para performance e clareza"
  backstory: |
    Você é um DBA experiente que sabe como escrever queries eficientes.
    Você adiciona limites, ordena resultados e garante que a query
    retorne dados relevantes.
```

```python
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

@CrewBase
class InterpreterCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Sequencial: interpreter → validator → refiner
            verbose=True
        )
```

---

## 3. Integração LLM via CrewAI (Não OpenAI SDK diretamente)

### Decision
Utilizar **CrewAI LLM class** (não OpenAI SDK diretamente) com `response_format` para structured output e configurações nativas de timeout/retry.

### Rationale
- **CrewAI LLM class** encapsula providers (OpenAI, Anthropic, etc.) com API unificada
- `response_format` com Pydantic garante outputs tipados e validados
- Retry e timeout são parâmetros nativos da classe LLM do CrewAI
- Não é necessário gerenciar streaming manualmente - CrewAI faz internamente
- Modelo GPT-4o conforme definido nas clarifications

### Implementation Pattern

```python
from crewai import LLM
from pydantic import BaseModel


class InterpretedQuery(BaseModel):
    """Structured output do LLM."""
    target_table: str
    filters: list[dict]
    select_columns: list[str]
    explanation: str


# Client LLM via CrewAI - NÃO usar AsyncOpenAI diretamente
llm = LLM(
    model="openai/gpt-4o",
    api_key="your-api-key",           # Via OPENAI_API_KEY env var
    temperature=0.3,                   # Baixo para consistência em queries
    timeout=15.0,                      # 15s conforme spec
    max_retries=3,                     # 3 tentativas com backoff automático
    max_tokens=4000,
    response_format=InterpretedQuery   # Structured output via Pydantic!
)

# Chamada com output estruturado
result = llm.call(
    """Contexto do catálogo:
    ...
    
    Prompt do usuário: usuários com cartão bloqueado"""
)

# result é InterpretedQuery, não string!
print(result.target_table)  # "card_main"
print(result.filters)       # [{"column": "card_status", "op": "=", "value": "blocked"}]
```

### Advanced Configuration

```python
from crewai import LLM

# Configuração completa conforme documentação CrewAI
llm = LLM(
    model="openai/gpt-4o",
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",  # Opcional: custom endpoint
    temperature=0.3,
    max_tokens=4000,
    timeout=15.0,                          # Request timeout em segundos
    max_retries=3,                         # Tentativas com backoff
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    seed=42,                               # Reproducibilidade
    response_format=InterpretedQuery       # Pydantic model para structured output
)
```

### Nota: Streaming para WebSocket

Para feedback progressivo ao usuário, o streaming deve ser configurado separadamente:

```python
# LLM com streaming habilitado
streaming_llm = LLM(
    model="openai/gpt-4o",
    stream=True,  # Habilita streaming
    timeout=15.0,
    max_retries=3
)

# Nota: response_format e stream=True podem ter comportamento diferente
# Para structured output final, use sem streaming
# Para feedback progressivo, use streaming sem response_format
```

---

## 4. Validação de Segurança SQL (Blacklist)

### Decision
Implementar blacklist de comandos SQL proibidos com regex e logging de auditoria.

### Rationale
- Comandos bloqueados: INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER
- Apenas SELECT permitido conforme FR-007
- Log de auditoria para queries bloqueadas conforme FR-008
- Mensagem de erro detalhada ao usuário

### Implementation Pattern

```python
import re
from dataclasses import dataclass

FORBIDDEN_COMMANDS = [
    r'\bINSERT\b',
    r'\bUPDATE\b',
    r'\bDELETE\b',
    r'\bDROP\b',
    r'\bTRUNCATE\b',
    r'\bALTER\b',
]

@dataclass
class ValidationResult:
    is_valid: bool
    blocked_command: str | None = None

def validate_query(query: str) -> ValidationResult:
    query_upper = query.upper()
    for pattern in FORBIDDEN_COMMANDS:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return ValidationResult(
                is_valid=False,
                blocked_command=pattern.replace(r'\b', '').strip()
            )
    return ValidationResult(is_valid=True)
```

---

## 5. Dependências Adicionais

### Decision
Adicionar as seguintes dependências ao projeto:

```toml
# pyproject.toml
dependencies = [
    # ... existentes ...
    "crewai==1.9.3",       # Framework multi-agent com LLM class e response_format
]
```

### Rationale
- `crewai==1.9.3`: Framework estável para multi-agent com:
  - Classe `LLM` que abstrai providers (OpenAI, Anthropic, etc.)
  - Suporte a `response_format` com Pydantic para structured output
  - Timeout e retry nativos
  - YAML config para agents e tasks
- **Não é necessário `openai` como dependência direta** - CrewAI já inclui e gerencia

---

## 6. Arquitetura de Fluxo

```
┌─────────────┐     WebSocket      ┌──────────────────┐
│   Cliente   │◄──────────────────►│  FastAPI WS      │
│   (QA UI)   │    streaming       │  Endpoint        │
└─────────────┘                    └────────┬─────────┘
                                            │
                                            ▼
                                   ┌──────────────────┐
                                   │  CrewAI Crew     │
                                   │  (Sequential)    │
                                   └────────┬─────────┘
                                            │
            ┌───────────────────────────────┼───────────────────────────────┐
            ▼                               ▼                               ▼
    ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
    │  Interpreter  │──────────────►│   Validator   │──────────────►│    Refiner    │
    │    Agent      │               │    Agent      │               │    Agent      │
    └───────┬───────┘               └───────┬───────┘               └───────┬───────┘
            │                               │                               │
    ┌───────┴───────┐               ┌───────┴───────┐               ┌───────┴───────┐
    │               │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼               ▼
┌─────────┐  ┌───────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ OpenAI  │  │ CatalogService│  │SQL Blacklist│  │ AuditLog    │  │ Catalog     │
│ GPT-4   │  │ (ExternalSource│  │ Validation  │  │ (se block)  │  │ Service     │
│         │  │ ColumnMetadata)│  │             │  │             │  │ (optimize)  │
└─────────┘  └───────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
                    │
                    ▼
            ┌───────────────────────────────────────────────┐
            │              PostgreSQL (Catalog)             │
            │  ┌─────────────────┐  ┌────────────────────┐  │
            │  │ external_sources│  │  column_metadata   │  │
            │  └─────────────────┘  └────────────────────┘  │
            └───────────────────────────────────────────────┘
```

---

## 7. Integração com Catálogo Existente

### Decision
Utilizar os serviços e modelos de catálogo já existentes no projeto (`CatalogService`, `ExternalSource`, `ColumnMetadata`) para validação e mapeamento de entidades.

### Rationale
- O catálogo já possui metadados ricos sobre as tabelas conhecidas:
  - `ExternalSource`: db_name, table_name, document_count
  - `ColumnMetadata`: column_name, column_path, inferred_type, is_enumerable, unique_values, sample_values
- Tabelas já catalogadas: `card_account_authorization.account_main`, `card_account_authorization.card_main`, `credit.invoice`, `credit.closed_invoice`
- Reutilizar infraestrutura evita duplicação e garante consistência

### Dados do Catálogo Utilizados para Interpretação

#### ExternalSource (Tabelas Disponíveis)

| Campo | Tipo | Uso para o LLM |
|-------|------|----------------|
| `db_name` | string | Identificar banco de dados (ex: `credit`, `card_account_authorization`) |
| `table_name` | string | Identificar tabela específica (ex: `invoice`, `account_main`) |
| `document_count` | int | Informar volume de dados disponível para expectativa de resultados |

#### ColumnMetadata (Schema das Colunas)

| Campo | Tipo | Uso para o LLM |
|-------|------|----------------|
| `column_name` | string | Nome da coluna para construir a query SQL |
| `column_path` | string | Caminho completo para campos nested (ex: `address.city`) |
| `inferred_type` | string | Tipo de dado para validar operadores de filtro (string, int, datetime, boolean, array) |
| `is_enumerable` | bool | Indica se coluna tem conjunto finito de valores conhecidos |
| `unique_values` | list | **Lista de valores possíveis** para colunas enumeráveis - essencial para mapear termos de negócio |
| `sample_values` | list | Exemplos de valores reais para contexto adicional |
| `description` | string | Descrição semântica da coluna (se enriquecido via LLM) |
| `is_required` | bool | Se campo é obrigatório (sempre presente nos registros) |
| `is_nullable` | bool | Se campo pode ser nulo |
| `presence_ratio` | float | Percentual de registros que possuem este campo |

### Exemplo de Contexto Enviado ao LLM

```markdown
# Catálogo de Dados QA

## credit.invoice (45.000 documentos)

| Coluna | Tipo | Obrigatório | Valores Possíveis |
|--------|------|-------------|-------------------|
| status | string | ✅ Sim | `open`, `paid`, `overdue`, `cancelled` |
| due_date | datetime | ✅ Sim | - |
| amount | number | ✅ Sim | - |
| user_id | string | ✅ Sim | - |
| payment_date | datetime | ❌ Não | - |
| days_overdue | number | ❌ Não | - |

## credit.closed_invoice (120.000 documentos)

| Coluna | Tipo | Obrigatório | Valores Possíveis |
|--------|------|-------------|-------------------|
| closure_reason | string | ✅ Sim | `paid`, `cancelled`, `written_off`, `merged` |
| closed_at | datetime | ✅ Sim | - |
| original_amount | number | ✅ Sim | - |

## card_account_authorization.card_main (80.000 documentos)

| Coluna | Tipo | Obrigatório | Valores Possíveis |
|--------|------|-------------|-------------------|
| card_status | string | ✅ Sim | `active`, `blocked`, `cancelled`, `expired` |
| card_type | string | ✅ Sim | `credit`, `debit`, `multiple` |
| credit_limit | number | ❌ Não | - |
| account_id | string | ✅ Sim | - |
| block_reason | string | ❌ Não | `fraud`, `user_request`, `overdue`, `lost` |

## card_account_authorization.account_main (50.000 documentos)

| Coluna | Tipo | Obrigatório | Valores Possíveis |
|--------|------|-------------|-------------------|
| account_status | string | ✅ Sim | `active`, `inactive`, `blocked`, `closed` |
| document_number | string | ✅ Sim | - |
| created_at | datetime | ✅ Sim | - |
| customer_type | string | ✅ Sim | `individual`, `business` |
```

### Mapeamento de Termos de Negócio

O campo `unique_values` permite que o LLM mapeie termos em linguagem natural para valores técnicos:

| Termo do Usuário | Coluna | Valor Técnico |
|------------------|--------|---------------|
| "cartão bloqueado" | card_status | `blocked` |
| "fatura vencida" | status | `overdue` |
| "conta ativa" | account_status | `active` |
| "cartão de crédito" | card_type | `credit` |
| "cliente pessoa física" | customer_type | `individual` |
| "fatura paga" | status | `paid` |
| "bloqueio por fraude" | block_reason | `fraud` |

### Integration Points

```python
# O agente Interpreter receberá contexto do catálogo
class CatalogContext:
    """Contexto do catálogo para o agente interpreter."""
    
    def __init__(self, catalog_service: CatalogService):
        self._catalog = catalog_service
    
    async def get_available_tables(self) -> list[dict]:
        """Retorna tabelas disponíveis para query."""
        sources = await self._catalog._repository.list_sources()
        return [
            {
                "db_name": s.db_name,
                "table_name": s.table_name,
                "full_name": f"{s.db_name}.{s.table_name}",
                "document_count": s.document_count,
            }
            for s in sources
        ]
    
    async def get_table_schema(self, db_name: str, table_name: str) -> dict:
        """Retorna schema de uma tabela para o LLM."""
        source = await self._catalog._repository.get_source_by_name(db_name, table_name)
        if not source:
            return None
        columns = await self._catalog._repository.get_columns(source.id)
        return {
            "table": f"{db_name}.{table_name}",
            "document_count": source.document_count,
            "columns": [
                {
                    "name": c.column_name,
                    "path": c.column_path,
                    "type": c.inferred_type,
                    "is_required": c.is_required,
                    "is_nullable": c.is_nullable,
                    "is_enumerable": c.is_enumerable,
                    "possible_values": c.unique_values if c.is_enumerable else None,
                    "sample_values": c.sample_values[:5] if c.sample_values else None,
                    "description": c.description,
                    "presence_ratio": c.presence_ratio,
                }
                for c in columns
            ]
        }
    
    async def build_llm_context(self) -> str:
        """Constrói o contexto completo do catálogo para o prompt do LLM."""
        sources = await self.get_available_tables()
        context_parts = ["# Catálogo de Dados QA\n"]
        
        for source in sources:
            schema = await self.get_table_schema(source["db_name"], source["table_name"])
            context_parts.append(f"\n## {schema['table']} ({schema['document_count']:,} documentos)\n")
            context_parts.append("| Coluna | Tipo | Obrigatório | Valores Possíveis |")
            context_parts.append("|--------|------|-------------|-------------------|")
            
            for col in schema["columns"]:
                required = "✅ Sim" if col["is_required"] else "❌ Não"
                values = ", ".join(f"`{v}`" for v in col["possible_values"]) if col["possible_values"] else "-"
                context_parts.append(f"| {col['name']} | {col['type']} | {required} | {values} |")
        
        return "\n".join(context_parts)
```

### Prompt Engineering com Catálogo

O agente Interpreter receberá o schema das tabelas como contexto:

```text
Você tem acesso às seguintes tabelas:

## card_account_authorization.account_main
Colunas:
- document_number (string): CPF/CNPJ do cliente
- account_status (string, enum): [active, inactive, blocked, closed]
- created_at (datetime): Data de criação da conta
...

## card_account_authorization.card_main
Colunas:
- card_status (string, enum): [active, blocked, cancelled, expired]
- card_type (string, enum): [credit, debit, multiple]
...

Dado o prompt do usuário, identifique as tabelas e colunas relevantes.
```

### Validation Flow

```
Prompt → Interpreter Agent → CatalogContext.get_table_schema()
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  Validar se tabelas │
                          │  e colunas existem  │
                          │  no catálogo        │
                          └─────────┬───────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │ não existe            │ existe                │
            ▼                       ▼                       │
    ┌───────────────┐       ┌───────────────┐              │
    │ Retornar erro │       │ Gerar query   │              │
    │ com sugestões │       │ com colunas   │              │
    │ de termos     │       │ corretas      │              │
    │ similares     │       │               │              │
    └───────────────┘       └───────────────┘              │
```

---

## Resolved Clarifications

| Item Original | Resolução |
|---------------|-----------|
| WebSocket pattern | ConnectionManager com session_id |
| CrewAI process | Sequential: Interpreter → Validator → Refiner |
| Streaming | OpenAI SDK stream=True + WebSocket send_json |
| Retry policy | 3 tentativas, backoff exponencial |
| SQL validation | Regex blacklist com audit logging |
| Catálogo de schemas | Integração com CatalogService/ColumnMetadata existentes |
