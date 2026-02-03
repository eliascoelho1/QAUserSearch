# AGENTS.md - Coding Agent Guidelines for QAUserSearch

FastAPI REST API for QA user test data search. Uses Python 3.11+, FastAPI, SQLAlchemy 2.0 async, Pydantic 2.x, structlog, and **uv** as package manager.

> **📐 Architecture Reference**: For detailed architecture diagrams, layer responsibilities, and design decisions, see [docs/architecture.md](../../docs/architecture.md).

## Build/Lint/Test Commands

### Package Management
```bash
uv sync --all-extras          # Install all dependencies
uv add <package>              # Add dependency
uv add --dev <package>        # Add dev dependency
```

### Running the Application
```bash
uv run uvicorn src.main:app --reload    # Development with hot reload
```

### Running Tests
```bash
uv run pytest                           # All tests
uv run pytest tests/unit/               # Unit tests only
uv run pytest tests/integration/        # Integration tests only
uv run pytest -k "test_name"            # Single test by name
uv run pytest tests/unit/test_extractor.py::TestTypeInferrer::test_infer_string  # Specific test
uv run pytest --cov=src                 # With coverage
```

### Linting and Formatting
```bash
uv run ruff check src/ tests/           # Lint
uv run ruff check src/ tests/ --fix     # Auto-fix lint issues
uv run black src/ tests/                # Format
uv run mypy src/ tests/                 # Type check (strict)
```

### Validation Scripts

The project includes validation scripts in `scripts/` that can be run manually or are triggered automatically by agent hooks.

#### Python File Validation
```bash
./scripts/validate-python.sh <file.py>              # Validate single file (blocking)
./scripts/validate-python.sh src/*.py               # Validate multiple files
./scripts/validate-python.sh --no-block <file.py>   # Non-blocking (background)
./scripts/validate-python.sh --block <file.py>      # Blocking (default)
```
Runs Black (formatting), Ruff (linting), and mypy (type checking) on Python files.

#### Test Validation
```bash
./scripts/validate-tests.sh                         # Run unit tests (blocking)
./scripts/validate-tests.sh /path/to/project        # Run in specific directory
./scripts/validate-tests.sh --no-block              # Non-blocking (background)
./scripts/validate-tests.sh --block                 # Blocking (default)
```
Runs `pytest tests/unit/` with verbose output.

### Database & Docker
```bash
uv run alembic upgrade head             # Apply migrations
uv run alembic revision -m "desc"       # Create migration
docker compose -f docker/docker-compose.yml up -d db   # Start database
```

## Zero Error Policy (LSP)

**CRITICAL**: This project follows a strict **zero errors policy**.

- **Always check LSP diagnostics** after any code change (basedpyright is configured in `opencode.json`)
- **No unresolved errors allowed** - Code is not complete until all LSP errors are fixed
- **Fix before committing** - All issues must be resolved before creating commits

## Code Style Guidelines

### Imports
- Order: stdlib, third-party, local (ruff isort enforced)
- Absolute imports: `from src.schemas.enums import InferredType`
- Type-only imports in `TYPE_CHECKING` block

### Formatting
- Line length: 88 chars (Black), double quotes, trailing commas, 4-space indent

### Type Annotations (mypy strict + extra checks)
- All functions must have type hints (including tests)
- Modern syntax: `list[str]`, `dict[str, Any]`, `X | None`
- Use `Annotated` for FastAPI dependencies
- **No implicit Any**: Always specify generic type parameters (`dict[str, Any]` not `dict`)
- **No untyped decorators**: Custom decorators must be fully typed
- Tests require full type annotations (same rules as src/)

### Naming Conventions
- Classes: `PascalCase` | Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE` | Private: `_underscore` prefix

### Docstrings (Google-style)
```python
def method(self, db_name: str) -> dict[str, Any]:
    """Short description.

    Args:
        db_name: External database name.

    Returns:
        Dictionary with results.
    """
```

### Error Handling
- Use `HTTPException` for API errors
- Log errors with structlog: `logger.error("msg", key=value)`

### Pydantic Schemas
```python
class SourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    db_name: str = Field(..., description="Database name")
```

### SQLAlchemy Models
```python
class ExternalSource(Base):
    __tablename__ = "external_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    db_name: Mapped[str] = mapped_column(String(100), index=True)
```

### FastAPI Endpoints
```python
@router.get("/sources/{source_id}")
async def get_source(
    source_id: int,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> SourceDetailResponse:
```

## Project Structure

```
src/
├── api/v1/          # API routers
├── core/            # Database, logging
├── models/          # SQLAlchemy models
├── repositories/    # Data access layer
├── schemas/         # Pydantic schemas
├── services/        # Business logic
├── config.py        # Settings
└── main.py          # App entry point

tests/
├── unit/            # No external deps
├── integration/     # Requires database
├── contract/        # API contracts
└── conftest.py      # Shared fixtures
```

## Testing Patterns

- Test classes: `class TestTypeName:`
- Test methods: `def test_behavior(self) -> None:` (return type required)
- Async tests auto-detected (asyncio_mode = "auto")
- Use `AsyncClient` with `ASGITransport` for API tests
- **All test functions must be fully typed** (same mypy rules as production code)

## Environment Variables

See `.env.example`:
- `DATABASE_URL`: PostgreSQL async connection (`postgresql+asyncpg://...`)
- `ENVIRONMENT`: development | staging | production
- `DEBUG`: false in production
- `LOG_LEVEL`: DEBUG | INFO | WARNING | ERROR
- `DATA_SOURCE_ENVIRONMENT`: MOCK | PROD

## Common Patterns

### Dependency Injection
```python
async def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CatalogService:
    return CatalogService(session=session)
```

### Logging
```python
import structlog
logger = structlog.get_logger(__name__)
log = logger.bind(db_name=db_name)
log.info("Starting extraction")
```

### Enums (inherit str for JSON serialization)
```python
class InferredType(str, Enum):
    STRING = "string"
```

## Active Technologies
- Python 3.11 + FastAPI, CrewAI (1.9.3), Pydantic, SQLAlchemy async (001-llm-query-interpreter)
- PostgreSQL (catálogo de metadados), MongoDB (dados de QA externos) (001-llm-query-interpreter)

## Recent Changes
- 001-llm-query-interpreter: Added Python 3.11 + FastAPI, CrewAI (1.9.3), Pydantic, SQLAlchemy async
