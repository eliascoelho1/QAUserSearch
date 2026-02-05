# Tasks: Infraestrutura Compartilhada de CLI UI

**Feature Branch**: `01-cli-shared-ui`  
**Input**: `.specify/plans/01P-cli-shared-ui.md`, `.specify/specs/01S-cli-shared-ui.md`  
**Design Reference**: `docs/plans/01-cli-shared-ui.md`  
**Created**: 2026-02-04

---

## User Stories Summary

| ID | Story | Priority | Estimativa |
|----|-------|----------|------------|
| US1 | Painéis de Feedback Visual Consistentes | P1 | 1.5h |
| US2 | Spinners e Progress Bars | P1 | 2h |
| US3 | Prompts Interativos Padronizados | P1 | 1.5h |
| US4 | Prompt de Aprovação Reutilizável | P2 | 45min |
| US5 | Sistema de Tema Unificado | P2 | 1h |
| US6 | Utilitários de Terminal | P3 | 45min |
| US7 | Console Pré-configurado | P3 | 30min |

**Total Estimado**: 8h

---

## Phase 1: Setup

**Purpose**: Criar estrutura de diretórios e arquivos base

- [x] T001 Criar estrutura `src/cli/shared/` com `__init__.py` em cada nível
- [x] T002 [P] Criar estrutura `tests/unit/cli/shared/` com `__init__.py`
- [x] T003 [P] Criar `tests/unit/cli/shared/conftest.py` com fixtures de mock

**Checkpoint**: Estrutura pronta para implementação

---

## Phase 2: Foundational (US5 + US6 + US7) - Pré-requisitos

**Purpose**: Componentes base que TODOS os outros dependem

**CRITICAL**: US1, US2, US3, US4 dependem desta fase

### US5 - Sistema de Tema Unificado (P2) - Base

**Goal**: Fornecer paleta de cores e estilos para Rich/Questionary

**Independent Test**: Importar `COLORS` e verificar constantes hex válidas

#### Testes TDD (RED)

- [x] T004 [P] [US5] Criar teste `test_colors_constants_exist` em `tests/unit/cli/shared/test_theme.py`
- [x] T005 [P] [US5] Criar teste `test_colors_are_valid_hex` em `tests/unit/cli/shared/test_theme.py`
- [x] T006 [P] [US5] Criar teste `test_get_icon_unicode` em `tests/unit/cli/shared/test_theme.py`
- [x] T007 [P] [US5] Criar teste `test_get_icon_ascii_fallback` em `tests/unit/cli/shared/test_theme.py`
- [x] T008 [P] [US5] Criar teste `test_get_rich_theme_returns_theme` em `tests/unit/cli/shared/test_theme.py`
- [x] T009 [P] [US5] Criar teste `test_get_questionary_style_returns_style` em `tests/unit/cli/shared/test_theme.py`

#### Implementação (GREEN)

- [x] T010 [US5] Implementar `COLORS` namespace em `src/cli/shared/ui/theme.py`
- [x] T011 [US5] Implementar `IconType` enum e mapeamentos `ICONS_EMOJI`/`ICONS_ASCII`
- [x] T012 [US5] Implementar `get_icon(icon_type, use_unicode)` em `src/cli/shared/ui/theme.py`
- [x] T013 [US5] Implementar `get_rich_theme()` em `src/cli/shared/ui/theme.py`
- [x] T014 [US5] Implementar `get_questionary_style()` em `src/cli/shared/ui/theme.py`

#### Refactor

- [x] T015 [US5] Verificar testes passam e refatorar se necessário

**Checkpoint US5**: `from src.cli.shared.ui.theme import COLORS, get_rich_theme` funciona

---

### US6 - Utilitários de Terminal (P3) - Base

**Goal**: Detectar capacidades do terminal (cores, unicode, tamanho)

**Independent Test**: Executar com `NO_COLOR=1` e verificar `supports_color() == False`

#### Testes TDD (RED)

