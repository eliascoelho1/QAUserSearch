# Tasks: Enriquecimento Semantico do Catalogo com IA

**Input**: Design documents from [spec.md](spec.md) and [plan.md](plan.md)
**Prerequisites**: plan.md (OK), spec.md (OK)

**Tests**: Testes sao OBRIGATORIOS conforme Constitution (TDD mandatorio, cobertura >= 80%)

**Organization**: Tasks agrupadas por user story para implementacao e teste independentes.

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Estrutura de diretorios e validacao de dependencias

- [ ] T001 Criar estrutura de diretorios `src/services/enrichment/` com `__init__.py`
- [ ] T002 [P] Criar estrutura de diretorios `src/cli/enrichment/` com `__init__.py`
- [ ] T003 [P] Criar estrutura de diretorios `tests/unit/services/enrichment/` com `__init__.py`
- [ ] T004 [P] Verificar dependencias existentes (httpx, rich, questionary, typer) em `pyproject.toml`

---

## Phase 2: Foundational - Schemas e Contratos (User Story 3 - P1)

**Purpose**: Atualizar schemas e infraestrutura para suportar novos campos semanticos

**Goal**: Todos os schemas (Pydantic + JSON Schema) validam corretamente os novos campos semanticos

**Independent Test**: `uv run qa-catalog validate` passa com YAMLs contendo novos campos

### Testes para User Story 3 (TDD - escrever PRIMEIRO)

- [ ] T005 [P] [US3] Criar teste unitario para `DomainCategory` enum em `tests/unit/schemas/test_enums.py`
- [ ] T006 [P] [US3] Criar teste unitario para `FieldEnrichment` em `tests/unit/schemas/test_enrichment.py`
- [ ] T007 [P] [US3] Criar teste unitario para `EnrichmentRequest` em `tests/unit/schemas/test_enrichment.py`
- [ ] T008 [P] [US3] Criar teste unitario para `EnrichmentResult` em `tests/unit/schemas/test_enrichment.py`
- [ ] T009 [P] [US3] Criar teste de serializacao/deserializacao para `ColumnMetadataYaml` com novos campos em `tests/unit/schemas/test_catalog_yaml.py`
- [ ] T010 [P] [US3] Criar teste de contrato para JSON Schema atualizado em `tests/contract/test_enrichment_schema.py`

### Implementacao para User Story 3

- [ ] T011 [US3] Adicionar enum `DomainCategory` em `src/schemas/enums.py` com valores: `status`, `financial`, `temporal`, `identification`, `configuration`
- [ ] T012 [US3] Criar `src/schemas/enrichment.py` com `FieldEnrichment`, `EnrichmentRequest`, `EnrichmentResult`, `EnrichmentStatus`
- [ ] T013 [US3] Estender `ColumnMetadataYaml` em `src/schemas/catalog_yaml.py` com campos semanticos opcionais
- [ ] T014 [US3] Atualizar metodos `to_yaml_dict()` e `from_yaml_dict()` para suportar novos campos
- [ ] T015 [US3] Atualizar `catalog/schema/source.schema.json` com novas propriedades semanticas
- [ ] T016 [US3] Adicionar configs de enrichment em `src/config/config.py` (timeout, max_synonyms, etc.)

**Checkpoint**: Schemas validam, testes unitarios passam, `uv run qa-catalog validate` funciona

---

## Phase 3: User Story 4 - Servico de Enriquecimento LLM (P1) - MVP Core

**Goal**: Servico robusto que chama OpenAI API com retry e validacao

**Independent Test**: `LLMEnricher.enrich_field()` retorna `FieldEnrichment` valido para campo de teste com mock da API

### Testes para User Story 4 (TDD - escrever PRIMEIRO)

- [ ] T017 [P] [US4] Criar teste unitario para `prompts.py` em `tests/unit/services/enrichment/test_prompts.py`
- [ ] T018 [P] [US4] Criar teste unitario para `ContextBuilder` em `tests/unit/services/enrichment/test_context_builder.py`
- [ ] T019 [P] [US4] Criar teste unitario para `FieldSelector` em `tests/unit/services/enrichment/test_field_selector.py`
- [ ] T020 [P] [US4] Criar teste unitario para `EnrichmentValidator` em `tests/unit/services/enrichment/test_validator.py`
- [ ] T021 [P] [US4] Criar teste unitario para `LLMEnricher` com mock da API em `tests/unit/services/enrichment/test_llm_enricher.py`
- [ ] T022 [US4] Criar teste de integracao para fluxo completo em `tests/integration/test_enrichment_flow.py`

### Implementacao para User Story 4

