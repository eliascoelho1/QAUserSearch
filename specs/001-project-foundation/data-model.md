# Data Model: Fundação do Projeto QAUserSearch

**Date**: 2026-01-28  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Contexto

Este documento define o modelo de dados inicial para a fundação do projeto. Como esta é uma feature de infraestrutura, o modelo é mínimo e focado em configuração e monitoramento.

---

## Entidades

### 1. HealthCheck (Transiente)

Não persistida - representa o estado atual da aplicação.

```
HealthCheck
├── status: HealthStatus (enum: healthy, degraded, unhealthy)
├── timestamp: datetime
├── version: string
├── uptime_seconds: int
└── checks: DependencyCheck[]
    ├── name: string
    ├── status: CheckStatus (enum: ok, warning, error)
    ├── latency_ms: int?
    └── message: string?
```

**Regras de Validação**:
- `status` é `healthy` apenas se TODOS os checks são `ok`
- `status` é `degraded` se algum check é `warning`
- `status` é `unhealthy` se algum check é `error`

---

### 2. AppConfig (Ambiente)

Configurações carregadas do ambiente, não persistidas em banco.

```
AppConfig
├── app_name: string = "qausersearch"
├── environment: Environment (enum: development, staging, production)
├── debug: bool = false
├── log_level: LogLevel (enum: DEBUG, INFO, WARNING, ERROR)
├── database_url: string (secret)
├── qa_database_url: string (secret)
├── allowed_hosts: string[] = ["*"]
├── cors_origins: string[] = []
└── metrics_enabled: bool = true
```

**Regras de Validação**:
- `database_url` é obrigatório
- `debug` DEVE ser `false` em `production`
- `log_level` DEVE ser `INFO` ou superior em `production`

---

## Diagrama de Relacionamentos

```
┌─────────────────────────────────────────────────────────────┐
│                      QAUserSearch App                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐     ┌─────────────────────────────────┐   │
│   │  AppConfig  │────▶│         Health Check             │   │
│   │  (env vars) │     │  (runtime state, não persistido) │   │
│   └─────────────┘     └─────────────────────────────────┘   │
│          │                          │                        │
│          │                          ▼                        │
│          │            ┌─────────────────────────────────┐   │
│          │            │      DependencyCheck[]          │   │
│          │            │  - App Database (PostgreSQL)    │   │
│          │            │  - QA Database (externa)        │   │
│          │            └─────────────────────────────────┘   │
│          │                                                   │
│          ▼                                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                  PostgreSQL (App)                    │   │
│   │  [vazio nesta feature - schema futuro em v1.0]      │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Enums

### HealthStatus
```python
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
```

### CheckStatus
```python
class CheckStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
```

### Environment
```python
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
```

### LogLevel
```python
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
```

---

## Schemas Pydantic (Preview)

```python
from pydantic import BaseModel
from datetime import datetime

class DependencyCheckResponse(BaseModel):
    name: str
    status: CheckStatus
    latency_ms: int | None = None
    message: str | None = None

class HealthCheckResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    version: str
    uptime_seconds: int
    checks: list[DependencyCheckResponse]
```

---

## Notas de Evolução

Esta fundação prepara o terreno para as seguintes entidades futuras (v1.0+):

| Feature | Entidades Previstas |
|---------|-------------------|
| Busca de usuários | User, SearchQuery, SearchResult |
| Autenticação | AuthSession, UserCredential |
| Queries dinâmicas | QueryTemplate, GeneratedQuery |
| Filtros rápidos (v2.0) | QuickFilter, FilterCategory |
| Histórico (v2.1) | SearchHistory |

O schema de banco será criado via Alembic migrations conforme features forem implementadas.
