# Tasks: CLI Chat Interativo para QAUserSearch

**Feature Branch**: `005-cli-chat`  
**Input**: `specs/005-cli-chat/spec.md`, `specs/005-cli-chat/plan.md`, `specs/005-cli-chat/data-model.md`  
**Created**: 2026-02-05  
**Prerequisite**: [`003-cli-shared-ui`](../003-cli-shared-ui/spec.md) (infraestrutura de UI compartilhada)

---

## User Stories Summary

| ID | Story | Priority | Estimativa |
|----|-------|----------|------------|
| US1 | Sessão de Chat Básica | P1 | 2.5h |
| US2 | Feedback Visual em Tempo Real | P1 | 1.5h |
| US3 | Comandos Especiais do Chat | P1 | 1.5h |
| US4 | Modo Mock para Desenvolvimento | P2 | 1.5h |
| US5 | Sugestões Interativas para Ambiguidades | P2 | 1h |
| US6 | Conexão WebSocket Real | P2 | 1.5h |
| US7 | Entry Point Unificado | P3 | 45min |

**Total Estimado**: ~11h

---

## Phase 1: Setup

**Purpose**: Criar estrutura de diretórios e arquivos base

- [ ] T001 Criar estrutura `src/cli/chat/` com `__init__.py`
- [ ] T002 [P] Criar estrutura `src/cli/chat/handlers/` com `__init__.py`
- [ ] T003 [P] Criar estrutura `tests/unit/cli/chat/` com `__init__.py`
- [ ] T004 [P] Criar `tests/unit/cli/chat/conftest.py` com fixtures (mock_console, mock_websocket, chat_session, sample_interpretation, sample_query)

**Checkpoint**: Estrutura pronta para implementação

---

## Phase 2: Foundational - Session & Commands (US3 parcial)

**Purpose**: Componentes base que TODOS os outros dependem

**⚠️ CRITICAL**: US1, US2, US4, US5, US6 dependem desta fase

### Session State Management

**Goal**: Gerenciar estado da sessão (histórico, última query, modo mock)

**Independent Test**: Criar `ChatSession()`, adicionar queries, verificar histórico limitado a 10 itens

#### Testes TDD (RED)

- [ ] T005 [P] Criar teste `test_query_record_dataclass` em `tests/unit/cli/chat/test_session.py`
- [ ] T006 [P] Criar teste `test_query_record_was_successful_true` em `tests/unit/cli/chat/test_session.py`
- [ ] T007 [P] Criar teste `test_query_record_was_successful_false` em `tests/unit/cli/chat/test_session.py`
- [ ] T008 [P] Criar teste `test_chat_session_initial_state` em `tests/unit/cli/chat/test_session.py`
- [ ] T009 [P] Criar teste `test_chat_session_add_query` em `tests/unit/cli/chat/test_session.py`
- [ ] T010 [P] Criar teste `test_chat_session_history_max_10` em `tests/unit/cli/chat/test_session.py`
- [ ] T011 [P] Criar teste `test_chat_session_clear` em `tests/unit/cli/chat/test_session.py`
- [ ] T012 [P] Criar teste `test_chat_session_toggle_mock_mode` em `tests/unit/cli/chat/test_session.py`

#### Implementação (GREEN)

- [ ] T013 Implementar `QueryRecord` dataclass em `src/cli/chat/session.py`
- [ ] T014 Implementar `ChatSession` dataclass em `src/cli/chat/session.py`
- [ ] T015 Implementar `ChatSession.add_query()` com limite de 10 itens (FIFO)
- [ ] T016 Implementar `ChatSession.get_history()`, `clear()`, `toggle_mock_mode()`

#### Refactor

- [ ] T017 Verificar testes passam e refatorar se necessário

**Checkpoint Session**: `from src.cli.chat.session import ChatSession, QueryRecord` funciona

---

### Command Processing (US3)

**Goal**: Processar comandos especiais (/exit, /help, /clear, /history, /execute, /mock)

**Independent Test**: Executar cada comando e verificar `CommandResult` retornado

#### Testes TDD (RED)