- [ ] T023 [US4] Implementar `src/services/enrichment/prompts.py` com templates de prompt
- [ ] T024 [US4] Implementar `src/services/enrichment/context_builder.py` com carga de docs de `docs/context/`
- [ ] T025 [US4] Implementar `src/services/enrichment/field_selector.py` com filtros de prioridade
- [ ] T026 [US4] Implementar `src/services/enrichment/validator.py` com validacoes (max chars, max synonyms, etc.)
- [ ] T027 [US4] Implementar `src/services/enrichment/llm_enricher.py` com client async, retry e timeout
- [ ] T028 [US4] Atualizar `src/services/enrichment/__init__.py` com exports publicos

**Checkpoint**: Servico LLM funciona com mock, testes unitarios e de integracao passam

---

## Phase 4: User Story 1 - Enriquecimento Individual via CLI (P1) - MVP Core

**Goal**: CLI interativo para enriquecer campos de uma tabela especifica

**Independent Test**: `uv run qa-catalog enrich credit invoice` executa e YAML e atualizado corretamente

### Testes para User Story 1 (TDD - escrever PRIMEIRO)

- [ ] T029 [P] [US1] Criar teste unitario para `EnrichmentPanel` em `tests/unit/cli/enrichment/test_panels.py`
- [ ] T030 [P] [US1] Criar teste de integracao para comando `enrich` com mock de input em `tests/integration/test_cli_enrich.py`

### Implementacao para User Story 1

- [ ] T031 [US1] Implementar `src/cli/enrichment/panels.py` com `EnrichmentPanel.render_enrichment()`
- [ ] T032 [US1] Adicionar comando `enrich` em `src/cli/catalog.py` com args: db_name, table_name, --fields, --auto-approve, --force, --model
- [ ] T033 [US1] Implementar fluxo interativo com `ask_approval()` (aprovar, editar, rejeitar, pular, cancelar)
- [ ] T034 [US1] Implementar edicao inline de `description` e `enum_meanings`
- [ ] T035 [US1] Implementar salvamento YAML com backup automatico
- [ ] T036 [US1] Implementar exibicao de resumo apos enriquecimento

**Checkpoint**: Usuario pode enriquecer `credit.invoice` interativamente, aprovar/editar campos

---

## Phase 5: User Story 2 - Validacao Interativa de Enriquecimento (P1)

**Goal**: Revisao e edicao dos enriquecimentos gerados pela IA

**Independent Test**: Simulando input do usuario, edicoes sao aplicadas corretamente no YAML

### Testes para User Story 2 (TDD - escrever PRIMEIRO)

- [ ] T037 [P] [US2] Criar teste unitario para opcoes de edicao em `tests/unit/cli/enrichment/test_edit_flow.py`
- [ ] T038 [US2] Criar teste de integracao para fluxo de edicao completo em `tests/integration/test_cli_edit.py`

### Implementacao para User Story 2

- [ ] T039 [US2] Implementar editor de `description` com validacao de max 100 chars
- [ ] T040 [US2] Implementar editor de `enum_meanings` com tabela interativa
- [ ] T041 [US2] Implementar opcao "Rejeitar" que marca campo como `pending_enrichment`
- [ ] T042 [US2] Implementar opcao "Pular" que mantem `not_enriched` e continua

**Checkpoint**: Usuario pode editar qualquer campo do enriquecimento interativamente

---

## Phase 6: User Story 5 - Visualizacao de Status (P2)

**Goal**: Visualizar progresso de enriquecimento do catalogo

**Independent Test**: `uv run qa-catalog enrich-status` exibe tabela formatada com progresso

### Testes para User Story 5 (TDD - escrever PRIMEIRO)

- [ ] T043 [P] [US5] Criar teste unitario para comando `enrich-status` em `tests/unit/cli/test_enrich_status.py`
- [ ] T044 [P] [US5] Criar teste unitario para comando `enrich-pending` em `tests/unit/cli/test_enrich_pending.py`

### Implementacao para User Story 5

- [ ] T045 [US5] Implementar comando `enrich-status` em `src/cli/catalog.py` com tabela rich
- [ ] T046 [US5] Implementar calculo de progresso (total, enriched, %)
- [ ] T047 [US5] Implementar comando `enrich-pending` com lista agrupada por tabela

**Checkpoint**: Usuario visualiza progresso de todas as tabelas do catalogo

---

## Phase 7: User Story 6 - Enriquecimento em Batch (P2)

**Goal**: Enriquecer todas as tabelas de uma vez

**Independent Test**: `uv run qa-catalog enrich-all --priority-only` processa multiplas tabelas

### Testes para User Story 6 (TDD - escrever PRIMEIRO)

- [ ] T048 [P] [US6] Criar teste unitario para comando `enrich-all` em `tests/unit/cli/test_enrich_all.py`
- [ ] T049 [US6] Criar teste de integracao para batch processing em `tests/integration/test_batch_enrich.py`

### Implementacao para User Story 6

