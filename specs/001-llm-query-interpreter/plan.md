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

Implementar um interpretador que utiliza LLM (OpenAI GPT-4o via CrewAI) para converter prompts em linguagem natural em queries SQL para busca de massas de dados em ambiente de QA. Utiliza arquitetura multi-agent com CrewAI (3 agentes: Interpretador, Validador, Refinador), WebSocket para streaming de feedback, e structured output via `response_format` com Pydantic para garantir respostas tipadas e validadas.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, CrewAI (1.9.3), Pydantic, SQLAlchemy async  
**Storage**: PostgreSQL (catálogo de metadados), MongoDB (dados de QA externos)  
**Testing**: pytest, pytest-asyncio, pytest-cov  
**Target Platform**: Linux server (Docker/Kubernetes)  
**Project Type**: web (backend API com frontend existente)  
**Performance Goals**: p95 < 2s para queries simples, p95 < 15s para interpretação LLM  
**Constraints**: Timeout LLM 15s, retry 3x, apenas SELECT permitido (blacklist de INSERT/UPDATE/DELETE/DROP/TRUNCATE/ALTER)  
**Scale/Scope**: 50 usuários simultâneos, catálogo com ~4 tabelas (~300k documentos total)

### Principais Decisões Técnicas (do research.md)

1. **CrewAI com `response_format`**: Usar classe `LLM` do CrewAI (não OpenAI SDK diretamente) com `response_format=PydanticModel` para outputs estruturados e tipados
2. **Tasks com `output_pydantic`**: Cada task do CrewAI define seu output via modelo Pydantic
3. **WebSocket com ConnectionManager**: Streaming de feedback progressivo ao usuário
4. **Integração com Catálogo existente**: Usar `CatalogService`, `ExternalSource`, `ColumnMetadata` já implementados

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| **I. Qualidade de Código** | ✅ PASS | Estrutura modular com separação de responsabilidades (agents, services, schemas). Ruff/Black/MyPy configurados |
| **II. TDD (Não Negociável)** | ✅ PASS | Estrutura tests/unit, tests/integration, tests/contract definida. pytest-asyncio configurado |
| **III. UX Consistency** | ✅ PASS | WebSocket com streaming para feedback <100ms. Mensagens de erro claras em português |
| **IV. Performance** | ✅ PASS | Timeout 15s para LLM, limite de 100 resultados, catálogo com métricas de volume |

### Quality Gates Aplicáveis

| Gate | Critério | Aplicação nesta Feature |
|------|----------|------------------------|
| Lint | Zero warnings | Ruff/Black obrigatórios |
| Testes Unitários | ≥80% cobertura | Testar agents, validators, catalog context |
| Testes Integração | 100% passando | Fluxo completo prompt→query→resultado |
| Testes Contrato | 100% passando | WebSocket messages, API responses |
| Code Review | 1 aprovação | PR para main |

## Project Structure

### Documentation (this feature)

```text
specs/001-llm-query-interpreter/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - WebSocket, CrewAI, LLM patterns
├── data-model.md        # Phase 1 output - Pydantic models para response_format
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output - WebSocket messages, API schemas
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── api/
│   └── v1/
│       ├── interpreter.py       # WebSocket endpoint para interpretação
│       └── ...                   # Endpoints existentes
├── services/
│   ├── interpreter/             # Novo: Serviços do interpretador LLM
│   │   ├── __init__.py
│   │   ├── crew.py              # CrewAI Crew com agents e tasks
│   │   ├── agents.py            # Definição dos 3 agents (ou via YAML)
│   │   ├── tasks.py             # Tasks com output_pydantic
│   │   ├── catalog_context.py   # Geração de contexto do catálogo para LLM
│   │   └── validator.py         # Validação de segurança SQL
│   ├── catalog_service.py       # Existente: serviço de catálogo
│   └── ...
├── schemas/
│   ├── interpreter.py           # Novo: Pydantic models para response_format
│   │   # InterpretedQuery, ValidationResult, RefinedQuery, etc.
│   └── ...                      # Schemas existentes
├── config/                      # Novo: YAML configs para CrewAI
│   ├── agents.yaml              # Definição dos agents
│   └── tasks.yaml               # Definição das tasks
└── ...                          # Estrutura existente

tests/
├── unit/
│   └── services/
│       └── interpreter/
│           ├── test_validator.py
│           ├── test_catalog_context.py
│           └── test_agents.py
├── integration/
│   └── test_interpreter_flow.py
└── contract/
    └── test_websocket_messages.py
```

**Structure Decision**: Seguir estrutura existente (single project) adicionando `src/services/interpreter/` para a nova feature. Configurações YAML do CrewAI em `src/config/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