- [ ] T018 [P] [US3] Criar teste `test_command_type_enum_values` em `tests/unit/cli/chat/test_commands.py`
- [ ] T019 [P] [US3] Criar teste `test_is_command_true` em `tests/unit/cli/chat/test_commands.py`
- [ ] T020 [P] [US3] Criar teste `test_is_command_false_no_slash` em `tests/unit/cli/chat/test_commands.py`
- [ ] T021 [P] [US3] Criar teste `test_parse_command_exit` em `tests/unit/cli/chat/test_commands.py`
- [ ] T022 [P] [US3] Criar teste `test_parse_command_quit_alias` em `tests/unit/cli/chat/test_commands.py`
- [ ] T023 [P] [US3] Criar teste `test_parse_command_case_insensitive` em `tests/unit/cli/chat/test_commands.py`
- [ ] T024 [P] [US3] Criar teste `test_parse_command_unknown_returns_none` em `tests/unit/cli/chat/test_commands.py`
- [ ] T025 [P] [US3] Criar teste `test_execute_command_exit` em `tests/unit/cli/chat/test_commands.py`
- [ ] T026 [P] [US3] Criar teste `test_execute_command_help` em `tests/unit/cli/chat/test_commands.py`
- [ ] T027 [P] [US3] Criar teste `test_execute_command_clear` em `tests/unit/cli/chat/test_commands.py`
- [ ] T028 [P] [US3] Criar teste `test_execute_command_history` em `tests/unit/cli/chat/test_commands.py`
- [ ] T029 [P] [US3] Criar teste `test_execute_command_execute_shows_info` em `tests/unit/cli/chat/test_commands.py`
- [ ] T030 [P] [US3] Criar teste `test_execute_command_mock_toggles` em `tests/unit/cli/chat/test_commands.py`

#### Implementação (GREEN)

- [ ] T031 [US3] Implementar `CommandType` enum em `src/cli/chat/commands.py`
- [ ] T032 [US3] Implementar `CommandResult` dataclass em `src/cli/chat/commands.py`
- [ ] T033 [US3] Implementar `is_command(text)` em `src/cli/chat/commands.py`
- [ ] T034 [US3] Implementar `parse_command(text)` com case-insensitive e aliases
- [ ] T035 [US3] Implementar `execute_command()` para EXIT/QUIT
- [ ] T036 [US3] Implementar `execute_command()` para HELP (usa renderer)
- [ ] T037 [US3] Implementar `execute_command()` para CLEAR
- [ ] T038 [US3] Implementar `execute_command()` para HISTORY
- [ ] T039 [US3] Implementar `execute_command()` para EXECUTE (simulação v1)
- [ ] T040 [US3] Implementar `execute_command()` para MOCK

#### Refactor

- [ ] T041 [US3] Verificar testes passam e refatorar se necessário

**Checkpoint Commands**: Todos os 6 comandos funcionam conforme spec

---

## Phase 3: User Story 1 - Sessão de Chat Básica (P1) 🎯 MVP

**Goal**: Usuário pode iniciar chat, enviar query, ver interpretação e SQL

**Independent Test**: Executar `qa chat --mock`, digitar query, ver painéis de resultado

### Renderer - Welcome, Interpretation, Query Panels

#### Testes TDD (RED)

- [ ] T042 [P] [US1] Criar teste `test_render_welcome_returns_panel` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T043 [P] [US1] Criar teste `test_render_welcome_contains_instructions` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T044 [P] [US1] Criar teste `test_render_interpretation_returns_panel` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T045 [P] [US1] Criar teste `test_render_interpretation_contains_summary` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T046 [P] [US1] Criar teste `test_render_interpretation_contains_entities_table` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T047 [P] [US1] Criar teste `test_render_interpretation_contains_filters_table` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T048 [P] [US1] Criar teste `test_render_query_returns_panel` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T049 [P] [US1] Criar teste `test_render_query_has_sql_syntax_highlight` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T050 [P] [US1] Criar teste `test_render_confidence_bar_high` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T051 [P] [US1] Criar teste `test_render_confidence_bar_medium` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T052 [P] [US1] Criar teste `test_render_confidence_bar_low` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T053 [P] [US1] Criar teste `test_render_history_returns_table` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T054 [P] [US1] Criar teste `test_render_help_returns_panel` em `tests/unit/cli/chat/test_renderer.py`
- [ ] T055 [P] [US1] Criar teste `test_render_error_returns_panel` em `tests/unit/cli/chat/test_renderer.py`

#### Implementação (GREEN)