- [ ] T050 [US6] Implementar comando `enrich-all` em `src/cli/catalog.py` com args: --auto-approve, --priority-only, --batch-size
- [ ] T051 [US6] Implementar loop de processamento com pausa por batch
- [ ] T052 [US6] Implementar exibicao de progresso em tempo real

**Checkpoint**: Usuario pode enriquecer todas as tabelas em batch

---

## Phase 8: User Story 7 - Documentacao de Contexto (P3)

**Goal**: Criar documentacao de contexto para melhorar qualidade de enriquecimentos

**Independent Test**: `ContextBuilder` injeta conteudo de `docs/context/*.md` nos prompts

### Testes para User Story 7 (TDD - escrever PRIMEIRO)

- [ ] T053 [P] [US7] Criar teste unitario para carga de documentos de contexto em `tests/unit/services/enrichment/test_context_loader.py`

### Implementacao para User Story 7

- [ ] T054 [P] [US7] Criar `docs/context/invoice_status.md` com descricao de status de fatura
- [ ] T055 [P] [US7] Criar `docs/context/account_types.md` com tipos de conta
- [ ] T056 [US7] Atualizar `ContextBuilder` para carregar docs relevantes baseado em nome de tabela

**Checkpoint**: Enriquecimentos com contexto sao mais precisos

---

## Phase 9: Polish & Validacao Final

**Purpose**: Validacao final, documentacao e cleanup

- [ ] T057 Executar `uv run mypy src/ tests/` e corrigir erros
- [ ] T058 Executar `uv run ruff check src/ tests/ --fix` e corrigir warnings
- [ ] T059 Executar `uv run pytest --cov=src` e verificar cobertura >= 80%
- [ ] T060 Executar `uv run pytest tests/contract/` para validar contratos
- [ ] T061 [P] Atualizar AGENTS.md com novos comandos de enriquecimento
- [ ] T062 [P] Atualizar README.md com secao de enriquecimento do catalogo
- [ ] T063 Realizar teste manual completo: enriquecer `credit.invoice` end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sem dependencias - pode iniciar imediatamente
- **Phase 2 (Schemas)**: Depende de Phase 1 - BLOQUEIA todas as outras phases
- **Phase 3 (Servico LLM)**: Depende de Phase 2 - Core do sistema
- **Phase 4 (CLI enrich)**: Depende de Phase 2 e 3 - Core do MVP
- **Phase 5 (Validacao)**: Depende de Phase 4 - Extensao do CLI
- **Phase 6 (Status)**: Depende de Phase 2 - Pode rodar em paralelo com Phase 4/5
- **Phase 7 (Batch)**: Depende de Phase 4 - Extensao do CLI
- **Phase 8 (Contexto)**: Depende de Phase 3 - Pode rodar em paralelo com Phase 4-7
- **Phase 9 (Polish)**: Depende de todas as outras phases

### Ordem de Implementacao Sugerida

```
Week 1:
  Phase 1 (Setup) → Phase 2 (Schemas) → Phase 3 (Servico LLM)
  
Week 2:
  Phase 4 (CLI enrich) → Phase 5 (Validacao)
  
Week 3:
  Phase 6 (Status) || Phase 7 (Batch) || Phase 8 (Contexto)
  
Week 4:
  Phase 9 (Polish) → Teste final → Deploy
```

### Parallel Opportunities

- T001-T004: Todas podem rodar em paralelo
- T005-T010: Todos os testes de schema podem rodar em paralelo
- T017-T021: Todos os testes do servico podem rodar em paralelo
- T029-T030, T037-T038, T043-T044, T048: Testes de CLI podem rodar em paralelo
- T054-T055: Docs de contexto podem ser criados em paralelo

---

## Checkpoints de Validacao

| Checkpoint | Criterio | Comando de Validacao |
|------------|----------|---------------------|
| CP1 | Schemas validam | `uv run pytest tests/unit/schemas/ && uv run qa-catalog validate` |
| CP2 | Servico LLM funciona com mock | `uv run pytest tests/unit/services/enrichment/` |
| CP3 | CLI enrich funciona | `uv run qa-catalog enrich credit invoice --fields status` |
| CP4 | Status e batch funcionam | `uv run qa-catalog enrich-status` |
| CP5 | Cobertura >= 80% | `uv run pytest --cov=src --cov-fail-under=80` |
| CP6 | Zero erros mypy/ruff | `uv run mypy src/ && uv run ruff check src/` |

---

## Notas

- [P] = Podem rodar em paralelo (arquivos diferentes, sem dependencias)
- [USn] = Pertence a User Story n para rastreabilidade
- TDD obrigatorio: escrever testes PRIMEIRO, verificar que FALHAM, depois implementar
- Commit apos cada tarefa ou grupo logico
- Parar em qualquer checkpoint para validar independentemente
