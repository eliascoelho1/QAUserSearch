<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Implementation Plan: Extração Automática de Schema de Bancos Externos

**Branch**: `001-external-schema-extraction` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-external-schema-extraction/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Sistema de extração automática de schemas de bancos MongoDB externos, com persistência em PostgreSQL local e enriquecimento semântico via OpenAI. A arquitetura segue padrão Repository com dois ambientes isolados (MOCK/PROD) e suporte a detecção de colunas enumeráveis por análise estatística de cardinalidade.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic 2.x, SQLAlchemy 2.x (async), asyncpg, structlog, OpenAI SDK  
**Storage**: PostgreSQL (catálogo local) + MongoDB (fontes externas, somente leitura)  
**Testing**: pytest, pytest-asyncio, pytest-cov (cobertura ≥80%)  
**Target Platform**: Linux server (Docker)  
**Project Type**: Single project (API backend)  
**Performance Goals**: Extração de schema <30s, consultas ao catálogo <1s (p95)  
**Constraints**: <512MB RAM, 50 usuários simultâneos  
**Scale/Scope**: 4 tabelas iniciais, expansível para N tabelas sem alteração de código

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Requisito | Status | Evidência |
|-----------|-----------|--------|-----------|
| **I. Qualidade de Código** | Nomes autoexplicativos, SRP, arquivos <300 linhas | ✅ PASS | Estrutura em camadas (models/, services/, repositories/) |
| **I. Qualidade de Código** | Linting obrigatório (ruff, black, mypy) | ✅ PASS | Configurado em pyproject.toml |
| **II. TDD** | Cobertura ≥80% código de negócio | ⏳ PENDING | Será validado na implementação |
| **II. TDD** | 100% cobertura lógica crítica (parsing, queries) | ⏳ PENDING | Será validado na implementação |
| **II. TDD** | Testes de contrato para integrações (DB, OpenAI) | ⏳ PENDING | Diretório tests/contract/ existe |
| **III. UX** | Feedback imediato <100ms | ✅ PASS | API async com FastAPI |
| **III. UX** | Mensagens de erro claras em português | ⏳ PENDING | Será validado na implementação |
| **IV. Performance** | p95 <2s queries simples, <5s complexas | ⏳ PENDING | Será validado com benchmarks |
| **IV. Performance** | <512MB RAM | ⏳ PENDING | Será validado em staging |
| **Quality Gates** | Lint zero warnings | ✅ PASS | CI configurado |
| **Quality Gates** | Testes 100% passando | ⏳ PENDING | Será validado na implementação |

## Project Structure

### Documentation (this feature)

```text
specs/001-external-schema-extraction/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── schema-api.yaml  # OpenAPI spec for schema endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── api/
│   └── routes/
│       └── schema.py           # Endpoints de extração e consulta de schemas
├── core/
│   └── exceptions.py           # Exceções de domínio
├── models/
│   ├── external/               # Modelos de fontes externas (já existe)
│   └── catalog/
│       ├── external_source.py  # Entidade ExternalSource
│       └── column_metadata.py  # Entidade ColumnMetadata
├── schemas/
│   ├── schema_extraction.py    # DTOs de request/response
│   └── catalog.py              # DTOs do catálogo
├── services/
│   ├── schema_extractor.py     # Lógica de extração de schema
│   ├── schema_enricher.py      # Integração com OpenAI para descrições
│   └── catalog_service.py      # Operações no catálogo
├── repositories/
│   ├── base.py                 # Repository abstrato
│   ├── mock_data_repository.py # Implementação MOCK (JSON local)
│   ├── mongo_data_repository.py # Implementação PROD (MongoDB)
│   └── catalog_repository.py   # Repository do catálogo PostgreSQL
└── config.py                   # Settings incluindo ENVIRONMENT, SAMPLE_SIZE, etc.

tests/
├── contract/
│   ├── test_openai_contract.py # Contrato com OpenAI
│   └── test_mongo_contract.py  # Contrato com MongoDB
├── integration/
│   ├── test_schema_extraction_flow.py
│   └── test_catalog_persistence.py
└── unit/
    ├── test_schema_extractor.py
    ├── test_schema_enricher.py
    ├── test_enumerable_detection.py
    └── test_catalog_service.py

res/
└── db/                         # Arquivos JSON mock (já existem)
    ├── card_account_authorization.account_main.json
    ├── card_account_authorization.card_main.json
    ├── credit.closed_invoice.json
    └── credit.invoice.json
```

**Structure Decision**: Single project seguindo estrutura existente com camadas bem definidas (api/services/repositories/models). Extensões adicionadas para suportar catálogo de schemas e conectores de ambiente.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *Nenhuma violação identificada* | - | - |

## Constitution Check (Post-Design)

*Re-avaliação após conclusão do Phase 1 design.*

| Princípio | Requisito | Status | Evidência |
|-----------|-----------|--------|-----------|
| **I. Qualidade de Código** | Nomes autoexplicativos, SRP | ✅ PASS | Entidades `ExternalSource`, `ColumnMetadata` com responsabilidades claras |
| **I. Qualidade de Código** | Arquivos <300 linhas | ✅ PASS | Estrutura modular com arquivos separados por domínio |
| **I. Qualidade de Código** | APIs públicas documentadas | ✅ PASS | OpenAPI spec completa em contracts/schema-api.yaml |
| **II. TDD** | Estrutura de testes definida | ✅ PASS | tests/unit/, tests/integration/, tests/contract/ mapeados |
| **II. TDD** | Testes de contrato planejados | ✅ PASS | test_openai_contract.py, test_mongo_contract.py definidos |
| **III. UX** | Feedback claro em APIs | ✅ PASS | Responses com status, mensagens e progress |
| **III. UX** | Tratamento de erros | ✅ PASS | ErrorResponse, ValidationErrorResponse em contrato |
| **IV. Performance** | Async para I/O | ✅ PASS | SQLAlchemy async, motor (MongoDB async) |
| **IV. Performance** | Batch processing LLM | ✅ PASS | Descrito em research.md |
| **Quality Gates** | Design alinhado com arquitetura | ✅ PASS | Repository pattern, DI, camadas separadas |

**Resultado**: ✅ DESIGN APROVADO - Nenhuma violação constitucional identificada.