- [ ] T056 [US1] Implementar `render_welcome()` em `src/cli/chat/renderer.py` (banner ASCII, instruções, exemplos)
- [ ] T057 [US1] Implementar `render_confidence_bar()` em `src/cli/chat/renderer.py` (verde/âmbar/vermelho)
- [ ] T058 [US1] Implementar `render_interpretation()` em `src/cli/chat/renderer.py` (resumo, confiança, entidades, filtros)
- [ ] T059 [US1] Implementar `render_query()` em `src/cli/chat/renderer.py` (SQL com syntax highlighting)
- [ ] T060 [US1] Implementar `render_history()` em `src/cli/chat/renderer.py`
- [ ] T061 [US1] Implementar `render_help()` em `src/cli/chat/renderer.py`
- [ ] T062 [US1] Implementar `render_error()` em `src/cli/chat/renderer.py`

#### Refactor

- [ ] T063 [US1] Verificar testes passam e refatorar se necessário

**Checkpoint US1 Renderer**: Painéis renderizam corretamente

---

## Phase 4: User Story 4 - Modo Mock (P2)

**Goal**: CLI funciona 100% offline com respostas simuladas

**Independent Test**: Executar `qa chat --mock` sem servidor, verificar que tudo funciona

### Mock Client

#### Testes TDD (RED)

- [ ] T064 [P] [US4] Criar teste `test_mock_client_connect_succeeds` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T065 [P] [US4] Criar teste `test_mock_client_is_connected` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T066 [P] [US4] Criar teste `test_mock_client_disconnect` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T067 [P] [US4] Criar teste `test_mock_client_send_prompt_normal` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T068 [P] [US4] Criar teste `test_mock_client_send_prompt_returns_status_messages` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T069 [P] [US4] Criar teste `test_mock_client_send_prompt_returns_interpretation` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T070 [P] [US4] Criar teste `test_mock_client_send_prompt_returns_query` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T071 [P] [US4] Criar teste `test_mock_client_error_keyword` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T072 [P] [US4] Criar teste `test_mock_client_ambiguity_keyword` em `tests/unit/cli/chat/test_mock_client.py`
- [ ] T073 [P] [US4] Criar teste `test_mock_client_simulates_delay` em `tests/unit/cli/chat/test_mock_client.py`

#### Implementação (GREEN)

- [ ] T074 [US4] Implementar `MockChatClient.__init__()` em `src/cli/chat/mock_client.py`
- [ ] T075 [US4] Implementar `MockChatClient.connect()` e `disconnect()`
- [ ] T076 [US4] Implementar `MockChatClient.is_connected` property
- [ ] T077 [US4] Implementar `MockChatClient.send_prompt()` com cenário normal
- [ ] T078 [US4] Implementar cenário "erro" em `send_prompt()` (retorna WSErrorMessage)
- [ ] T079 [US4] Implementar cenário "ambiguidade" em `send_prompt()` (retorna com ambiguities)
- [ ] T080 [US4] Implementar delays simulados (500-2000ms)

#### Refactor

- [ ] T081 [US4] Verificar testes passam e refatorar se necessário

**Checkpoint US4**: Modo mock funciona 100% offline

---

## Phase 5: User Story 2 - Feedback Visual (P1) 🎯 MVP

**Goal**: Spinners e status durante processamento de queries

**Independent Test**: Enviar query e observar PhaseSpinner com fases distintas

### Message Handler

#### Testes TDD (RED)

- [ ] T082 [P] [US2] Criar teste `test_message_handler_init` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T083 [P] [US2] Criar teste `test_handle_status_updates_spinner` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T084 [P] [US2] Criar teste `test_handle_chunk_appends_content` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T085 [P] [US2] Criar teste `test_handle_interpretation_renders_panel` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T086 [P] [US2] Criar teste `test_handle_interpretation_updates_session` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T087 [P] [US2] Criar teste `test_handle_query_renders_panel` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T088 [P] [US2] Criar teste `test_handle_query_updates_session` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T089 [P] [US2] Criar teste `test_handle_error_renders_error_panel` em `tests/unit/cli/chat/test_handlers.py`

#### Implementação (GREEN)

