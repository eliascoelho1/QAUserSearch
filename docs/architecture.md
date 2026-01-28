# Architecture: QAUserSearch

## Overview

QAUserSearch é uma API REST para busca de massas de usuários em ambiente de QA. A aplicação segue uma arquitetura em camadas com separação clara de responsabilidades.

## Stack Tecnológica

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| **Runtime** | Python | 3.11+ |
| **Framework** | FastAPI | 0.115+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Validação** | Pydantic | 2.10+ |
| **Database** | PostgreSQL | 15+ |
| **Logging** | structlog | 24.4+ |
| **Testing** | pytest | 8.3+ |

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API Layer (v1/)                         │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │  │
│  │  │  root   │  │  health │  │  users  │  │ queries │      │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘      │  │
│  └───────│────────────│────────────│────────────│───────────┘  │
│          │            │            │            │               │
│  ┌───────▼────────────▼────────────▼────────────▼───────────┐  │
│  │                   Service Layer                           │  │
│  │  ┌─────────────────┐  ┌─────────────────┐               │  │
│  │  │  health_service │  │  user_service   │  ...          │  │
│  │  └────────┬────────┘  └────────┬────────┘               │  │
│  └───────────│─────────────────────│────────────────────────┘  │
│              │                     │                            │
│  ┌───────────▼─────────────────────▼────────────────────────┐  │
│  │                    Core Layer                             │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ database │  │  logging │  │  config  │               │  │
│  │  └────┬─────┘  └──────────┘  └──────────┘               │  │
│  └───────│──────────────────────────────────────────────────┘  │
└──────────│──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL                                 │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │   App Database     │  │   QA Database      │                │
│  │   (read/write)     │  │   (read-only)      │                │
│  └────────────────────┘  └────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

## Camadas

### 1. API Layer (`src/api/`)

Responsável por:
- Definição de endpoints REST
- Validação de entrada (via Pydantic)
- Serialização de resposta
- Documentação OpenAPI

**Padrões**:
- Um arquivo por recurso (ex: `health.py`, `users.py`)
- Routers agrupados por versão (`v1/`)
- Schemas separados para request/response

### 2. Service Layer (`src/services/`)

Responsável por:
- Lógica de negócio
- Orquestração de operações
- Validações de domínio

**Padrões**:
- Funções puras quando possível
- Injeção de dependências
- Sem acesso direto a frameworks HTTP

### 3. Core Layer (`src/core/`)

Responsável por:
- Infraestrutura cross-cutting
- Conexões de banco de dados
- Logging estruturado
- Configuração centralizada

### 4. Models Layer (`src/models/`)

Responsável por:
- Definição de entidades SQLAlchemy
- Mapeamento objeto-relacional
- Migrations (via Alembic)

### 5. Schemas Layer (`src/schemas/`)

Responsável por:
- Schemas Pydantic para validação
- DTOs (Data Transfer Objects)
- Enums e tipos compartilhados

## Fluxo de Requisição

```
Request → Router → Service → Database → Service → Router → Response
           │         │                      │         │
           └── Validates ──────────────────────── Serializes
```

## Estrutura de Diretórios

```
src/
├── __init__.py
├── main.py              # Entry point, app factory
├── config.py            # Pydantic Settings
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── health.py    # Health endpoints
│       └── root.py      # Root endpoint
├── core/
│   ├── __init__.py
│   ├── database.py      # DB connection manager
│   └── logging.py       # structlog setup
├── models/
│   └── __init__.py      # SQLAlchemy models
├── schemas/
│   ├── __init__.py
│   ├── enums.py         # Shared enums
│   ├── health.py        # Health schemas
│   └── root.py          # Root schemas
└── services/
    ├── __init__.py
    └── health_service.py
```

## Decisões de Design

### 1. Async por Padrão

Toda a stack usa async/await para máxima performance:
- SQLAlchemy async
- asyncpg como driver
- ASGI server (uvicorn)

### 2. Configuração Tipada

Pydantic Settings com validação em startup:
- Falha rápida se config inválida
- Documentação automática via tipos
- Suporte a múltiplos ambientes

### 3. Logging Estruturado

structlog para logs JSON parseáveis:
- Correlação por request_id
- Métricas de latência automáticas
- Integração com sistemas de observabilidade

### 4. Type Safety

mypy em modo strict:
- Todas as funções tipadas
- Nenhum Any implícito
- Validação em CI

## Extensibilidade

Para adicionar novos recursos:

1. **Novo Endpoint**:
   - Criar router em `src/api/v1/`
   - Registrar em `src/main.py`

2. **Nova Entidade**:
   - Criar model em `src/models/`
   - Criar schema em `src/schemas/`
   - Criar migration com Alembic

3. **Novo Serviço**:
   - Criar em `src/services/`
   - Injetar via Depends() nos routers

## Performance

- Pool de conexões: 5-15 conexões
- Timeout de query: 30s
- Health check: <100ms
- Target p95: <2s para buscas simples
