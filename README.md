# QAUserSearch

API para busca de massas de usuários em ambiente de QA.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker and Docker Compose

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd QAUserSearch

# Run the setup script (requires Docker)
./scripts/setup.sh

# Or without Docker (local setup only)
./scripts/setup-local.sh
```

Or manually:

```bash
# Copy environment file
cp .env.example .env

# Install dependencies
uv sync --all-extras

# Start the database
docker compose -f docker/docker-compose.yml up -d db

# Run the application
uv run uvicorn src.main:app --reload
```

### Access

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Development

### Running Tests

```bash
uv run pytest                     # All tests
uv run pytest tests/unit/         # Unit tests only
uv run pytest --cov=src           # With coverage
```

### Catalog Extraction CLI

Extract schema metadata from external data sources:

```bash
# Extract from a single source
uv run qa-catalog extract credit invoice --sample-size 500

# Extract from all known sources
uv run qa-catalog extract-all

# List available known sources
uv run qa-catalog list-known
```

### Code Quality

```bash
uv run ruff check src/ tests/     # Lint
uv run ruff check src/ --fix      # Auto-fix
uv run mypy src/                  # Type check
uv run black src/ tests/          # Format
```

### Docker

```bash
# Start all services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f app

# Stop services
docker compose -f docker/docker-compose.yml down
```

## Project Structure

```
├── src/
│   ├── api/v1/          # API endpoints
│   ├── cli/             # CLI commands
│   ├── core/            # Cross-cutting concerns (logging, database)
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── config.py        # Application configuration
│   └── main.py          # FastAPI application entry
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── contract/        # Contract tests
├── docker/              # Docker configuration
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

See `.env.example` for all available options.

## License

Proprietary