- [ ] T090 [US2] Implementar `MessageHandler.__init__()` em `src/cli/chat/handlers/message_handler.py`
- [ ] T091 [US2] Implementar `MessageHandler.handle_status()` (atualiza PhaseSpinner)
- [ ] T092 [US2] Implementar `MessageHandler.handle_chunk()` (streaming content)
- [ ] T093 [US2] Implementar `MessageHandler.handle_interpretation()` (renderiza + atualiza session)
- [ ] T094 [US2] Implementar `MessageHandler.handle_query()` (renderiza + atualiza session)
- [ ] T095 [US2] Implementar `MessageHandler.handle_error()` (renderiza erro)

#### Refactor

- [ ] T096 [US2] Verificar testes passam e refatorar se necessário

**Checkpoint US2**: Feedback visual funciona com spinners e status

---

## Phase 6: User Story 5 - Sugestões Interativas (P2)

**Goal**: Prompts interativos quando há ambiguidades na interpretação

**Independent Test**: Enviar query com "ambiguidade", ver prompt com opções, selecionar uma

### Suggestion Handler

#### Testes TDD (RED)

- [ ] T097 [P] [US5] Criar teste `test_has_critical_ambiguities_true` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T098 [P] [US5] Criar teste `test_has_critical_ambiguities_false` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T099 [P] [US5] Criar teste `test_prompt_for_clarification_shows_options` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T100 [P] [US5] Criar teste `test_prompt_for_clarification_returns_selection` em `tests/unit/cli/chat/test_handlers.py`
- [ ] T101 [P] [US5] Criar teste `test_prompt_for_clarification_cancelled_returns_none` em `tests/unit/cli/chat/test_handlers.py`

#### Implementação (GREEN)

- [ ] T102 [US5] Implementar `SuggestionHandler` class em `src/cli/chat/handlers/suggestion_handler.py`
- [ ] T103 [US5] Implementar `has_critical_ambiguities()` (verifica se ambiguities não vazio)
- [ ] T104 [US5] Implementar `prompt_for_clarification()` (usa ask_select de shared/ui)

#### Refactor

- [ ] T105 [US5] Verificar testes passam e refatorar se necessário

**Checkpoint US5**: Sugestões interativas funcionam para queries ambíguas

---

## Phase 7: User Story 6 - Conexão WebSocket Real (P2)

**Goal**: CLI conecta ao backend real via WebSocket

**Independent Test**: Executar `qa chat --server ws://localhost:8000/ws/query/interpret` com backend rodando

### WebSocket Client

#### Testes TDD (RED)

- [ ] T106 [P] [US6] Criar teste `test_ws_client_init_default_url` em `tests/unit/cli/chat/test_client.py`
- [ ] T107 [P] [US6] Criar teste `test_ws_client_init_custom_url` em `tests/unit/cli/chat/test_client.py`
- [ ] T108 [P] [US6] Criar teste `test_ws_client_connect` em `tests/unit/cli/chat/test_client.py`
- [ ] T109 [P] [US6] Criar teste `test_ws_client_disconnect` em `tests/unit/cli/chat/test_client.py`
- [ ] T110 [P] [US6] Criar teste `test_ws_client_is_connected` em `tests/unit/cli/chat/test_client.py`
- [ ] T111 [P] [US6] Criar teste `test_ws_client_send_prompt_sends_message` em `tests/unit/cli/chat/test_client.py`
- [ ] T112 [P] [US6] Criar teste `test_ws_client_send_prompt_yields_responses` em `tests/unit/cli/chat/test_client.py`
- [ ] T113 [P] [US6] Criar teste `test_ws_client_reconnect_on_disconnect` em `tests/unit/cli/chat/test_client.py`
- [ ] T114 [P] [US6] Criar teste `test_ws_client_max_retries_exceeded` em `tests/unit/cli/chat/test_client.py`
- [ ] T115 [P] [US6] Criar teste `test_ws_client_backoff_exponential` em `tests/unit/cli/chat/test_client.py`

#### Implementação (GREEN)

- [ ] T116 [US6] Implementar `ChatClientProtocol` em `src/cli/chat/client.py`
- [ ] T117 [US6] Implementar `WSChatClient.__init__()` em `src/cli/chat/client.py`
- [ ] T118 [US6] Implementar `WSChatClient.connect()` usando websockets library
- [ ] T119 [US6] Implementar `WSChatClient.disconnect()`
- [ ] T120 [US6] Implementar `WSChatClient.is_connected` property
- [ ] T121 [US6] Implementar `WSChatClient.send_prompt()` como AsyncIterator
- [ ] T122 [US6] Implementar reconnection automática com backoff exponencial (max 3 retries)
- [ ] T123 [US6] Implementar tratamento de erro quando reconexão falha