- [x] T016 [P] [US6] Criar teste `test_supports_color_no_color_env` em `tests/unit/cli/shared/test_terminal.py`
- [x] T017 [P] [US6] Criar teste `test_supports_color_force_color_env` em `tests/unit/cli/shared/test_terminal.py`
- [x] T018 [P] [US6] Criar teste `test_supports_unicode_windows_no_wt` em `tests/unit/cli/shared/test_terminal.py`
- [x] T019 [P] [US6] Criar teste `test_is_interactive_tty` em `tests/unit/cli/shared/test_terminal.py`
- [x] T020 [P] [US6] Criar teste `test_is_interactive_pipe` em `tests/unit/cli/shared/test_terminal.py`
- [x] T021 [P] [US6] Criar teste `test_get_terminal_size_fallback` em `tests/unit/cli/shared/test_terminal.py`

#### Implementação (GREEN)

- [x] T022 [US6] Implementar `get_terminal_size()` em `src/cli/shared/utils/terminal.py`
- [x] T023 [US6] Implementar `supports_color()` com lógica NO_COLOR/FORCE_COLOR
- [x] T024 [US6] Implementar `supports_unicode()` com detecção Windows/Unix
- [x] T025 [US6] Implementar `is_interactive()` com isatty checks

#### Refactor

- [x] T026 [US6] Verificar testes passam e refatorar se necessário

**Checkpoint US6**: Detecção de capacidades funciona em diferentes ambientes

---

### US7 - Console Pré-configurado (P3) - Base

**Goal**: Factory para criar Console Rich pré-configurado

**Independent Test**: Chamar `create_console()` e verificar tema aplicado

#### Testes TDD (RED)

- [x] T027 [P] [US7] Criar teste `test_create_console_default` em `tests/unit/cli/shared/test_terminal.py`
- [x] T028 [P] [US7] Criar teste `test_create_console_no_color` em `tests/unit/cli/shared/test_terminal.py`
- [x] T029 [P] [US7] Criar teste `test_create_console_no_unicode` em `tests/unit/cli/shared/test_terminal.py`

#### Implementação (GREEN)

- [x] T030 [US7] Implementar `create_console()` em `src/cli/shared/utils/terminal.py`
- [x] T031 [US7] Integrar `get_rich_theme()` no console factory

#### Refactor

- [x] T032 [US7] Verificar testes passam e refatorar se necessário

**Checkpoint Foundational**: Base completa - US1, US2, US3, US4 podem iniciar

---

## Phase 3: User Story 1 - Painéis de Feedback Visual (P1)

**Goal**: Painéis estilizados (info, success, warning, error) com fallback

**Independent Test**: Importar `success_panel("msg", "title")` e renderizar no terminal

### Testes TDD (RED)

- [x] T033 [P] [US1] Criar teste `test_create_panel_basic` em `tests/unit/cli/shared/test_panels.py`
- [x] T034 [P] [US1] Criar teste `test_info_panel_style` em `tests/unit/cli/shared/test_panels.py`
- [x] T035 [P] [US1] Criar teste `test_success_panel_style` em `tests/unit/cli/shared/test_panels.py`
- [x] T036 [P] [US1] Criar teste `test_warning_panel_style` em `tests/unit/cli/shared/test_panels.py`
- [x] T037 [P] [US1] Criar teste `test_error_panel_style` em `tests/unit/cli/shared/test_panels.py`
- [x] T038 [P] [US1] Criar teste `test_panel_icon_fallback_ascii` em `tests/unit/cli/shared/test_panels.py`

### Implementação (GREEN)

- [x] T039 [US1] Implementar `create_panel()` em `src/cli/shared/ui/panels.py`
- [x] T040 [US1] Implementar `info_panel()` com estilo azul e ícone
- [x] T041 [US1] Implementar `success_panel()` com estilo verde e ícone
- [x] T042 [US1] Implementar `warning_panel()` com estilo âmbar e ícone
- [x] T043 [US1] Implementar `error_panel()` com estilo vermelho e ícone
- [x] T044 [US1] Implementar fallback ASCII para ícones quando `supports_unicode()=False`

### Refactor

- [x] T045 [US1] Verificar testes passam e refatorar para reduzir duplicação

**Checkpoint US1**: Painéis funcionam com cores e fallback

