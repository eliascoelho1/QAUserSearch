<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Implementation Plan: Interpretador LLM para Geração de Queries

**Branch**: `001-llm-query-interpreter` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-llm-query-interpreter/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementar um interpretador de linguagem natural que utiliza LLM (OpenAI GPT-4) para converter prompts de usuários QA em queries SQL válidas. O sistema utiliza **CrewAI** para orquestrar agentes especializados (interpretador, validador, refinador) e **WebSocket** para streaming de respostas em tempo real, permitindo feedback progressivo durante a geração da query.

**Integração com Catálogo Existente**: O sistema utiliza o `CatalogService` e os modelos `ExternalSource`/`ColumnMetadata` já existentes para:
- Validar entidades mencionadas no prompt contra tabelas conhecidas
- Mapear termos de negócio para colunas reais (`column_name`, `column_path`)
- Utilizar `inferred_type` para validar tipos de filtros
- Aproveitar `unique_values` de colunas enumeráveis para sugestões

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, CrewAI, OpenAI SDK, SQLAlchemy (async), Pydantic  
**Storage**: PostgreSQL (via asyncpg) para dados de QA, logs de auditoria em banco existente  
**Testing**: pytest, pytest-asyncio, pytest-cov (cobertura ≥80%)  
**Target Platform**: Linux server (Docker)  
**Project Type**: single (backend API)  
**Performance Goals**: p95 < 2s queries simples, p95 < 5s queries complexas, timeout LLM 15s  
**Constraints**: <512MB RAM, 50 usuários simultâneos, 100 resultados máximo por query  
**Scale/Scope**: 50 usuários simultâneos, catálogo de metadados existente

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Requisito | Status | Evidência |
|-----------|-----------|--------|-----------|
| I. Qualidade de Código | Legibilidade, Simplicidade, SRP | ✅ PASS | Arquitetura modular com serviços isolados |
| I. Qualidade de Código | Arquivos ≤300 linhas | ✅ PASS | Dividido em módulos: agents/, services/, api/ |
| I. Qualidade de Código | Linting obrigatório | ✅ PASS | ruff + black configurados em pyproject.toml |
| II. TDD | Ciclo Red-Green-Refactor | ✅ PASS | Testes primeiro para cada componente |
| II. TDD | Cobertura ≥80% negócio | ✅ PASS | pytest-cov configurado |
| II. TDD | 100% lógica crítica | ✅ PASS | Validação SQL, parsing, autenticação |
| II. TDD | Testes de contrato | ✅ PASS | Contratos OpenAPI definidos em contracts/ |
| III. UX | Feedback <100ms | ✅ PASS | WebSocket para streaming progressivo |
| III. UX | Erros em português | ✅ PASS | Mensagens localizadas para usuários |
| IV. Performance | p95 <2s simples | ✅ PASS | Cache de metadados, async |
| IV. Performance | 50 usuários simultâneos | ✅ PASS | ConnectionManager para WebSocket |
| IV. Performance | Logs estruturados | ✅ PASS | structlog já configurado |

**Quality Gates Pre-Implementation**:
- [x] Lint: ruff configurado
- [x] Testes: pytest-asyncio configurado
- [x] Build: hatchling configurado
- [ ] Code Review: será validado no PR

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-query-interpreter/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml     # API contracts for WebSocket + REST endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── agents/                      # CrewAI agents para interpretação LLM
│   ├── __init__.py
│   ├── config/
│   │   ├── agents.yaml          # Definições dos agentes (role, goal, backstory)
│   │   └── tasks.yaml           # Definições das tasks do crew
│   ├── interpreter_crew.py      # Crew principal de interpretação
│   ├── prompt_interpreter.py    # Agente interpretador de prompts
│   ├── query_validator.py       # Agente validador de queries
│   └── query_refiner.py         # Agente refinador de queries
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── query_interpreter.py  # REST + WebSocket endpoints
│       └── websocket/
│           ├── __init__.py
│           ├── connection_manager.py # Gerenciador de conexões WS
│           └── handlers.py           # Handlers de mensagens WS
├── models/
│   └── query/
│       ├── __init__.py
│       ├── interpretation.py    # Modelo de interpretação estruturada
│       ├── audit_log.py         # Modelo de log de auditoria
│       └── query_result.py      # Modelo de resultado de query
├── services/
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── openai_client.py     # Cliente OpenAI com retry
│   │   └── streaming.py         # Handlers de streaming
│   ├── query/
│   │   ├── __init__.py
│   │   ├── interpreter_service.py   # Serviço principal de interpretação
│   │   ├── validator_service.py     # Validação de segurança SQL
│   │   └── executor_service.py      # Execução de queries
│   └── audit/
│       ├── __init__.py
│       └── audit_service.py     # Serviço de log de auditoria
├── schemas/
│   └── query/
│       ├── __init__.py
│       ├── request.py           # DTOs de request
│       └── response.py          # DTOs de response
└── core/
    └── security/
        ├── __init__.py
        └── sql_blacklist.py     # Blacklist de comandos SQL

tests/
├── unit/
│   ├── agents/
│   │   └── test_interpreter_crew.py
│   ├── services/
│   │   ├── test_interpreter_service.py
│   │   ├── test_validator_service.py
│   │   └── test_executor_service.py
│   └── core/
│       └── test_sql_blacklist.py
├── integration/
│   ├── test_query_flow.py       # Fluxo completo prompt → resultado
│   └── test_websocket.py        # Testes de WebSocket
└── contract/
    ├── test_openai_contract.py  # Contrato com OpenAI
    └── test_database_contract.py # Contrato com banco QA
```

**Structure Decision**: Mantida estrutura `src/` existente do projeto. Adicionados módulos `agents/` para CrewAI, `api/v1/websocket/` para WebSocket handlers, e `services/llm/` e `services/query/` para lógica de negócio isolada.

## Constitution Check - Post-Design Validation

*Re-evaluation after Phase 1 design artifacts completed.*

| Princípio | Requisito | Status | Evidência |
|-----------|-----------|--------|-----------|
| I. Qualidade de Código | SRP | ✅ PASS | Cada serviço tem responsabilidade única (interpreter, validator, executor) |
| I. Qualidade de Código | Arquivos ≤300 linhas | ✅ PASS | Arquitetura modular evita arquivos grandes |
| II. TDD | Testes de contrato | ✅ PASS | `test_openai_contract.py`, `test_database_contract.py` planejados |
| II. TDD | Testes de integração | ✅ PASS | `test_query_flow.py`, `test_websocket.py` planejados |
| III. UX | Feedback <100ms | ✅ PASS | WebSocket streaming permite feedback instantâneo |
| III. UX | Erros em português | ✅ PASS | Schemas de erro com mensagens localizadas |
| IV. Performance | p95 <2s | ✅ PASS | Async em toda stack, cache de catálogo |
| IV. Performance | Logs estruturados | ✅ PASS | structlog + AuditLog para queries bloqueadas |

**Artifacts Delivered**:
- ✅ `research.md` - Decisões técnicas documentadas
- ✅ `data-model.md` - Entidades, schemas, state transitions
- ✅ `contracts/openapi.yaml` - API REST + WebSocket spec
- ✅ `quickstart.md` - Guia de uso e testes

## Complexity Tracking

> **No violations identified.** Design segue princípios da constituição sem exceções.
