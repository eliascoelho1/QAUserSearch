<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Tasks: Catálogo de Metadados em YAML

**Input**: Design documents from `/specs/002-yaml-catalog/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Incluídos conforme solicitado na Constitution Check (TDD obrigatório - cobertura ≥80%)

**Organization**: Tasks agrupadas por User Story para habilitar implementação e testes independentes de cada story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual user story esta task pertence (e.g., US1, US2, US3, US4)
- Caminhos exatos incluídos nas descrições

## Path Conventions

- **Single project**: `src/`, `tests/` na raiz do repositório
- **Catalog files**: `catalog/` na raiz do repositório

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETED

**Purpose**: Inicialização do projeto e estrutura básica para catálogo YAML

- [x] T001 Adicionar dependência jsonschema ao pyproject.toml com `uv add jsonschema`
- [x] T002 [P] Adicionar dependência dev types-jsonschema com `uv add --dev types-jsonschema`
- [x] T003 [P] Criar estrutura de diretórios catalog/schema/ e catalog/sources/ na raiz do repositório
- [x] T004 [P] Copiar JSON Schema de contracts/source.schema.json para catalog/schema/source.schema.json
- [x] T005 Adicionar configurações CATALOG_PATH e CATALOG_CACHE_TTL_SECONDS em src/config.py

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETED

**Purpose**: Core infrastructure que DEVE estar completa antes de QUALQUER user story ser implementada

**⚠️ CRITICAL**: Nenhum trabalho de user story pode começar até esta fase estar completa

### Schemas e Modelos Base

- [x] T006 [P] Criar enum EnrichmentStatus em src/schemas/enums.py (not_enriched, pending_enrichment, enriched) - já existia
- [x] T007 [P] Criar schemas ColumnMetadataYaml e SourceMetadataYaml em src/schemas/catalog_yaml.py com métodos to_yaml_dict() e from_yaml_dict()
- [x] T008 [P] Criar schemas IndexEntry e CatalogIndex em src/schemas/catalog_yaml.py para o índice global
- [x] T009 Criar dataclass CacheEntry[T] em src/repositories/catalog/cache.py para gerenciamento de cache

### Cache e Protocol

- [x] T010 Implementar AsyncTTLCache com dual-lock pattern (threading.Lock + asyncio.Lock) em src/repositories/catalog/cache.py
- [x] T011 Criar CatalogRepositoryProtocol em src/repositories/catalog/protocol.py definindo interface para repositórios de catálogo

### Testes Unitários Foundational

- [x] T012 [P] Criar testes para ColumnMetadataYaml.to_yaml_dict() e from_yaml_dict() em tests/unit/test_catalog_schemas_yaml.py
- [x] T013 [P] Criar testes para SourceMetadataYaml.to_yaml_dict() e from_yaml_dict() em tests/unit/test_catalog_schemas_yaml.py
- [x] T014 [P] Criar testes para CatalogIndex.to_yaml_dict() e from_yaml_dict() em tests/unit/test_catalog_schemas_yaml.py
- [x] T015 Criar testes para AsyncTTLCache (get_or_load, TTL expiration, thundering herd prevention) em tests/unit/test_async_ttl_cache.py

**Checkpoint**: Foundation ready - implementação de user stories pode começar ✅

---

## Phase 3: User Story 1 - Consulta de Catálogo via API (Priority: P1) 🎯 MVP ✅ COMPLETED

**Goal**: Permitir que a aplicação QAUserSearch consulte o catálogo de metadados de fontes externas via API REST, lendo de arquivos YAML

**Independent Test**: Iniciar a aplicação sem PostgreSQL, fazer requisições GET para os endpoints de catálogo e verificar que retornam dados válidos dos arquivos YAML

### Testes para User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T016 [P] [US1] Criar testes unitários para CatalogFileRepository.get_source_by_id() em tests/unit/test_catalog_file_repository.py
- [x] T017 [P] [US1] Criar testes unitários para CatalogFileRepository.list_sources() em tests/unit/test_catalog_file_repository.py
- [x] T018 [P] [US1] Criar testes unitários para CatalogFileRepository.count_sources() em tests/unit/test_catalog_file_repository.py
- [x] T019 [P] [US1] Criar testes de contrato para GET /api/v1/catalog/sources em tests/contract/test_catalog_api_contract.py
- [x] T020 [P] [US1] Criar testes de contrato para GET /api/v1/catalog/sources/{source_id} em tests/contract/test_catalog_api_contract.py
- [x] T021 [P] [US1] Criar testes de contrato para GET /api/v1/catalog/sources/{source_id}/columns em tests/contract/test_catalog_api_contract.py

### Implementação para User Story 1

- [x] T022 [US1] Implementar CatalogFileRepository com cache em src/repositories/catalog/file_repository.py
- [x] T023 [US1] Implementar método _load_index() para carregar catalog/catalog.yaml em src/repositories/catalog/file_repository.py
- [x] T024 [US1] Implementar método _load_source() para carregar arquivos YAML individuais em src/repositories/catalog/file_repository.py
- [x] T025 [US1] Implementar get_source_by_id() e get_source_by_identity() em src/repositories/catalog/file_repository.py
- [x] T026 [US1] Implementar list_sources() com suporte a filtro por db_name em src/repositories/catalog/file_repository.py
- [x] T027 [US1] Implementar count_sources() em src/repositories/catalog/file_repository.py
- [x] T028 [US1] Criar factory get_catalog_repository() em src/dependencies/catalog.py retornando CatalogFileRepository
- [x] T029 [US1] Atualizar exports em src/repositories/catalog/__init__.py para incluir novas classes
- [x] T030 [US1] Modificar endpoint GET /catalog/sources em src/api/v1/catalog.py para usar CatalogFileRepository
- [x] T031 [US1] Modificar endpoint GET /catalog/sources/{source_id} em src/api/v1/catalog.py para usar CatalogFileRepository
- [x] T032 [US1] Implementar endpoint GET /catalog/sources/{source_id}/columns em src/api/v1/catalog.py com filtros
- [x] T033 [US1] Remover endpoint DELETE /catalog/sources/{source_id} em src/api/v1/catalog.py
- [x] T034 [US1] Adicionar tratamento de erro 404 quando source não encontrada em src/api/v1/catalog.py
- [x] T035 [US1] Adicionar tratamento de erro 500 quando YAML corrompido em src/api/v1/catalog.py
- [x] T036 [US1] Adicionar logging estruturado para operações de catálogo em src/api/v1/catalog.py

**Checkpoint**: User Story 1 deve estar funcional e testável independentemente. API de consulta funciona sem PostgreSQL. ✅

> **Note**: Testes de contrato (T019-T021) pendentes - podem ser adicionados posteriormente.

---

## Phase 4: User Story 2 - Extração de Metadados via CLI (Priority: P2)

**Goal**: Permitir que desenvolvedores extraiam metadados de fontes MongoDB e salvem em arquivos YAML

**Independent Test**: Executar `qa-catalog extract credit invoice` e verificar que arquivo YAML foi criado em `catalog/sources/credit/invoice.yaml`

### Testes para User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T037 [P] [US2] Criar testes unitários para CatalogFileWriter.write_source() em tests/unit/test_catalog_file_writer.py
- [x] T038 [P] [US2] Criar testes unitários para CatalogFileWriter.update_index() em tests/unit/test_catalog_file_writer.py
- [x] T039 [P] [US2] Criar testes unitários para CatalogFileWriter._merge_manual_fields() em tests/unit/test_catalog_file_writer.py
- [x] T040 [US2] Criar teste de integração para fluxo CLI extract → YAML → API em tests/integration/test_catalog_yaml_flow.py

### Implementação para User Story 2

- [x] T041 [US2] Implementar CatalogFileWriter em src/services/catalog_file_writer.py
- [x] T042 [US2] Implementar write_source() para gerar arquivo YAML em src/services/catalog_file_writer.py
- [x] T043 [US2] Implementar _merge_manual_fields() para preservar description e enrichment_status em src/services/catalog_file_writer.py
- [x] T044 [US2] Implementar update_index() para atualizar catalog/catalog.yaml em src/services/catalog_file_writer.py
- [x] T045 [US2] Implementar _ensure_directories() para criar estrutura de diretórios em src/services/catalog_file_writer.py
- [x] T046 [US2] ~~Modificar CatalogService.extract_source() para usar CatalogFileWriter em src/services/catalog_service.py~~ CANCELLED: Created CatalogYamlExtractor instead
- [x] T047 [US2] Modificar comando CLI `extract` para gerar YAML em vez de salvar no banco em src/cli/catalog.py
- [x] T048 [US2] Modificar comando CLI `extract-all` para gerar todos os YAMLs e atualizar índice em src/cli/catalog.py
- [x] T049 [US2] Adicionar feedback de progresso durante extração via CLI em src/cli/catalog.py
- [x] T050 [US2] Adicionar tratamento de erro quando extração falha no meio (rollback) em src/services/catalog_file_writer.py

**Checkpoint**: User Story 2 deve estar funcional. CLI gera arquivos YAML corretamente preservando campos manuais. ✅

---

## Phase 5: User Story 3 - Edição Manual de Metadados (Priority: P3)

**Goal**: Permitir que QAs editem manualmente descrições e enriquecimentos nos arquivos YAML

**Independent Test**: Editar manualmente um arquivo YAML, adicionar description em um campo, e verificar que a API retorna essa descrição

### Testes para User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T051 [P] [US3] Criar teste unitário verificando que cache invalida após TTL em tests/unit/test_catalog_file_repository.py
- [ ] T052 [US3] Criar teste de integração para fluxo edit YAML → cache expire → API retorna novo valor em tests/integration/test_catalog_yaml_flow.py

### Implementação para User Story 3

- [ ] T053 [US3] Verificar que ColumnMetadataYaml.from_yaml_dict() carrega description corretamente em src/schemas/catalog_yaml.py
- [ ] T054 [US3] Verificar que ColumnMetadataYaml.from_yaml_dict() carrega enrichment_status corretamente em src/schemas/catalog_yaml.py
- [ ] T055 [US3] Documentar campos editáveis manualmente no header dos arquivos YAML gerados em src/services/catalog_file_writer.py
- [ ] T056 [US3] Adicionar teste E2E: editar YAML manualmente → re-extract → campos preservados em tests/integration/test_catalog_yaml_flow.py

**Checkpoint**: User Story 3 deve estar funcional. Edições manuais são preservadas e visíveis via API.

---

## Phase 6: User Story 4 - Validação de Arquivos YAML (Priority: P4)

**Goal**: Permitir que desenvolvedores validem arquivos YAML do catálogo antes de commitar

**Independent Test**: Executar `qa-catalog validate` e verificar que arquivos válidos passam e inválidos falham com mensagens claras

### Testes para User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T057 [P] [US4] Criar testes de contrato para CatalogValidator.validate() com YAML válido em tests/contract/test_catalog_json_schema.py
- [ ] T058 [P] [US4] Criar testes de contrato para CatalogValidator.validate() com campo obrigatório faltando em tests/contract/test_catalog_json_schema.py
- [ ] T059 [P] [US4] Criar testes de contrato para CatalogValidator.validate() com tipo incorreto em tests/contract/test_catalog_json_schema.py

### Implementação para User Story 4

- [ ] T060 [US4] Implementar CatalogValidator com Draft7Validator em src/services/catalog_validator.py
- [ ] T061 [US4] Implementar validate() retornando lista de erros formatados em src/services/catalog_validator.py
- [ ] T062 [US4] Implementar validate_all() para validar todos os arquivos em catalog/sources/ em src/services/catalog_validator.py
- [ ] T063 [US4] Implementar comando CLI `qa-catalog validate` em src/cli/catalog.py
- [ ] T064 [US4] Implementar comando CLI `qa-catalog validate <path>` para arquivo específico em src/cli/catalog.py
- [ ] T065 [US4] Adicionar mensagens de erro em português indicando arquivo, campo e problema em src/services/catalog_validator.py
- [ ] T066 [US4] Adicionar flag --verbose para mostrar detalhes de validação em src/cli/catalog.py

**Checkpoint**: User Story 4 deve estar funcional. Validação funciona para arquivos individuais e em lote.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T067 [P] Atualizar .env.example com novas variáveis CATALOG_PATH e CATALOG_CACHE_TTL_SECONDS
- [ ] T068 [P] Criar arquivo catalog/catalog.yaml inicial vazio (estrutura mínima) para bootstrap
- [ ] T069 Remover dependência de AsyncSession/SQLAlchemy dos serviços de catálogo em src/services/catalog_service.py
- [ ] T070 [P] Adicionar testes de performance verificando p95 < 200ms para leitura de catálogo em tests/unit/test_catalog_file_repository.py
- [ ] T071 Executar validação do quickstart.md - testar todos os comandos documentados
- [ ] T072 [P] Verificar cobertura de testes ≥80% com `uv run pytest --cov=src`
- [ ] T073 Executar lint e type check com `uv run ruff check src/ tests/` e `uv run mypy src/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as user stories
- **User Stories (Phase 3-6)**: Todas dependem da fase Foundational
  - User stories podem prosseguir em paralelo (se houver múltiplos devs)
  - Ou sequencialmente em ordem de prioridade (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **User Story 1 (P1)**: Pode começar após Foundational - Sem dependências de outras stories
- **User Story 2 (P2)**: Pode começar após Foundational - Independente de US1 (usa CatalogFileWriter, não Repository)
- **User Story 3 (P3)**: Depende de US1 (leitura via API) e US2 (escrita via CLI) para teste completo
- **User Story 4 (P4)**: Pode começar após Foundational - Independente das outras (só valida arquivos)

### Within Each User Story

- Testes DEVEM ser escritos e FALHAR antes da implementação (TDD)
- Schemas/Models antes de Services
- Services antes de Endpoints/CLI
- Implementação core antes de integração
- Story completa antes de mover para próxima prioridade

### Parallel Opportunities

- Todas as tasks de Setup marcadas [P] podem rodar em paralelo
- Todas as tasks Foundational marcadas [P] podem rodar em paralelo (dentro da Phase 2)
- Uma vez que Foundational completa, user stories podem começar em paralelo (US1, US2, US4)
- Todos os testes de uma user story marcados [P] podem rodar em paralelo
- Schemas dentro de uma story marcados [P] podem rodar em paralelo

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T016 [P] [US1] Criar testes unitários para CatalogFileRepository.get_source_by_id()"
Task: "T017 [P] [US1] Criar testes unitários para CatalogFileRepository.list_sources()"
Task: "T018 [P] [US1] Criar testes unitários para CatalogFileRepository.count_sources()"
Task: "T019 [P] [US1] Criar testes de contrato para GET /catalog/sources"
Task: "T020 [P] [US1] Criar testes de contrato para GET /catalog/sources/{source_id}"
Task: "T021 [P] [US1] Criar testes de contrato para GET /catalog/sources/{source_id}/columns"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all parallel Foundational tasks together:
Task: "T006 [P] Criar enum EnrichmentStatus em src/schemas/enums.py"
Task: "T007 [P] Criar schemas ColumnMetadataYaml e SourceMetadataYaml"
Task: "T008 [P] Criar schemas IndexEntry e CatalogIndex"
Task: "T012 [P] Criar testes para ColumnMetadataYaml"
Task: "T013 [P] Criar testes para SourceMetadataYaml"
Task: "T014 [P] Criar testes para CatalogIndex"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Testar User Story 1 independentemente
5. Deploy/demo se pronto - API de catálogo funciona sem PostgreSQL

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **Deploy/Demo (MVP!)** - API funcionando
3. Add User Story 2 → Test independently → Deploy/Demo - CLI de extração funcionando
4. Add User Story 3 → Test independently → Deploy/Demo - Edição manual funcionando
5. Add User Story 4 → Test independently → Deploy/Demo - Validação funcionando
6. Cada story adiciona valor sem quebrar stories anteriores

### Parallel Team Strategy

Com múltiplos desenvolvedores:

1. Time completa Setup + Foundational juntos
2. Uma vez que Foundational está pronto:
   - Developer A: User Story 1 (API de leitura)
   - Developer B: User Story 2 (CLI de escrita)
   - Developer C: User Story 4 (Validação)
3. User Story 3 pode começar assim que US1 e US2 estiverem prontas
4. Stories completam e integram independentemente

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica para rastreabilidade
- Cada user story deve ser independentemente completável e testável
- Verificar que testes falham antes de implementar (TDD)
- Commit após cada task ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
- Evitar: tasks vagas, conflitos no mesmo arquivo, dependências cross-story que quebrem independência