---

## Phase 4: User Story 2 - Spinners e Progress Bars (P1)

**Goal**: Indicadores de progresso para operações async/sync

**Independent Test**: `with spinner("msg"):` exibe animação e some ao completar

### Testes TDD (RED)

- [ ] T046 [P] [US2] Criar teste `test_spinner_context_manager` em `tests/unit/cli/shared/test_progress.py`
- [ ] T047 [P] [US2] Criar teste `test_spinner_non_interactive_fallback` em `tests/unit/cli/shared/test_progress.py`
- [ ] T048 [P] [US2] Criar teste `test_phase_dataclass_frozen` em `tests/unit/cli/shared/test_progress.py`
- [ ] T049 [P] [US2] Criar teste `test_phase_spinner_initial_state` em `tests/unit/cli/shared/test_progress.py`
- [ ] T050 [P] [US2] Criar teste `test_phase_spinner_advance` em `tests/unit/cli/shared/test_progress.py`
- [ ] T051 [P] [US2] Criar teste `test_phase_spinner_complete` em `tests/unit/cli/shared/test_progress.py`
- [ ] T052 [P] [US2] Criar teste `test_phase_spinner_fail` em `tests/unit/cli/shared/test_progress.py`
- [ ] T053 [P] [US2] Criar teste `test_phase_spinner_no_advance_past_end` em `tests/unit/cli/shared/test_progress.py`
- [ ] T054 [P] [US2] Criar teste `test_create_bar_progress` em `tests/unit/cli/shared/test_progress.py`

### Implementação (GREEN)

- [ ] T055 [US2] Implementar `Phase` dataclass em `src/cli/shared/ui/progress.py`
- [ ] T056 [US2] Implementar `create_spinner_progress()` factory
- [ ] T057 [US2] Implementar `create_bar_progress()` factory com barra, %, tempo
- [ ] T058 [US2] Implementar `spinner()` context manager com fallback non-interactive
- [ ] T059 [US2] Implementar `PhaseSpinner.__init__()` com lista de fases
- [ ] T060 [US2] Implementar `PhaseSpinner.live()` context manager com Rich Live
- [ ] T061 [US2] Implementar `PhaseSpinner.advance()` e `PhaseSpinner.complete()`
- [ ] T062 [US2] Implementar `PhaseSpinner.fail()` com mensagem opcional
- [ ] T063 [US2] Implementar fallback estático para terminais non-interactive

### Refactor

- [ ] T064 [US2] Verificar testes passam e refatorar PhaseSpinner se necessário

**Checkpoint US2**: Spinners animam, PhaseSpinner gerencia fases corretamente

---

## Phase 5: User Story 3 - Prompts Interativos (P1)

**Goal**: Prompts text/confirm/select/checkbox com estilo consistente

**Independent Test**: `ask_select("msg", ["A", "B"])` exibe lista navegável

### Testes TDD (RED)

- [ ] T065 [P] [US3] Criar teste `test_ask_text_returns_input` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T066 [P] [US3] Criar teste `test_ask_text_keyboard_interrupt_returns_none` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T067 [P] [US3] Criar teste `test_ask_confirm_returns_bool` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T068 [P] [US3] Criar teste `test_ask_confirm_keyboard_interrupt_returns_none` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T069 [P] [US3] Criar teste `test_ask_select_returns_choice` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T070 [P] [US3] Criar teste `test_ask_select_keyboard_interrupt_returns_none` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T071 [P] [US3] Criar teste `test_ask_checkbox_returns_list` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T072 [P] [US3] Criar teste `test_ask_checkbox_keyboard_interrupt_returns_none` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T073 [P] [US3] Criar teste `test_prompts_non_interactive_returns_none` em `tests/unit/cli/shared/test_prompts.py`

### Implementação (GREEN)

- [ ] T074 [US3] Implementar `ask_text()` em `src/cli/shared/ui/prompts.py` com estilo e Ctrl+C handling
- [ ] T075 [US3] Implementar `ask_confirm()` com estilo e Ctrl+C handling
- [ ] T076 [US3] Implementar `ask_select()` com estilo, instrução em português e Ctrl+C handling
- [ ] T077 [US3] Implementar `ask_checkbox()` com estilo, instrução em português e Ctrl+C handling
- [ ] T078 [US3] Implementar check `is_interactive()` retornando None se não-interativo

