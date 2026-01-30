---
description: General development guidelines for the QAUserSearch project
---

# QAUserSearch Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-28

## Project Context

QAUserSearch is a Python FastAPI application for searching user data in QA environments. It provides a REST API for QA teams to find test user records across multiple databases.

> **📐 Architecture Reference**: For detailed architecture diagrams, layer responsibilities, and design decisions, see [docs/architecture.md](../../docs/architecture.md).

## Active Technologies
- Python 3.11 + FastAPI 0.115+, Pydantic 2.10+, SQLAlchemy 2.0+ (asyncio), asyncpg 0.30+, structlog 24.4+ (001-external-schema-extraction)
- PostgreSQL (catálogo de schemas via SQLAlchemy async), arquivos JSON (amostras MOCK em `res/db/`) (001-external-schema-extraction)

- **Language**: Python 3.11+ (LTS)
- **Framework**: FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn
- **Package Manager**: uv
- **Testing**: pytest with pytest-asyncio
- **Linting**: Ruff, Black
- **Type Checking**: mypy (strict mode)

## Project Structure

```text
src/
├── api/v1/          # FastAPI routers
├── core/            # Database, logging
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
├── config.py        # Settings
└── main.py          # App entry

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── contract/        # Contract tests
```

## Commands

```bash
# Run application
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Format
uv run black src/ tests/
```

## Code Style

### Type Annotations

All code MUST have complete type annotations:

```python
# ✅ Good
def get_user(user_id: int) -> User | None:
    ...

# ❌ Bad
def get_user(user_id):
    ...
```

### File Size

Keep files under 300 lines. Split into modules if larger.

### Documentation

- All public functions need docstrings
- Use Google-style docstrings

## Recent Changes
- 001-external-schema-extraction: Added Python 3.11 + FastAPI 0.115+, Pydantic 2.10+, SQLAlchemy 2.0+ (asyncio), asyncpg 0.30+, structlog 24.4+
- 001-external-schema-extraction: Added Python 3.11 + FastAPI, Pydantic 2.x, SQLAlchemy 2.x (async), asyncpg, structlog, OpenAI SDK

- 001-project-foundation: Added Python 3.11 (LTS) + FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
