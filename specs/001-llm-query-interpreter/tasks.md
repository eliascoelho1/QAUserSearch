# Tasks: Interpretador LLM para Geração de Queries

**Input**: Design documents from `/specs/001-llm-query-interpreter/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Incluídos conforme plan.md indica cobertura ≥80% e ciclo TDD obrigatório.

**Organization**: Tasks organizadas por user story para implementação e testes independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual user story pertence (US1, US2, US3)
- Caminhos exatos incluídos nas descrições

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Inicialização do projeto e estrutura básica

- [X] T001 Adicionar dependências openai>=1.0.0 e crewai>=0.80.0 em pyproject.toml
- [X] T002 Executar `uv sync` para instalar novas dependências
- [X] T003 [P] Criar estrutura de diretórios src/agents/config/
- [X] T004 [P] Criar estrutura de diretórios src/api/v1/websocket/
- [X] T005 [P] Criar estrutura de diretórios src/services/llm/
- [X] T006 [P] Criar estrutura de diretórios src/services/query/
- [X] T007 [P] Criar estrutura de diretórios src/services/audit/
- [X] T008 [P] Criar estrutura de diretórios src/models/query/
- [X] T009 [P] Criar estrutura de diretórios src/schemas/query/
- [X] T010 [P] Criar estrutura de diretórios src/core/security/
- [X] T011 Adicionar variáveis OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, OPENAI_MAX_RETRIES em .env.example

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes)

**Purpose**: Infraestrutura core que DEVE estar completa antes de qualquer user story

**⚠️ CRÍTICO**: Nenhuma user story pode começar até esta fase estar completa

- [X] T012 [P] Criar enum FilterOperator em src/models/query/enums.py
- [X] T013 [P] Criar enum InterpretationStatus em src/models/query/enums.py
- [X] T014 [P] Criar modelo Entity em src/models/query/interpretation.py
- [X] T015 [P] Criar modelo Filter em src/models/query/interpretation.py
- [X] T016 Criar modelo PromptInterpretation em src/models/query/interpretation.py (depende T014, T015)
- [X] T017 [P] Criar modelo GeneratedQuery em src/models/query/generated_query.py
- [X] T018 [P] Criar modelo QueryResult em src/models/query/query_result.py
- [X] T019 [P] Criar modelo AuditLog em src/models/query/audit_log.py
- [X] T020 Criar migration Alembic para tabela audit_log com índices em alembic/versions/
- [X] T021 [P] Criar schema InterpretPromptRequest em src/schemas/query/request.py
- [X] T022 [P] Criar schema ExecuteQueryRequest em src/schemas/query/request.py
- [X] T023 [P] Criar schema InterpretationResponse em src/schemas/query/response.py
- [X] T024 [P] Criar schema QueryResponse em src/schemas/query/response.py
- [X] T025 [P] Criar schema QueryResultResponse em src/schemas/query/response.py
- [X] T026 [P] Criar schema ErrorResponse em src/schemas/query/response.py
- [X] T027 [P] Criar schemas WSMessage, WSStatusMessage, WSChunkMessage, WSInterpretationMessage, WSErrorMessage em src/schemas/query/websocket.py
- [X] T028 Criar SQL blacklist FORBIDDEN_COMMANDS com regex em src/core/security/sql_blacklist.py
- [X] T029 Implementar função validate_query() em src/core/security/sql_blacklist.py
- [X] T030 [P] Criar teste unitário para validate_query() em tests/unit/core/test_sql_blacklist.py
- [X] T031 Criar ConnectionManager para WebSocket em src/api/v1/websocket/connection_manager.py
- [X] T032 [P] Criar teste unitário para ConnectionManager em tests/unit/api/test_connection_manager.py
- [X] T033 Criar OpenAIClient com retry e streaming em src/services/llm/openai_client.py
- [X] T034 [P] Criar teste unitário para OpenAIClient (mock) em tests/unit/services/test_openai_client.py
- [X] T035 Criar CatalogContext para integração com catálogo existente em src/services/query/catalog_context.py
- [X] T036 [P] Criar teste unitário para CatalogContext em tests/unit/services/test_catalog_context.py
- [X] T037 Criar agents.yaml com definições de interpreter, validator, refiner em src/agents/config/agents.yaml
- [X] T038 Criar tasks.yaml com definições de tasks do crew em src/agents/config/tasks.yaml

**Checkpoint**: Foundation ready - implementação das user stories pode começar

---

## Phase 3: User Story 1 - Busca por Cenário em Linguagem Natural (Priority: P1) 🎯 MVP

**Goal**: Testador QA descreve em linguagem natural e sistema gera query que retorna dados correspondentes

**Independent Test**: Fornecer prompt em linguagem natural e verificar se retorna dados relevantes

### Tests for User Story 1

> **NOTE**: Escrever testes PRIMEIRO, garantir que FALHAM antes da implementação

- [X] T039 [P] [US1] Criar teste de contrato para POST /query/interpret em tests/contract/test_interpret_endpoint.py
- [X] T040 [P] [US1] Criar teste de contrato para POST /query/{id}/execute em tests/contract/test_execute_endpoint.py
- [X] T041 [P] [US1] Criar teste de integração para fluxo prompt → query → resultado em tests/integration/test_query_flow.py

### Implementation for User Story 1

- [X] T042 [US1] Criar agente PromptInterpreterAgent em src/agents/prompt_interpreter.py
- [X] T043 [US1] Criar agente QueryValidatorAgent em src/agents/query_validator.py
- [X] T044 [US1] Criar agente QueryRefinerAgent em src/agents/query_refiner.py
- [X] T045 [US1] Criar InterpreterCrew com processo sequencial em src/agents/interpreter_crew.py
- [X] T046 [P] [US1] Criar teste unitário para InterpreterCrew em tests/unit/agents/test_interpreter_crew.py
- [X] T047 [US1] Criar InterpreterService (orquestra crew + catálogo) em src/services/query/interpreter_service.py
- [X] T048 [P] [US1] Criar teste unitário para InterpreterService em tests/unit/services/test_interpreter_service.py
- [X] T049 [US1] Criar ValidatorService (validação de segurança SQL) em src/services/query/validator_service.py
- [X] T050 [P] [US1] Criar teste unitário para ValidatorService em tests/unit/services/test_validator_service.py
- [X] T051 [US1] Criar ExecutorService (executa query no banco QA) em src/services/query/executor_service.py
- [X] T052 [P] [US1] Criar teste unitário para ExecutorService em tests/unit/services/test_executor_service.py
- [X] T053 [US1] Criar AuditService (log de queries bloqueadas) em src/services/audit/audit_service.py
- [X] T054 [P] [US1] Criar teste unitário para AuditService em tests/unit/services/test_audit_service.py
- [X] T055 [US1] Implementar endpoint POST /api/v1/query/interpret em src/api/v1/endpoints/query_interpreter.py
- [X] T056 [US1] Implementar endpoint POST /api/v1/query/{query_id}/execute em src/api/v1/endpoints/query_interpreter.py
- [X] T057 [US1] Implementar endpoint GET /api/v1/query/{query_id} em src/api/v1/endpoints/query_interpreter.py
- [X] T058 [US1] Registrar router query_interpreter no app FastAPI em src/main.py
- [X] T059 [US1] Adicionar tratamento de prompts ambíguos (ex: "usuários novos" → últimos 30 dias) em src/agents/prompt_interpreter.py
- [X] T060 [US1] Adicionar limite de 100 resultados com flag is_partial em src/services/query/executor_service.py

**Checkpoint**: User Story 1 funcional e testável independentemente - MVP pronto

---

## Phase 4: User Story 2 - Feedback de Interpretação (Priority: P2)

**Goal**: Visualizar como o sistema interpretou o prompt antes de executar, para confirmar ou ajustar

**Independent Test**: Verificar se sistema exibe resumo da interpretação antes de executar

### Tests for User Story 2

- [ ] T061 [P] [US2] Criar teste de integração para WebSocket streaming em tests/integration/test_websocket.py
- [ ] T062 [P] [US2] Criar teste unitário para WSHandlers em tests/unit/api/test_websocket_handlers.py

### Implementation for User Story 2

- [ ] T063 [US2] Criar WebSocket handlers para interpret em src/api/v1/websocket/handlers.py
- [ ] T064 [US2] Implementar streaming de status (interpreting, validating, refining) em src/api/v1/websocket/handlers.py
- [ ] T065 [US2] Implementar streaming de chunks do LLM via WebSocket em src/api/v1/websocket/handlers.py
- [ ] T066 [US2] Implementar endpoint WebSocket /ws/query/interpret em src/api/v1/endpoints/query_interpreter.py
- [ ] T067 [US2] Adicionar campo summary em InterpretationResponse com resumo para usuário em src/schemas/query/response.py
- [ ] T068 [US2] Implementar geração de summary em português em src/services/query/interpreter_service.py
- [ ] T069 [US2] Permitir resubmissão de prompt modificado mantendo contexto em src/api/v1/websocket/handlers.py

**Checkpoint**: User Stories 1 e 2 funcionais e testáveis independentemente

---

## Phase 5: User Story 3 - Tratamento de Erros e Sugestões (Priority: P3)

**Goal**: Mensagens claras explicando problemas e sugestões de reformulação quando prompt falha

**Independent Test**: Fornecer prompts inválidos e verificar se sistema dá feedback útil

### Tests for User Story 3

- [ ] T070 [P] [US3] Criar teste para cenário sem resultados em tests/integration/test_error_handling.py
- [ ] T071 [P] [US3] Criar teste para termos não reconhecidos em tests/integration/test_error_handling.py
- [ ] T072 [P] [US3] Criar teste para query bloqueada (comando proibido) em tests/integration/test_error_handling.py

### Implementation for User Story 3

- [ ] T073 [US3] Implementar mensagens de erro em português com sugestões em src/schemas/query/response.py
- [ ] T074 [US3] Adicionar detecção de termos não reconhecidos no catálogo em src/services/query/interpreter_service.py
- [ ] T075 [US3] Adicionar sugestões de termos similares do catálogo em src/services/query/interpreter_service.py
- [ ] T076 [US3] Implementar mensagem "nenhum resultado" com sugestões de critérios mais amplos em src/services/query/executor_service.py
- [ ] T077 [US3] Implementar mensagem detalhada para query bloqueada (qual comando) em src/services/query/validator_service.py
- [ ] T078 [US3] Registrar queries bloqueadas no AuditLog (sem identificação do usuário) em src/services/audit/audit_service.py
- [ ] T079 [US3] Adicionar tratamento de timeout LLM (15s) com mensagem amigável em src/services/llm/openai_client.py
- [ ] T080 [US3] Adicionar tratamento de termos conflitantes (ex: "ativos e inativos") em src/agents/prompt_interpreter.py

**Checkpoint**: Todas as user stories funcionais e testáveis independentemente

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T081 [P] Criar teste de contrato para OpenAI API em tests/contract/test_openai_contract.py
- [ ] T082 [P] Criar teste de contrato para banco de dados QA em tests/contract/test_database_contract.py
- [ ] T083 Adicionar logging estruturado (structlog) em todos os services
- [ ] T084 Adicionar métricas de tempo de resposta (p95) nos services
- [ ] T085 [P] Atualizar documentação em docs/ com exemplos de uso
- [ ] T086 Executar quickstart.md para validar implementação completa
- [ ] T087 Executar pytest --cov=src --cov-report=term-missing e garantir ≥80%
- [ ] T088 Executar ruff e black para lint e formatação

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as user stories
- **User Stories (Phases 3-5)**: Dependem de Foundational
  - Podem prosseguir em paralelo (se equipe permitir)
  - Ou sequencialmente por prioridade (P1 → P2 → P3)
- **Polish (Phase 6)**: Depende de todas as user stories desejadas

### User Story Dependencies

- **User Story 1 (P1)**: Pode começar após Foundational - Sem dependências de outras stories
- **User Story 2 (P2)**: Pode começar após Foundational - Utiliza serviços de US1 mas testável independentemente
- **User Story 3 (P3)**: Pode começar após Foundational - Integra com US1/US2 mas testável independentemente

### Within Each User Story

- Testes DEVEM ser escritos e FALHAR antes da implementação (TDD)
- Modelos antes de serviços
- Serviços antes de endpoints
- Implementação core antes de integração
- Story completa antes de mover para próxima prioridade

### Parallel Opportunities

- Todas as tasks marcadas [P] em Setup podem rodar em paralelo
- Todas as tasks marcadas [P] em Foundational podem rodar em paralelo
- Uma vez Foundational completa, todas as user stories podem começar em paralelo
- Todos os testes de uma user story marcados [P] podem rodar em paralelo
- Modelos dentro de uma story marcados [P] podem rodar em paralelo

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all models in parallel:
Task T012: "Criar enum FilterOperator em src/models/query/enums.py"
Task T013: "Criar enum InterpretationStatus em src/models/query/enums.py"
Task T014: "Criar modelo Entity em src/models/query/interpretation.py"
Task T015: "Criar modelo Filter em src/models/query/interpretation.py"
Task T017: "Criar modelo GeneratedQuery em src/models/query/generated_query.py"
Task T018: "Criar modelo QueryResult em src/models/query/query_result.py"
Task T019: "Criar modelo AuditLog em src/models/query/audit_log.py"

# Launch all schemas in parallel:
Task T021: "Criar schema InterpretPromptRequest em src/schemas/query/request.py"
Task T022: "Criar schema ExecuteQueryRequest em src/schemas/query/request.py"
Task T023: "Criar schema InterpretationResponse em src/schemas/query/response.py"
Task T024: "Criar schema QueryResponse em src/schemas/query/response.py"
Task T025: "Criar schema QueryResultResponse em src/schemas/query/response.py"
Task T026: "Criar schema ErrorResponse em src/schemas/query/response.py"
```

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T039: "Criar teste de contrato para POST /query/interpret"
Task T040: "Criar teste de contrato para POST /query/{id}/execute"
Task T041: "Criar teste de integração para fluxo prompt → query → resultado"

# Launch all unit tests in parallel (after implementations):
Task T046: "Criar teste unitário para InterpreterCrew"
Task T048: "Criar teste unitário para InterpreterService"
Task T050: "Criar teste unitário para ValidatorService"
Task T052: "Criar teste unitário para ExecutorService"
Task T054: "Criar teste unitário para AuditService"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRÍTICO - bloqueia todas as stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Testar User Story 1 independentemente
5. Deploy/demo se pronto

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independentemente → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independentemente → Deploy/Demo
4. Add User Story 3 → Test independentemente → Deploy/Demo
5. Cada story adiciona valor sem quebrar stories anteriores

### Parallel Team Strategy

Com múltiplos desenvolvedores:

1. Equipe completa Setup + Foundational juntos
2. Uma vez Foundational pronto:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories completam e integram independentemente

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica para rastreabilidade
- Cada user story deve ser completável e testável independentemente
- Verificar que testes falham antes de implementar
- Commit após cada task ou grupo lógico
- Pare em qualquer checkpoint para validar story independentemente
- Evitar: tasks vagas, conflitos de mesmo arquivo, dependências cross-story que quebram independência
