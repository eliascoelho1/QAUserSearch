# Tasks: Fundação do Projeto QAUserSearch

**Input**: Design documents from `/specs/001-project-foundation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Não explicitamente solicitados na especificação. Tasks de teste NÃO incluídas.

**Organization**: Tasks agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story associada (US1, US2, US3, US4)
- Caminhos de arquivos exatos incluídos nas descrições

## Path Conventions

- **Single project**: `src/`, `tests/` na raiz do repositório
- Estrutura conforme plan.md: `src/`, `tests/`, `.github/`, `docker/`, `docs/`
- **Package Manager**: uv (gerenciador de pacotes Python moderno e rápido)

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Inicialização do projeto e estrutura básica com uv

- [x] T001 Inicializar projeto com `uv init` e configurar `pyproject.toml` com dependências
- [x] T002 Criar arquivo `.env.example` com template de variáveis de ambiente
- [x] T003 [P] Criar arquivo `.gitignore` com padrões Python, venv, .env, __pycache__, .venv
- [x] T004 [P] Criar estrutura base de diretórios: `src/`, `tests/`, `docker/`, `docs/`
- [x] T005 [P] Criar arquivos `__init__.py` em todos os módulos Python
- [x] T006 Instalar dependências com `uv add fastapi pydantic sqlalchemy alembic uvicorn structlog python-dotenv`
- [x] T007 Instalar dev dependencies com `uv add --dev pytest pytest-cov pytest-asyncio httpx ruff mypy`

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes)

**Purpose**: Infraestrutura core que DEVE estar completa antes de qualquer user story

**⚠️ CRÍTICO**: Nenhum trabalho de user story pode começar até esta fase estar completa

- [x] T008 Implementar `src/config.py` com Pydantic Settings para configurações tipadas
- [x] T009 Implementar enums em `src/schemas/enums.py` (HealthStatus, CheckStatus, Environment, LogLevel)
- [x] T010 [P] Implementar logging estruturado em `src/core/logging.py` com structlog
- [x] T011 [P] Implementar conexão de banco em `src/core/database.py` com SQLAlchemy async
- [x] T012 Criar `src/main.py` com FastAPI app básico (sem rotas)
- [x] T013 Criar `tests/conftest.py` com fixtures básicas para pytest

**Checkpoint**: Fundação pronta - implementação de user stories pode começar em paralelo

---

## Phase 3: User Story 1 - Configuração do Ambiente de Desenvolvimento (Priority: P1) 🎯 MVP

**Goal**: Permitir que desenvolvedores configurem o ambiente e executem a aplicação em <15 minutos

**Independent Test**: Clonar repo, executar `uv sync`, executar aplicação localmente

### Implementation for User Story 1

- [x] T014 [P] [US1] Criar `docker/Dockerfile` com multi-stage build para Python 3.11 + uv
- [x] T015 [P] [US1] Criar `docker/docker-compose.yml` com serviços app e db (PostgreSQL)
- [x] T016 [US1] Atualizar `src/main.py` com lifespan handler para startup/shutdown
- [x] T017 [US1] Implementar hot-reload no docker-compose para desenvolvimento
- [x] T018 [US1] Criar script `scripts/setup.sh` para setup automatizado do ambiente com uv
- [x] T019 [US1] Atualizar `README.md` com instruções de instalação usando uv

**Checkpoint**: User Story 1 completa - ambiente de desenvolvimento funcional e documentado

---

## Phase 4: User Story 2 - Estrutura Base da Aplicação (Priority: P1)

**Goal**: Estrutura de projeto bem definida com health check funcional

**Independent Test**: Executar aplicação, acessar /health e receber status JSON válido

### Implementation for User Story 2

- [x] T020 [P] [US2] Criar schemas Pydantic em `src/schemas/health.py` (HealthCheckResponse, DependencyCheck, etc)
- [x] T021 [P] [US2] Criar schema `src/schemas/root.py` (RootResponse)
- [x] T022 [US2] Implementar service `src/services/health_service.py` com lógica de health check
- [x] T023 [US2] Criar router `src/api/v1/health.py` com endpoints /health, /health/live, /health/ready
- [x] T024 [US2] Criar router `src/api/v1/root.py` com endpoint / (root)
- [x] T025 [US2] Registrar routers em `src/main.py` e configurar OpenAPI/Swagger
- [x] T026 [US2] Implementar verificação de dependências (database checks) em health_service

**Checkpoint**: User Story 2 completa - estrutura base com health check funcional

---

## Phase 5: User Story 3 - Configuração de Integração Contínua (Priority: P2)

**Goal**: Pipeline de CI que executa lint, typecheck e testes automaticamente

**Independent Test**: Criar PR e verificar que checks são executados e reportados

### Implementation for User Story 3

- [x] T027 [P] [US3] Criar `.github/workflows/ci.yml` com jobs: lint, typecheck, test, build (usando uv)
- [x] T028 [P] [US3] Configurar Ruff em `pyproject.toml` section [tool.ruff]
- [x] T029 [P] [US3] Configurar Black em `pyproject.toml` section [tool.black]
- [x] T030 [P] [US3] Configurar mypy em `pyproject.toml` section [tool.mypy] com strict=true
- [x] T031 [US3] Configurar pytest em `pyproject.toml` section [tool.pytest.ini_options]
- [x] T032 [US3] Criar `.github/hooks/hooks.json` com configuração de Copilot hooks
- [x] T033 [P] [US3] Criar `.github/hooks/scripts/validate-python.sh` para lint + typecheck
- [x] T034 [P] [US3] Criar `.github/hooks/scripts/run-tests.sh` para testes unitários
- [x] T035 [US3] Criar `.github/hooks/scripts/lib/common.sh` com funções compartilhadas

**Checkpoint**: User Story 3 completa - CI pipeline funcional com validações automáticas

---

## Phase 6: User Story 4 - Documentação Técnica Inicial (Priority: P2)

**Goal**: Documentação técnica básica para onboarding e referência

**Independent Test**: Novo desenvolvedor consegue entender a arquitetura lendo docs/

### Implementation for User Story 4

- [x] T036 [P] [US4] Criar `docs/architecture.md` com diagramas e descrição das camadas
- [x] T037 [P] [US4] Criar `.github/agents/copilot-instructions.md` com contexto do agente
- [x] T038 [US4] Atualizar `README.md` com seção de arquitetura e links para docs/
- [x] T039 [US4] Documentar estrutura de diretórios em `docs/architecture.md`

**Checkpoint**: User Story 4 completa - documentação técnica básica disponível

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [x] T040 Validar conformidade com quickstart.md (executar todos os comandos documentados com uv)
- [x] T041 [P] Adicionar logging nas rotas de health check
- [x] T042 [P] Garantir que todos os arquivos Python passam em ruff + mypy
- [x] T043 Criar testes básicos em `tests/unit/test_config.py` para validar configuração
- [x] T044 Criar testes básicos em `tests/integration/test_health.py` para health endpoints
- [x] T045 Executar CI pipeline completo e corrigir eventuais falhas

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as user stories
- **User Stories (Phase 3-6)**: Todas dependem de Foundational
  - US1 e US2 são ambas P1 - priorizar US1 primeiro (ambiente dev)
  - US3 e US4 são ambas P2 - podem começar após US2
- **Polish (Phase 7)**: Depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **User Story 1 (P1)**: Pode iniciar após Foundational (Phase 2)
- **User Story 2 (P1)**: Pode iniciar após Foundational (Phase 2) - independente de US1
- **User Story 3 (P2)**: Pode iniciar após Foundational (Phase 2) - independente de US1/US2
- **User Story 4 (P2)**: Pode iniciar após Foundational (Phase 2) - independente de outras

### Within Each User Story

- Schemas antes de services
- Services antes de routers/endpoints
- Core implementation antes de integração
- Story completa antes de mover para próxima prioridade

### Parallel Opportunities

- T003, T004, T005 podem rodar em paralelo (Setup)
- T010, T011 podem rodar em paralelo (Foundational)
- T014, T015 podem rodar em paralelo (US1)
- T020, T021 podem rodar em paralelo (US2)
- T027, T028, T029, T030 podem rodar em paralelo (US3)
- T033, T034 podem rodar em paralelo (US3)
- T036, T037 podem rodar em paralelo (US4)

---

## Parallel Example: User Story 2

```bash
# Launch schemas em paralelo:
Task: "Criar schemas Pydantic em src/schemas/health.py"
Task: "Criar schema src/schemas/root.py"

