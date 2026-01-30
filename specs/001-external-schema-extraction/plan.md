<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Implementation Plan: Extração Automática de Schema de Bancos Externos

**Branch**: `001-external-schema-extraction` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-external-schema-extraction/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementar sistema de extração automática de schemas de bancos MongoDB externos a partir de amostras JSON, persistência em catálogo PostgreSQL local, e preparação estrutural para enriquecimento via LLM em versão futura. O sistema operará em dois ambientes (MOCK com arquivos locais, PROD com conexão direta), utilizando padrão Repository para abstrair a fonte de dados.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI 0.115+, Pydantic 2.10+, SQLAlchemy 2.0+ (asyncio), asyncpg 0.30+, structlog 24.4+  
**Storage**: PostgreSQL (catálogo de schemas via SQLAlchemy async), arquivos JSON (amostras MOCK em `res/db/`)  
**Testing**: pytest 8.3+, pytest-asyncio 0.25+, pytest-cov 6.0+, httpx 0.28+ (contract tests)  
**Target Platform**: Linux server (Docker), macOS (desenvolvimento)  
**Project Type**: Single project (API backend)  
**Performance Goals**: Extração de schema < 30s, consulta ao catálogo p95 < 1s  
**Constraints**: Memória < 512MB, suportar 50 usuários simultâneos  
**Scale/Scope**: 4 tabelas iniciais (account_main, card_main, invoice, closed_invoice), expansível sem alteração de código

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Qualidade de Código ✅
- [x] Nomes de variáveis/funções expressam propósito claramente
- [x] Soluções seguem princípio KISS
- [x] Funções com responsabilidade única (SRP)
- [x] Arquivos ≤ 300 linhas
- [x] Style guide seguido (ruff, black configurados)
- [x] APIs públicas documentadas

### II. Test-Driven Development ✅
- [x] Ciclo Red-Green-Refactor será seguido
- [x] Cobertura mínima 80% para código de negócio
- [x] 100% cobertura para lógica crítica (parsing de schema, inferência de tipos)
- [x] Testes de contrato para integrações (PostgreSQL, arquivos JSON)
- [x] Testes de integração para fluxos principais
- [x] Estrutura tests/unit, tests/integration, tests/contract existente

### III. Consistência UX ✅
- [x] Feedback imediato para operações (logs estruturados)
- [x] Mensagens de erro claras e acionáveis
- [x] API REST consistente com padrões existentes

### IV. Performance ✅
- [x] p95 < 2s para consultas simples ao catálogo
- [x] Logs estruturados para operações de DB
- [x] Métricas de latência por endpoint

## Project Structure

### Documentation (this feature)

```text
specs/001-external-schema-extraction/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── api/                      # Endpoints REST (existente)
│   └── v1/
│       └── catalog.py        # Endpoints de consulta ao catálogo (NOVO)
├── config.py                 # Configurações da aplicação (existente - adicionar novas vars)
├── core/                     # Infraestrutura e utilitários (existente)
│   └── database.py           # Conexão PostgreSQL async (existente)
├── models/
│   ├── catalog/              # Modelos SQLAlchemy do catálogo (NOVO)
│   │   ├── __init__.py
│   │   ├── external_source.py
│   │   └── column_metadata.py
│   └── external/             # Modelos de dados externos (existente - vazio)
├── repositories/
│   ├── catalog/              # Repositórios de acesso ao catálogo (NOVO)
│   │   ├── __init__.py
│   │   └── catalog_repository.py
│   └── external/             # Repositórios de acesso a dados externos (NOVO)
│       ├── __init__.py
│       ├── base.py           # Interface abstrata
│       ├── mock_repository.py
│       └── prod_repository.py
├── schemas/
│   ├── enums.py              # Enums (existente - adicionar DataSourceEnvironment, EnrichmentStatus)
│   └── catalog.py            # Pydantic schemas para API (NOVO)
└── services/
    ├── schema_extraction/    # Serviço de extração de schema (NOVO)
    │   ├── __init__.py
    │   ├── extractor.py      # Lógica de inferência de tipos
    │   └── analyzer.py       # Análise de cardinalidade/enumeráveis
    └── catalog_service.py    # Orquestração do catálogo (NOVO)

res/
└── db/                       # Arquivos JSON de amostras MOCK (existente)
    ├── card_account_authorization.account_main.json
    ├── card_account_authorization.card_main.json
    ├── credit.closed_invoice.json
    └── credit.invoice.json

tests/
├── contract/
│   └── test_catalog_contracts.py   # Contratos de API do catálogo (NOVO)
├── integration/
│   └── test_schema_extraction.py   # Integração extração + persistência (NOVO)
└── unit/
    ├── test_extractor.py           # Testes de inferência de tipos (NOVO)
    └── test_analyzer.py            # Testes de cardinalidade (NOVO)
```

**Structure Decision**: Single project (API backend). Estrutura existente já segue padrão de camadas (models, services, repositories, api). Novos componentes serão adicionados seguindo a mesma organização.

## Complexity Tracking

> **No violations identified.** Constitution Check passed with full compliance.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Implementation Plan | `specs/001-external-schema-extraction/plan.md` | ✅ Complete |
| Research | `specs/001-external-schema-extraction/research.md` | ✅ Complete |
| Data Model | `specs/001-external-schema-extraction/data-model.md` | ✅ Complete |
| API Contracts | `specs/001-external-schema-extraction/contracts/catalog-api.yaml` | ✅ Complete |
| Quickstart | `specs/001-external-schema-extraction/quickstart.md` | ✅ Complete |

## Next Steps

1. Execute `/speckit.tasks` para gerar lista de tarefas ordenada por dependências
2. Implementar seguindo ciclo TDD (Red-Green-Refactor)
3. Validar Quality Gates antes de merge
