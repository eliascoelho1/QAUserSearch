<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Implementation Plan: Catálogo de Metadados em YAML

**Branch**: `002-yaml-catalog` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-yaml-catalog/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Migrar o armazenamento do catálogo de metadados de fontes externas (external_sources e column_metadata) do PostgreSQL para arquivos YAML versionados no repositório. A abordagem técnica envolve criar uma nova camada de repositório (`CatalogFileRepository`) implementando um Protocol comum, com cache em memória com TTL configurável, e adaptar os serviços existentes (`CatalogService`, `CatalogContext`) para usar o novo repositório baseado em arquivos.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.115+, Pydantic 2.10+, PyYAML 6.0+, structlog 24.4+
**Storage**: YAML files (catalog/sources/{db_name}/{table_name}.yaml) + JSON Schema para validação
**Testing**: pytest 8.3+, pytest-asyncio, httpx para testes de API
**Target Platform**: Linux server (Docker container)
**Project Type**: single (FastAPI REST API)
**Performance Goals**: p95 < 200ms para leitura de catálogo, validação < 5s para 50 sources
**Constraints**: Cache TTL configurável (default 60s), sem dependência de PostgreSQL para catálogo
**Scale/Scope**: ~10 sources inicialmente, escalável para ~100 sources

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Qualidade de Código (Code Quality)

| Critério | Status | Notas |
|----------|--------|-------|
| Legibilidade | ✅ PASS | Nomes claros: `CatalogFileRepository`, `CatalogFileWriter`, `to_yaml_dict()` |
| Simplicidade (KISS) | ✅ PASS | Cache simples com dict + timestamps, sem Redis ou dependências extras |
| Manutenibilidade (SRP) | ✅ PASS | Separação clara: Repository (leitura), Writer (escrita), Protocol (interface) |
| Consistência | ✅ PASS | Segue padrões existentes do projeto (mypy strict, ruff, black) |
| Documentação | ✅ PASS | JSON Schema fornecido, docstrings obrigatórios |

### II. Test-Driven Development (TDD)

| Critério | Status | Notas |
|----------|--------|-------|
| Cobertura ≥ 80% | ✅ COMMIT | Testes unitários para Repository, Writer, Cache |
| 100% lógica crítica | ✅ COMMIT | Testes para parsing YAML, cache TTL, merge de campos manuais |
| Testes de contrato | ✅ COMMIT | Validação JSON Schema, compatibilidade com API existente |
| Testes de integração | ✅ COMMIT | Fluxo completo CLI → YAML → API |

### III. UX Consistency

| Critério | Status | Notas |
|----------|--------|-------|
| Feedback imediato | ✅ PASS | CLI exibe progresso durante extração |
| Tratamento de erros | ✅ PASS | Mensagens claras em português para erros de YAML corrompido |
| Compatibilidade API | ✅ PASS | Mesmos endpoints, mesmos schemas de resposta |

### IV. Performance

| Critério | Status | Notas |
|----------|--------|-------|
| p95 < 200ms | ✅ PASS | Cache evita I/O repetido |
| Memória < 512MB | ✅ PASS | Cache limitado a metadados (~100 sources max) |
| Concorrência | ✅ PASS | Thread-safe cache com mecanismo de lock para evitar thundering herd |

### Quality Gates Compliance

| Gate | Status |
|------|--------|
| Lint (zero errors) | ✅ COMMIT |
| Testes Unitários (100% passing, ≥80% coverage) | ✅ COMMIT |
| Testes de Integração | ✅ COMMIT |
| Testes de Contrato | ✅ COMMIT |
| Performance (sem regressão > 20%) | ✅ COMMIT |
| Build (sem erros) | ✅ COMMIT |

## Project Structure

### Documentation (this feature)

