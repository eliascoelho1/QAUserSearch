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
Utilizar CrewAI com processo sequencial e 3 agentes especializados: Interpretador, Validador e Refinador.

### Rationale
- CrewAI permite definir agentes com roles claros (role, goal, backstory)
- Processo sequencial garante que cada etapa depende da anterior
- Separação de responsabilidades:
  - **Interpretador**: Converte linguagem natural → estrutura de query
  - **Validador**: Verifica segurança (blacklist) e conformidade com catálogo
  - **Refinador**: Ajusta query para performance e clareza
- YAML config recomendado para manutenibilidade

### Alternatives Considered
1. **LangGraph**: Mais flexível para workflows complexos, mas overhead maior para este caso
2. **Agente único com prompt longo**: Difícil debug, sem separação de responsabilidades
3. **Pipeline manual com funções**: Menos estruturado, harder to test

### Implementation Pattern

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

## 3. Integração OpenAI com Streaming

### Decision
Utilizar OpenAI SDK com streaming (`stream=True`) e retry com backoff exponencial (3 tentativas).

### Rationale
- Streaming permite feedback progressivo ao usuário via WebSocket
- Retry protege contra falhas transitórias da API
- Timeout de 15 segundos conforme especificação
- Modelo GPT-4 conforme definido nas clarifications

### Implementation Pattern

```python
from openai import AsyncOpenAI
from openai import RateLimitError, APIConnectionError
import asyncio

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.max_retries = 3
        self.timeout = 15

    async def stream_completion(self, messages: list[dict], on_chunk: callable):
        retries = 0
        backoff = 1

        while retries < self.max_retries:
            try:
                stream = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    stream=True,
                    timeout=self.timeout
                )
                async for chunk in stream:
                    if content := chunk.choices[0].delta.content:
                        await on_chunk(content)
                return
            except (RateLimitError, APIConnectionError):
                retries += 1
                await asyncio.sleep(backoff)
                backoff *= 2
            except Exception as e:
                raise
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
    "openai>=1.0.0",       # Cliente OpenAI com async support
    "crewai>=0.80.0",      # Framework multi-agent
    "websockets>=12.0",    # WebSocket utilities (opcional, FastAPI já inclui)
]
```

### Rationale
- `openai>=1.0.0`: SDK oficial com suporte a async e streaming
- `crewai>=0.80.0`: Framework estável para multi-agent (YAML config, process types)
- `websockets`: Já incluído via uvicorn[standard], mas explicitado para clareza

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
