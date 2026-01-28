# QAUserSearch Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-28

## Project Context

QAUserSearch is a Python FastAPI application for searching user data in QA environments. It provides a REST API for QA teams to find test user records across multiple databases.

## Active Technologies

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

- 001-project-foundation: Added Python 3.11 (LTS) + FastAPI, Pydantic, SQLAlchemy, Alembic, uvicorn

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
