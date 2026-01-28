# Research: Fundação do Projeto QAUserSearch

**Date**: 2026-01-28  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Contexto da Pesquisa

Esta pesquisa consolida as decisões técnicas para a fundação do projeto QAUserSearch, uma aplicação para busca de massas de usuários em ambiente de QA.

---

## 1. Stack Tecnológica

### Decision: Python 3.11 + FastAPI

**Rationale**:
- Python 3.11 oferece melhorias de performance significativas (~25% mais rápido que 3.10)
- FastAPI é o framework mais adequado para APIs modernas com Python:
  - Performance comparável a Node.js e Go (graças ao Starlette + uvicorn)
  - Validação automática via Pydantic
  - Documentação OpenAPI gerada automaticamente
  - Excelente suporte a async/await
- Ideal para futuras integrações com AI/LLM (geração de queries dinâmicas)

**Alternatives Considered**:
- **Django REST Framework**: Mais maduro, mas overhead desnecessário para API simples
- **Flask**: Menor curva de aprendizado, mas sem validação nativa e async limitado
- **Node.js + Express**: Boa performance, mas equipe tem mais experiência com Python

---

## 2. ORM e Migrations

### Decision: SQLAlchemy 2.0 + Alembic

**Rationale**:
- SQLAlchemy 2.0 com suporte nativo a async
- Alembic para versionamento de schema (migrations)
- Padrão de mercado para Python, excelente documentação
- Permite queries raw quando necessário para performance

**Alternatives Considered**:
- **Tortoise ORM**: Async-first mas menos maduro
- **Prisma Python**: Interessante mas comunidade menor
- **Raw SQL**: Máxima performance mas difícil manutenção

---

## 3. Configuração e Variáveis de Ambiente

### Decision: Pydantic Settings + python-dotenv

**Rationale**:
- Pydantic Settings fornece validação tipada de configurações
- Integração nativa com FastAPI
- Suporte a múltiplos ambientes (.env, .env.local, .env.test)
- Documentação automática de variáveis obrigatórias

**Configuration Strategy**:
```
.env.example    # Template commitado, sem valores reais
.env            # Local (gitignore)
.env.test       # Testes (gitignore)
```

---

## 4. Logging Estruturado

### Decision: structlog

**Rationale**:
- Logs JSON estruturados, ideais para agregação (ELK, Datadog)
- Contexto automático (request_id, user_id)
- Performance superior a logging padrão
- Atende requisito da Constitution (IV. Performance - logs estruturados)

**Alternatives Considered**:
- **loguru**: Mais simples mas menos estruturado
- **logging stdlib**: Muito básico para produção

---

## 5. Testes e Cobertura

### Decision: pytest + pytest-cov + pytest-asyncio + httpx

**Rationale**:
- pytest é o padrão de facto para Python
- pytest-asyncio para testar código async
- httpx como client HTTP para testes de integração FastAPI
- pytest-cov para relatório de cobertura (requisito Constitution: ≥80%)

**Test Structure** (conforme Constitution II. TDD):
```
tests/
├── unit/           # Testes isolados, mocks
├── integration/    # Testes com DB real
└── contract/       # Testes de API contracts
```

---

## 6. Linting e Formatação

### Decision: Ruff + Black + isort

**Rationale**:
- Ruff: Linter extremamente rápido (100x mais rápido que flake8)
- Black: Formatador opinionado, zero configuração
- isort: Ordenação de imports (integrado no Ruff)
- Atende requisito Constitution (I. Qualidade - formatadores obrigatórios)

**Configuration**: pyproject.toml centraliza todas as configs

---

## 6.1. Tipagem Forte (Strong Typing)

### Decision: mypy --strict + tipos explícitos obrigatórios

**Rationale**:
- Python é dinamicamente tipado por padrão, mas suporta type hints desde 3.5
- mypy em modo strict garante:
  - Todas as funções DEVEM ter type annotations
  - Todas as variáveis DEVEM ter tipos inferidos ou explícitos
  - Nenhum `Any` implícito permitido
  - Imports tipados obrigatórios
- Pydantic v2 é 100% compatível com mypy
- SQLAlchemy 2.0 tem suporte nativo a tipagem
- Detecta bugs em tempo de desenvolvimento, não em runtime

**Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]

[tool.mypy.overrides]
module = ["tests.*"]
disallow_untyped_defs = false  # Relaxado apenas para testes
```

**Regras de Implementação**:
1. **Funções**: Todas DEVEM ter return type e parameter types
   ```python
   def get_user(user_id: int) -> User | None:
   ```
2. **Classes**: Atributos DEVEM ter type annotations
   ```python
   class Config:
       debug: bool = False
       timeout_seconds: int = 30
   ```
3. **Containers**: Usar tipos genéricos explícitos
   ```python
   users: list[User] = []
   cache: dict[str, Any] = {}  # Any explícito quando necessário
   ```
4. **Optional**: Usar `X | None` (Python 3.10+ syntax)
   ```python
   name: str | None = None
   ```

**Alternatives Considered**:
- **pyright**: Mais rápido, mas menos integração com ecossistema Python
- **pytype (Google)**: Menos popular, comunidade menor
- **Sem type checker**: Não aceitável para projeto de qualidade

**CI Integration**:
- Job `typecheck` no GitHub Actions
- Bloqueante: zero erros de tipo tolerados
- Executado antes dos testes

---

## 7. CI/CD

### Decision: GitHub Actions

**Rationale**:
- Já disponível no repositório (.github/ existe)
- Integração nativa com PRs
- Boa disponibilidade de actions para Python

**Pipeline Jobs**:
1. `lint` - Ruff + format check
2. `typecheck` - mypy --strict (bloqueante)
3. `test` - pytest com cobertura
4. `build` - Docker image build
5. `deploy-staging` - Auto deploy após merge em develop

---

## 8. Containerização

### Decision: Docker + Docker Compose

**Rationale**:
- Ambiente consistente local ↔ produção
- Facilita onboarding (objetivo: <15 min setup)
- PostgreSQL local via docker-compose

**Images**:
- Base: `python:3.11-slim`
- Multi-stage build para imagem final pequena

---

## 9. Commit Conventions

### Decision: Conventional Commits + commitlint

**Rationale**:
- Padrão estabelecido na Constitution
- Permite changelog automático
- Facilita navegação no histórico

**Tipos permitidos**: feat, fix, docs, style, refactor, test, chore

---

## 10. Health Check e Observabilidade

### Decision: Endpoint /health + Prometheus metrics

**Rationale**:
- Health check é requisito funcional (FR-001)
- Prometheus metrics atende Constitution (IV. Performance - métricas de latência)
- Padrão para Kubernetes/container orchestration

**Health Check Response**:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "dependencies": ["qa_db: ok"]
  },
  "version": "1.0.0"
}
```

---

## Resumo de Decisões

| Área | Decisão | Justificativa Principal |
|------|---------|------------------------|
| Framework | FastAPI | Performance + validação + OpenAPI |
| ORM | SQLAlchemy 2.0 | Async + maturidade + tipagem |
| Config | Pydantic Settings | Tipagem + validação |
| Type Check | mypy --strict | Tipagem forte obrigatória |
| Logging | structlog | Estruturado + performance |
| Testes | pytest stack | Padrão + cobertura |
| Lint | Ruff + Black | Velocidade + consistência |
| CI/CD | GitHub Actions | Integração nativa |
| Container | Docker | Consistência + onboarding |
