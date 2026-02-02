# Tasks: Interpretador LLM para Geração de Queries

**Input**: Design documents from `/specs/001-llm-query-interpreter/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Tests are NOT included in this task list as they were not explicitly requested in the feature specification. Follow TDD approach separately if desired.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and basic configuration

- [ ] T001 Add CrewAI dependency (crewai==1.9.3) to pyproject.toml
- [ ] T002 [P] Create interpreter service directory structure at src/services/interpreter/
- [ ] T003 [P] Create config directory for CrewAI YAML files at src/config/
- [ ] T004 [P] Add OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, OPENAI_MAX_RETRIES to environment configuration in src/config/settings.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create Pydantic schemas for interpreter in src/schemas/interpreter.py (FilterOperator enum, InterpretationStatus enum, QueryFilter, InterpretedQuery, ValidationResult, RefinedQuery, InterpreterCrewOutput)
- [ ] T006 [P] Create WebSocket message schemas in src/schemas/websocket.py (WSMessage, WSStatusMessage, WSChunkMessage, WSInterpretationMessage, WSErrorMessage)
- [ ] T007 [P] Create request/response schemas in src/schemas/interpreter.py (InterpretPromptRequest, ExecuteQueryRequest, InterpretationResponse, QueryResponse, QueryResultResponse, ErrorResponse)
- [ ] T008 Create SQL validator service with blacklist (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER) in src/services/interpreter/validator.py
- [ ] T009 Create AuditLog model for blocked queries in src/models/audit_log.py (id, blocked_query, original_prompt, blocked_command, timestamp, reason - NO user identification per FR-008)
- [ ] T010 [P] Create Alembic migration for audit_log table with indexes (timestamp DESC, blocked_command)
- [ ] T011 Create ConnectionManager for WebSocket connections in src/api/v1/websocket/connection_manager.py
- [ ] T012 Create CatalogContext service for building LLM context from existing CatalogService in src/services/interpreter/catalog_context.py (get_available_tables, get_table_schema, build_llm_context)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Busca por Cenário em Linguagem Natural (Priority: P1) - MVP

**Goal**: Allow QA testers to describe in natural language the type of test data they need and receive matching results via SQL query generation

**Independent Test**: Provide a natural language prompt like "usuários com cartão de crédito ativo" and verify the system returns relevant data matching the description

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create CrewAI agents YAML configuration in src/config/agents.yaml (interpreter, validator, refiner agents with roles, goals, backstories)
- [ ] T014 [P] [US1] Create CrewAI tasks YAML configuration in src/config/tasks.yaml (interpret_task, validate_task, refine_task with descriptions and output_pydantic)
- [ ] T015 [US1] Implement InterpreterCrew class using CrewBase decorator in src/services/interpreter/crew.py (load YAML configs, sequential process, kickoff method)
- [ ] T016 [US1] Configure LLM instance with response_format for structured output in src/services/interpreter/crew.py (model=openai/gpt-4o, timeout=15, max_retries=3, temperature=0.3)
- [ ] T017 [US1] Implement interpret_prompt method in InterpreterService in src/services/interpreter/service.py (receive prompt, build catalog context, call crew, return InterpretedQuery)
- [ ] T018 [US1] Implement query execution service in src/services/interpreter/query_executor.py (execute validated SQL against MongoDB external sources, apply limit, return QueryResult)
- [ ] T019 [US1] Create REST endpoint POST /api/v1/query/interpret in src/api/v1/endpoints/interpreter.py (accept InterpretPromptRequest, return InterpretationWithQueryResponse)
- [ ] T020 [US1] Create REST endpoint POST /api/v1/query/{query_id}/execute in src/api/v1/endpoints/interpreter.py (accept ExecuteQueryRequest, return QueryResultResponse)
- [ ] T021 [US1] Create REST endpoint GET /api/v1/query/{query_id} in src/api/v1/endpoints/interpreter.py (return QueryResponse)
- [ ] T022 [US1] Register interpreter router in main FastAPI application in src/api/v1/router.py
- [ ] T023 [US1] Implement SQL validation before execution in query_executor.py using validator.py (block forbidden commands, log to audit_log if blocked)
- [ ] T024 [US1] Implement result limiting (default 100, max 1000) and is_partial flag when results exceed limit in src/services/interpreter/query_executor.py

**Checkpoint**: User Story 1 complete - QA testers can submit natural language prompts via REST API and receive SQL query results

---

## Phase 4: User Story 2 - Feedback de Interpretação (Priority: P2)

**Goal**: Show QA testers how the system interpreted their prompt before executing the query, enabling confirmation or adjustment

**Independent Test**: Submit a prompt and verify the system displays a summary like "Buscarei usuários onde: cartão de crédito = ativo E fatura = vencida" before returning results

### Implementation for User Story 2

- [ ] T025 [US2] Create WebSocket endpoint /ws/query/interpret in src/api/v1/websocket/interpreter_ws.py (accept WebSocket connection, handle interpret messages)
- [ ] T026 [US2] Implement streaming status updates via WebSocket in src/api/v1/websocket/interpreter_ws.py (send WSStatusMessage for interpreting, validating, refining, ready states)
- [ ] T027 [US2] Implement chunk streaming for LLM processing feedback in src/api/v1/websocket/interpreter_ws.py (send WSChunkMessage with partial content and agent name)
- [ ] T028 [US2] Send WSInterpretationMessage with summary and entities/filters before query execution in src/api/v1/websocket/interpreter_ws.py
- [ ] T029 [US2] Implement natural_explanation field generation in interpreter agent (human-readable summary of interpretation criteria)
- [ ] T030 [US2] Add confidence score display in interpretation response (0.0-1.0 range indicating interpretation certainty)
- [ ] T031 [US2] Implement session context preservation for prompt refinement (allow user to modify prompt without losing previous context)

**Checkpoint**: User Story 2 complete - QA testers can see real-time interpretation feedback via WebSocket before query execution

---

## Phase 5: User Story 3 - Tratamento de Erros e Sugestões (Priority: P3)

**Goal**: Provide clear error messages and suggestions when prompts cannot be interpreted or return no results

**Independent Test**: Submit an invalid prompt or one that returns no results and verify the system provides helpful feedback and suggestions

### Implementation for User Story 3

- [ ] T032 [US3] Implement error handling for unrecognized terms in src/services/interpreter/service.py (detect unknown entities/fields, suggest similar terms from catalog)
- [ ] T033 [US3] Implement no-results handling with suggestions in src/services/interpreter/query_executor.py (suggest broader criteria when query returns empty)
- [ ] T034 [US3] Create error suggestion generator in src/services/interpreter/suggestion_service.py (find similar catalog terms using fuzzy matching)
- [ ] T035 [US3] Implement ambiguity detection in interpreter agent (detect conflicting terms like "ativos e inativos", request clarification or apply default)
- [ ] T036 [US3] Handle LLM timeout with user-friendly message in src/services/interpreter/service.py (return LLM_TIMEOUT error after 15s with retry suggestion)
- [ ] T037 [US3] Implement blocked query error response with detail in src/services/interpreter/validator.py (return SQL_COMMAND_BLOCKED with specific blocked command)
- [ ] T038 [US3] Add suggestions array to ErrorResponse for all error types in src/schemas/interpreter.py (actionable suggestions for error recovery)
- [ ] T039 [US3] Implement WSErrorMessage streaming for WebSocket errors in src/api/v1/websocket/interpreter_ws.py (send error with suggestions via WebSocket)

**Checkpoint**: User Story 3 complete - QA testers receive helpful error messages and suggestions when issues occur

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Add logging for all interpreter operations in src/services/interpreter/ (prompt received, interpretation started, query generated, execution completed)
- [ ] T041 [P] Add performance metrics collection (p95 targets: <2s for queries, <15s for LLM interpretation)
- [ ] T042 [P] Implement graceful WebSocket disconnection handling in src/api/v1/websocket/connection_manager.py
- [ ] T043 Run quickstart.md validation scenarios manually to verify full flow works
- [ ] T044 [P] Add OpenAPI documentation for REST endpoints (ensure auto-generated docs match contracts/openapi.yaml)
- [ ] T045 Code cleanup and ensure Ruff/Black/MyPy compliance across all new files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses components from US1 but adds WebSocket layer
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances error handling across US1/US2

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- YAML configs before Python crew implementation

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- T013 and T014 (YAML configs) can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch YAML configurations together:
Task: "Create CrewAI agents YAML configuration in src/config/agents.yaml"
Task: "Create CrewAI tasks YAML configuration in src/config/tasks.yaml"

# After YAMLs are done, proceed with Python implementation:
Task: "Implement InterpreterCrew class using CrewBase decorator in src/services/interpreter/crew.py"
```