```text
specs/002-yaml-catalog/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml     # OpenAPI spec for catalog endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── config/
│   └── config.py                    # [MODIFY] Add CATALOG_PATH, CATALOG_CACHE_TTL_SECONDS
├── schemas/
│   └── catalog.py                   # [MODIFY] Add to_yaml_dict(), from_yaml_dict() methods
├── repositories/
│   └── catalog/
│       ├── __init__.py              # [MODIFY] Export new classes
│       ├── catalog_repository.py    # [EXISTING] DB repository (to be deprecated)
│       ├── protocol.py              # [NEW] CatalogRepositoryProtocol
│       └── file_repository.py       # [NEW] CatalogFileRepository with cache
├── services/
│   ├── catalog_service.py           # [MODIFY] Use CatalogFileWriter for output
│   └── catalog_file_writer.py       # [NEW] YAML file generation
├── dependencies/
│   └── catalog.py                   # [NEW] get_catalog_repository() factory
├── api/v1/
│   └── catalog.py                   # [MODIFY] Use CatalogFileRepository, remove DELETE
└── cli/
    └── catalog.py                   # [MODIFY] Add validate command, YAML output

catalog/                             # [NEW] Generated catalog structure
├── catalog.yaml                     # Index of all sources
├── schema/
│   └── source.schema.json           # JSON Schema for validation
└── sources/
    └── {db_name}/
        └── {table_name}.yaml        # Source metadata files

tests/
├── unit/
│   ├── test_catalog_file_repository.py   # [NEW] Repository tests
│   ├── test_catalog_file_writer.py       # [NEW] Writer tests
│   └── test_catalog_schemas_yaml.py      # [NEW] to_yaml_dict/from_yaml_dict tests
├── integration/
│   └── test_catalog_yaml_flow.py         # [NEW] CLI → YAML → API flow
└── contract/
    └── test_catalog_json_schema.py       # [NEW] JSON Schema validation tests
```

**Structure Decision**: Single project structure maintained. New files added following existing patterns (repositories/catalog/, services/). New `catalog/` directory at repo root for YAML files. New `dependencies/` directory for DI factories (following FastAPI patterns).

## Complexity Tracking

> No Constitution Check violations identified. All principles satisfied with standard implementation patterns.

## Constitution Check - Post-Design Re-evaluation

*Re-checked after Phase 1 design completion on 2026-02-03.*

### Re-evaluation Summary

| Principle | Pre-Design | Post-Design | Notes |
|-----------|------------|-------------|-------|
| I. Code Quality | ✅ PASS | ✅ PASS | Design maintains KISS principle |
| II. TDD | ✅ COMMIT | ✅ COMMIT | Test strategy defined in data-model.md |
| III. UX Consistency | ✅ PASS | ✅ PASS | API compatibility confirmed in OpenAPI |
| IV. Performance | ✅ PASS | ✅ PASS | Cache design addresses thundering herd |

### Design Decisions Validated

1. **Repository Protocol Pattern**: Follows existing `ExternalDataSource` Protocol pattern
2. **Cache Implementation**: Research confirmed dual-lock pattern (threading.Lock + asyncio.Lock) is necessary for FastAPI
3. **JSON Schema Validation**: `jsonschema` library chosen for mypy-strict compatibility with `types-jsonschema` stubs
4. **YAML Library**: PyYAML (already installed) used; ruamel.yaml deferred for future comment preservation

### No New Violations

All design decisions align with Constitution principles. No justifications needed in Complexity Tracking.

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Implementation Plan | `specs/002-yaml-catalog/plan.md` | ✅ Complete |
| Research | `specs/002-yaml-catalog/research.md` | ✅ Complete |
| Data Model | `specs/002-yaml-catalog/data-model.md` | ✅ Complete |
| OpenAPI Contract | `specs/002-yaml-catalog/contracts/openapi.yaml` | ✅ Complete |
| JSON Schema | `specs/002-yaml-catalog/contracts/source.schema.json` | ✅ Complete |
| Quickstart Guide | `specs/002-yaml-catalog/quickstart.md` | ✅ Complete |
| Agent Context | `AGENTS.md` | ✅ Updated |