### Refactor

- [ ] T079 [US3] Verificar testes passam e extrair decorator para Ctrl+C handling se útil

**Checkpoint US3**: Prompts funcionam com estilo e tratam interrupção graciosamente

---

## Phase 6: User Story 4 - Prompt de Aprovação (P2)

**Goal**: Prompt especializado para workflows de revisão (approve/edit/reject/skip/cancel)

**Independent Test**: `ask_approval("item")` retorna `ApprovalResult.APPROVE`

### Testes TDD (RED)

- [ ] T080 [P] [US4] Criar teste `test_approval_result_enum_values` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T081 [P] [US4] Criar teste `test_approval_result_inherits_str` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T082 [P] [US4] Criar teste `test_ask_approval_all_options` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T083 [P] [US4] Criar teste `test_ask_approval_no_edit` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T084 [P] [US4] Criar teste `test_ask_approval_no_skip` em `tests/unit/cli/shared/test_prompts.py`
- [ ] T085 [P] [US4] Criar teste `test_ask_approval_keyboard_interrupt` em `tests/unit/cli/shared/test_prompts.py`

### Implementação (GREEN)

- [ ] T086 [US4] Implementar `ApprovalResult` enum em `src/cli/shared/ui/prompts.py`
- [ ] T087 [US4] Implementar `ask_approval()` com opções condicionais
- [ ] T088 [US4] Mapear seleção para `ApprovalResult` enum value

### Refactor

- [ ] T089 [US4] Verificar testes passam e refatorar se necessário

**Checkpoint US4**: `ask_approval()` pronto para uso em `02P-catalog-ai-enrichment`

---

## Phase 7: Integration & Exports

**Purpose**: Consolidar exports e verificar integração

- [ ] T090 Criar `src/cli/shared/ui/__init__.py` com todos os exports públicos
- [ ] T091 Criar `src/cli/shared/utils/__init__.py` com exports de terminal
- [ ] T092 Criar `src/cli/shared/__init__.py` com re-exports de ui e utils
- [ ] T093 [P] Criar teste `test_all_exports_importable` em `tests/unit/cli/shared/test_init.py`
- [ ] T094 Verificar `from src.cli.shared.ui import *` funciona sem erros

**Checkpoint**: Todos os componentes importáveis via módulo público

---

## Phase 8: Polish & Validation

**Purpose**: Qualidade, documentação e verificação manual

- [ ] T095 Executar `uv run ruff check src/cli/shared/ tests/unit/cli/shared/` - zero erros
- [ ] T096 [P] Executar `uv run mypy src/cli/shared/ tests/unit/cli/shared/` - zero erros
- [ ] T097 [P] Executar `uv run black src/cli/shared/ tests/unit/cli/shared/` - formatação ok
- [ ] T098 Executar `uv run pytest tests/unit/cli/shared/ -v` - todos os testes passam
- [ ] T099 [P] Verificação manual: painéis renderizam corretamente (60+ colunas)
- [ ] T100 [P] Verificação manual: spinners animam sem flicker
- [ ] T101 [P] Verificação manual: prompts respondem sem delay
- [ ] T102 [P] Verificação manual: `NO_COLOR=1` output legível
- [ ] T103 Atualizar docstrings conforme Google-style onde necessário

**Checkpoint Final**: Qualidade validada, pronto para merge

---

## Dependencies Graph