## Parallel Example: Foundational Phase

```bash
# Launch all parallel foundational tasks together:
Task: "Create WebSocket message schemas in src/schemas/websocket.py"
Task: "Create request/response schemas in src/schemas/interpreter.py"
Task: "Create Alembic migration for audit_log table"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 via REST API with prompts like "usuários com cartão de crédito ativo"
5. Deploy/demo if ready - core value is delivered

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test via REST API → Deploy/Demo (MVP!)
3. Add User Story 2 → Test WebSocket streaming → Deploy/Demo (Enhanced UX)
4. Add User Story 3 → Test error scenarios → Deploy/Demo (Robust error handling)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (REST API + CrewAI)
   - Developer B: User Story 2 (WebSocket streaming)
   - Developer C: User Story 3 (Error handling)
3. Stories complete and integrate independently

---

## Key Files Summary

| File | Phase | Purpose |
|------|-------|---------|
| `src/schemas/interpreter.py` | 2 | Pydantic models for LLM response_format and API |
| `src/schemas/websocket.py` | 2 | WebSocket message schemas |
| `src/services/interpreter/validator.py` | 2 | SQL blacklist validation |
| `src/services/interpreter/catalog_context.py` | 2 | Build LLM context from catalog |
| `src/models/audit_log.py` | 2 | Audit log for blocked queries |
| `src/config/agents.yaml` | 3 | CrewAI agent definitions |
| `src/config/tasks.yaml` | 3 | CrewAI task definitions |
| `src/services/interpreter/crew.py` | 3 | InterpreterCrew orchestration |
| `src/services/interpreter/service.py` | 3 | Main InterpreterService |
| `src/services/interpreter/query_executor.py` | 3 | Query execution against MongoDB |
| `src/api/v1/endpoints/interpreter.py` | 3 | REST API endpoints |
| `src/api/v1/websocket/connection_manager.py` | 2 | WebSocket connection management |
| `src/api/v1/websocket/interpreter_ws.py` | 4 | WebSocket endpoint for streaming |
| `src/services/interpreter/suggestion_service.py` | 5 | Error suggestions and fuzzy matching |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- CrewAI uses `response_format` with Pydantic models for structured LLM output
- SQL validation uses blacklist approach (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER blocked)
- Audit log does NOT include user identification per FR-008