#### Refactor

- [ ] T124 [US6] Verificar testes passam e refatorar se necessário

**Checkpoint US6**: Conexão WebSocket real funciona com reconexão automática

---

## Phase 8: User Story 7 - Entry Point Unificado (P3)

**Goal**: Comando `qa` com subcomandos `chat` e `catalog`

**Independent Test**: Executar `qa --help` e ver subcomandos listados

### Entry Point

#### Testes TDD (RED)

- [ ] T125 [P] [US7] Criar teste `test_qa_help_lists_subcommands` em `tests/unit/cli/test_main.py`
- [ ] T126 [P] [US7] Criar teste `test_qa_chat_help` em `tests/unit/cli/test_main.py`
- [ ] T127 [P] [US7] Criar teste `test_qa_catalog_help` em `tests/unit/cli/test_main.py`

#### Implementação (GREEN)

- [ ] T128 [US7] Criar `src/cli/main.py` com Typer app principal
- [ ] T129 [US7] Registrar subcomando `catalog` (existente)
- [ ] T130 [US7] Implementar `chat` command com flags `--mock` e `--server`
- [ ] T131 [US7] Atualizar `pyproject.toml` scripts para usar `qa` entry point

#### Refactor

- [ ] T132 [US7] Verificar testes passam e refatorar se necessário

**Checkpoint US7**: `qa chat --mock` e `qa catalog` funcionam

---

## Phase 9: Integration - Main Chat Loop

**Purpose**: Orquestrar todos os módulos no loop principal

### Chat Loop

- [ ] T133 Implementar `run_chat()` em `src/cli/chat/__init__.py`
- [ ] T134 Implementar welcome screen display
- [ ] T135 Implementar input loop com prompt interativo
- [ ] T136 Implementar detecção de comando vs query
- [ ] T137 Implementar processamento de query (client → handler → renderer)
- [ ] T138 Implementar Ctrl+C handling gracioso
- [ ] T139 Implementar session history update após cada query
- [ ] T140 Implementar toggle entre mock e real client via /mock

**Checkpoint Integration**: Chat loop completo funcionando

---

## Phase 10: Polish & Validation

**Purpose**: Qualidade, edge cases e verificação manual

### Edge Cases

- [ ] T141 Implementar validação de prompt (1-2000 chars)
- [ ] T142 Implementar tratamento de terminal estreito (<60 cols)
- [ ] T143 Implementar fallback para terminal sem TTY (non-interactive)
- [ ] T144 Implementar escape de caracteres especiais no prompt
- [ ] T145 Implementar timeout de resposta (30s)

### Quality Gates

- [ ] T146 Executar `uv run ruff check src/cli/chat/ tests/unit/cli/chat/` - zero erros
- [ ] T147 [P] Executar `uv run mypy src/cli/chat/ tests/unit/cli/chat/` - zero erros
- [ ] T148 [P] Executar `uv run black src/cli/chat/ tests/unit/cli/chat/` - formatação ok
- [ ] T149 Executar `uv run pytest tests/unit/cli/chat/ -v` - todos os testes passam
- [ ] T150 Verificar cobertura >80% para `src/cli/chat/`

### Verificação Manual

- [ ] T151 [P] Verificação manual: welcome screen renderiza corretamente
- [ ] T152 [P] Verificação manual: painéis de interpretação/SQL com cores
- [ ] T153 [P] Verificação manual: PhaseSpinner anima sem flicker
- [ ] T154 [P] Verificação manual: comandos especiais funcionam
- [ ] T155 [P] Verificação manual: Ctrl+C sai graciosamente
- [ ] T156 [P] Verificação manual: `NO_COLOR=1` output legível
- [ ] T157 [P] Verificação manual: modo mock funciona offline

**Checkpoint Final**: Qualidade validada, pronto para merge ✅

---

## Dependencies Graph