# Depois, sequencialmente:
Task: "Implementar service src/services/health_service.py"
Task: "Criar router src/api/v1/health.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (com uv)
2. Complete Phase 2: Foundational (CRÍTICO - bloqueia todas as stories)
3. Complete Phase 3: User Story 1 (ambiente dev)
4. Complete Phase 4: User Story 2 (health check)
5. **STOP and VALIDATE**: Testar ambiente + health check independentemente
6. Deploy/demo se pronto

### Incremental Delivery

1. Complete Setup + Foundational → Fundação pronta
2. Add User Story 1 → Test independently → Deploy/Demo (ambiente dev!)
3. Add User Story 2 → Test independently → Deploy/Demo (health check funcional!)
4. Add User Story 3 → Test independently → Deploy/Demo (CI configurado!)
5. Add User Story 4 → Test independently → Deploy/Demo (documentação completa!)

### Parallel Team Strategy

Com múltiplos desenvolvedores:

1. Team completa Setup + Foundational juntos
2. Uma vez Foundational completo:
   - Developer A: User Story 1 + 2 (P1s)
   - Developer B: User Story 3 (P2 - CI)
   - Developer C: User Story 4 (P2 - Docs)
3. Stories completam e integram independentemente

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica
- Cada user story deve ser completável e testável independentemente
- Usar `uv sync` para instalar dependências (substitui pip install)
- Usar `uv run pytest` para executar testes
- Usar `uv run ruff check` para linting
- Commit após cada task ou grupo lógico
- Pare em qualquer checkpoint para validar story independentemente
