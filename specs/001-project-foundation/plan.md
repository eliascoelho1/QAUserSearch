<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Implementation Plan: Fundação do Projeto QAUserSearch

**Branch**: `001-project-foundation` | **Date**: 2026-01-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-project-foundation/spec.md`

## Summary

Configurar a fundação completa do projeto QAUserSearch: ambiente de desenvolvimento, estrutura de código, CI/CD e documentação inicial. Usando Python 3.11 com FastAPI para backend API, PostgreSQL para storage, e pytest para testes. O objetivo é permitir que novos desenvolvedores configurem o ambiente em menos de 15 minutos e comecem a contribuir imediatamente.

## Technical Context

**Language/Version**: Python 3.11 (LTS)  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn  
**Storage**: PostgreSQL (banco de QA existente + banco local para app)  
**Testing**: pytest, pytest-cov, pytest-asyncio, httpx (client de teste)  
**Target Platform**: Linux server (containerizado com Docker)  
**Type Checking**: mypy --strict (tipagem forte obrigatória, zero erros tolerados)  
**Project Type**: Single backend API (frontend será feature futura)  
**Performance Goals**: p95 < 2s buscas simples, p95 < 5s queries complexas (conforme constitution)  
**Constraints**: < 512MB RAM, suportar 50 usuários simultâneos (conforme constitution)  
**Scale/Scope**: Equipes de QA (~50 usuários), integração com bases de dados QA existentes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Requisito | Status | Evidência |
|-----------|-----------|--------|-----------|
| **I. Qualidade de Código** | Linting obrigatório, formatadores automáticos | ✅ PLANEJADO | Ruff + Black configurados |
| **I. Qualidade de Código** | Tipagem forte obrigatória | ✅ PLANEJADO | mypy --strict no CI |
| **I. Qualidade de Código** | Arquivos ≤ 300 linhas | ✅ PLANEJADO | Estrutura modular definida |
| **II. TDD** | Ciclo Red-Green-Refactor | ✅ PLANEJADO | pytest + fixtures estruturados |
| **II. TDD** | Cobertura ≥ 80% código de negócio | ✅ PLANEJADO | pytest-cov no CI |
| **II. TDD** | Estrutura tests/unit, integration, contract | ✅ PLANEJADO | Ver Source Code abaixo |
| **III. UX Consistency** | N/A para fundação | ⏭️ N/A | Backend apenas |
| **IV. Performance** | Logs estruturados | ✅ PLANEJADO | structlog configurado |
| **IV. Performance** | Métricas de latência | ✅ PLANEJADO | Prometheus metrics |
| **Quality Gates** | Lint, testes, build no CI | ✅ PLANEJADO | GitHub Actions workflow |
| **Development Workflow** | Conventional Commits | ✅ PLANEJADO | commitlint configurado |

**Gate Status**: ✅ PASSED - Nenhuma violação identificada

## Project Structure

### Documentation (this feature)

```text
specs/001-project-foundation/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py              # FastAPI app entry point
├── config.py            # Configurações e variáveis de ambiente
├── models/              # SQLAlchemy models
│   └── __init__.py
├── schemas/             # Pydantic schemas
│   └── __init__.py
├── services/            # Business logic
│   └── __init__.py
├── api/                 # FastAPI routers
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── health.py    # Health check endpoint
└── core/                # Cross-cutting concerns
    ├── __init__.py
    ├── logging.py       # Structured logging setup
    └── database.py      # Database connection

tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── unit/
│   └── __init__.py
├── integration/
│   └── __init__.py
└── contract/
    └── __init__.py

.github/
├── workflows/
│   └── ci.yml           # GitHub Actions CI pipeline
├── hooks/
│   ├── hooks.json       # Copilot hooks configuration
│   └── scripts/
│       ├── validate-python.sh  # Lint + typecheck por arquivo
│       ├── run-tests.sh        # Testes unitários (batch)
│       └── lib/
│           └── common.sh       # Funções compartilhadas
└── agents/
    └── copilot-instructions.md  # Agent context

docker/
├── Dockerfile
└── docker-compose.yml   # Local dev environment

docs/
└── architecture.md      # ADR e diagramas
```

**Structure Decision**: Estrutura single-project com separação clara entre api/, models/, schemas/, services/ e core/. Segue padrões FastAPI recomendados e permite evolução modular conforme features futuras.

## Copilot Hooks (Validação Automática)

Hooks configurados para validar modificações automaticamente durante sessões do GitHub Copilot.

### Comportamento

| Hook | Trigger | Ação | Bloqueante |
|------|---------|------|------------|
| `postToolUse` | Após `edit`/`create` em `.py` | Ruff + mypy no arquivo | ✅ Sim |
| `sessionEnd` | Sessão completa | pytest tests/unit/ | ✅ Sim |

### Estrutura

```text
.github/hooks/
├── hooks.json              # Configuração principal
└── scripts/
    ├── validate-python.sh  # Lint + typecheck (bloqueante)
    ├── run-tests.sh        # Testes unitários (bloqueante)
    └── lib/common.sh       # Funções utilitárias
```

### Fluxo de Validação

```
Agent edita arquivo.py
        │
        ▼
  postToolUse hook
        │
        ▼
┌───────────────────┐
│  ruff check file  │
└───────┬───────────┘
        │ falha?
        ├──────────▶ DENY + mensagem de erro
        │            (agente deve corrigir)
        ▼ ok
┌───────────────────┐
│  mypy --strict    │
└───────┬───────────┘
        │ falha?
        ├──────────▶ DENY + mensagem de erro
        │            (agente deve corrigir)
        ▼ ok
     ALLOW
   (continua)
```

### Integração Constitution

Os hooks garantem conformidade automática com:
- **I. Qualidade de Código**: Lint bloqueante
- **I. Qualidade de Código**: Tipagem forte bloqueante
- **II. TDD**: Testes bloqueantes (agente deve corrigir falhas)

## Complexity Tracking

> **Nenhuma violação identificada** - Estrutura segue princípios da constitution sem exceções.