```
Phase 1: Setup
    T001 ─────────────────┐
    T002 ─────[P]─────────┼───► Phase 2
    T003 ─────[P]─────────┘

Phase 2: Foundational (US5 + US6 + US7)
    ┌─ US5: Theme ──────────────────────────────────────┐
    │  T004-T009 [P] tests ──► T010-T014 impl ──► T015  │
    ├───────────────────────────────────────────────────┤
    │  US6: Terminal                                     │
    │  T016-T021 [P] tests ──► T022-T025 impl ──► T026  │
    ├───────────────────────────────────────────────────┤
    │  US7: Console (depende de US5 e US6)              │
    │  T027-T029 [P] tests ──► T030-T031 impl ──► T032  │
    └───────────────────────────────────────────────────┘
            │
            ▼ (BLOCKS)
    ┌───────────────────────────────────────────────────┐
    │        Phases 3-6: User Stories (podem ser [P])   │
    ├───────────────────────────────────────────────────┤
    │                                                    │
    │  US1: Panels (P1)     US2: Progress (P1)          │
    │  T033-T038 tests      T046-T054 tests             │
    │  T039-T044 impl       T055-T063 impl              │
    │  T045 refactor        T064 refactor               │
    │         │                   │                      │
    │         └───────[P]─────────┘                      │
    │                                                    │
    │  US3: Prompts (P1)    US4: Approval (P2)          │
    │  T065-T073 tests      T080-T085 tests             │
    │  T074-T078 impl       T086-T088 impl              │
    │  T079 refactor        T089 refactor               │
    │         │                   │                      │
    │         └───────[P]─────────┘                      │
    │                                                    │
    └───────────────────────────────────────────────────┘
            │
            ▼
Phase 7: Integration
    T090-T094 ──► Phase 8

Phase 8: Polish
    T095-T103 ──► DONE
```

---

## Time Estimates

| Phase | Tasks | Estimativa |
|-------|-------|------------|
| Setup | T001-T003 | 30min |
| US5 Theme | T004-T015 | 1h |
| US6 Terminal | T016-T026 | 45min |
| US7 Console | T027-T032 | 30min |
| US1 Panels | T033-T045 | 1.5h |
| US2 Progress | T046-T064 | 2h |
| US3 Prompts | T065-T079 | 1.5h |
| US4 Approval | T080-T089 | 45min |
| Integration | T090-T094 | 30min |
| Polish | T095-T103 | 1h |
| **Total** | **103 tasks** | **~10h** |

---

## Implementation Strategy

### MVP First (P1 Stories)

1. Complete Setup (Phase 1)
2. Complete Foundational: US5 + US6 + US7 (Phase 2)
3. Complete US1: Panels (Phase 3)
4. Complete US2: Progress (Phase 4)
5. Complete US3: Prompts (Phase 5)
6. **STOP and VALIDATE**: Testar componentes P1 independentemente
7. Deploy se suficiente para `03P-cli-chat`

### Full Feature

1. Complete MVP (phases 1-5)
2. Complete US4: Approval (Phase 6) - necessário para `02P-catalog-ai-enrichment`
3. Complete Integration + Polish (Phases 7-8)
4. Merge para branch principal

### Parallel Opportunities

Com múltiplos desenvolvedores após Phase 2:
- Dev A: US1 (Panels) + US3 (Prompts)
- Dev B: US2 (Progress) + US4 (Approval)

---

## Success Criteria (from Spec)

- [ ] **SC-001**: 100% dos componentes importáveis via `from src.cli.shared.ui import *`
- [ ] **SC-002**: Zero erros de mypy/ruff/black
- [ ] **SC-003**: Testes unitários cobrem lógica crítica (PhaseSpinner, Ctrl+C)
- [ ] **SC-004**: Painéis renderizam em terminais 60+ colunas (manual)
- [ ] **SC-005**: Spinners animam sem flicker (manual)
- [ ] **SC-006**: Prompts respondem sem delay perceptível (manual)
- [ ] **SC-007**: Output legível com `NO_COLOR=1` (manual)
- [ ] **SC-008**: `ask_approval()` usável por plano 02P
- [ ] **SC-009**: Painéis/spinners usáveis por plano 03P

---

## Notes

- **[P]**: Tasks podem rodar em paralelo (arquivos diferentes, sem dependências)
- **[USx]**: Identifica qual User Story a task pertence
- **TDD Flow**: RED (testes falham) → GREEN (implementar) → REFACTOR (melhorar)
- Commit após cada checkpoint de User Story
- Verificações manuais agrupadas no final (Phase 8) para eficiência