```
Phase 1: Setup
    T001-T004 ──────────────────────────────────────► Phase 2

Phase 2: Foundational (Session + Commands)
    ┌─ Session ─────────────────────────────────────┐
    │  T005-T012 tests ──► T013-T016 impl ──► T017  │
    ├───────────────────────────────────────────────┤
    │  Commands (US3)                                │
    │  T018-T030 tests ──► T031-T040 impl ──► T041  │
    └───────────────────────────────────────────────┘
            │
            ▼ (BLOCKS)
    ┌───────────────────────────────────────────────┐
    │        Phases 3-8: User Stories               │
    │                                                │
    │  ┌────────────────┐  ┌────────────────┐      │
    │  │ US1 Renderer   │  │ US4 Mock Client│      │
    │  │ T042-T063      │  │ T064-T081      │      │
    │  └───────┬────────┘  └───────┬────────┘      │
    │          │                   │                │
    │          └──────────┬────────┘                │
    │                     ▼                         │
    │  ┌────────────────────────────────────┐      │
    │  │ US2 Message Handler                 │      │
    │  │ T082-T096 (depende de Renderer+Mock)│      │
    │  └───────────────┬────────────────────┘      │
    │                  │                            │
    │  ┌───────────────▼────────────────────┐      │
    │  │ US5 Suggestion Handler              │      │
    │  │ T097-T105                            │      │
    │  └────────────────────────────────────┘      │
    │                                                │
    │  ┌────────────────┐  ┌────────────────┐      │
    │  │ US6 WS Client  │  │ US7 Entry Point│      │
    │  │ T106-T124      │  │ T125-T132      │      │
    │  └────────────────┘  └────────────────┘      │
    │         [P]                [P]                │
    └───────────────────────────────────────────────┘
            │
            ▼
Phase 9: Integration
    T133-T140 (depende de todos os módulos)
            │
            ▼
Phase 10: Polish
    T141-T157 ──► DONE
```

---

## Time Estimates

| Phase | Tasks | Estimativa |
|-------|-------|------------|
| Setup | T001-T004 | 30min |
| Session | T005-T017 | 45min |
| Commands (US3) | T018-T041 | 1.5h |
| Renderer (US1) | T042-T063 | 1.5h |
| Mock Client (US4) | T064-T081 | 1.5h |
| Message Handler (US2) | T082-T096 | 1h |
| Suggestion Handler (US5) | T097-T105 | 45min |
| WS Client (US6) | T106-T124 | 1.5h |
| Entry Point (US7) | T125-T132 | 45min |
| Integration | T133-T140 | 1h |
| Polish | T141-T157 | 1h |
| **Total** | **157 tasks** | **~11h** |

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Session + Commands)
3. Complete Phase 3: US1 Renderer
4. Complete Phase 4: US4 Mock Client
5. Complete Phase 5: US2 Message Handler
6. **STOP and VALIDATE**: Testar `qa chat --mock` end-to-end
7. Deploy se suficiente para demo

### Full Feature

1. Complete MVP (phases 1-5)
2. Complete US5: Suggestion Handler (Phase 6)
3. Complete US6: WS Client (Phase 7) - conexão real
4. Complete US7: Entry Point (Phase 8)
5. Complete Integration + Polish (Phases 9-10)
6. Merge para branch principal

### Parallel Opportunities

Com múltiplos desenvolvedores após Phase 2:
- Dev A: US1 (Renderer) + US2 (Message Handler)
- Dev B: US4 (Mock Client) + US5 (Suggestion Handler)
- Dev C: US6 (WS Client) + US7 (Entry Point)

---

## Success Criteria (from Spec)

- [ ] **SC-001**: Fluxo básico completo em <10s (modo mock)
- [ ] **SC-002**: 6 comandos especiais funcionando
- [ ] **SC-003**: Modo mock 100% offline
- [ ] **SC-004**: Reconexão automática funciona
- [ ] **SC-005**: Zero erros mypy/ruff/black
- [ ] **SC-006**: Cobertura >80% para `src/cli/chat/`
- [ ] **SC-007**: Ctrl+C graceful em qualquer estado
- [ ] **SC-008**: Output legível com NO_COLOR=1
- [ ] **SC-009**: Sugestões interativas funcionam
- [ ] **SC-010**: Entry point `qa` com subcomandos

---

## Notes

- **[P]**: Tasks podem rodar em paralelo (arquivos diferentes, sem dependências)
- **[USx]**: Identifica qual User Story a task pertence
- **TDD Flow**: RED (testes falham) → GREEN (implementar) → REFACTOR (melhorar)
- Commit após cada checkpoint de User Story
- Verificações manuais agrupadas no final (Phase 10) para eficiência
- MockChatClient é prioridade alta pois habilita desenvolvimento offline
- Renderer é base para todos os handlers
