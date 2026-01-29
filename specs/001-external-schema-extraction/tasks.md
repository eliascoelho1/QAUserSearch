<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este documento está em PORTUGUÊS BRASILEIRO.                   ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Tasks: Extração Automática de Schema de Bancos Externos

**Input**: Design documents from `/specs/001-external-schema-extraction/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Não solicitados explicitamente - tarefas de teste NÃO incluídas.

**Organization**: Tasks agrupadas por user story para implementação e teste independente de cada história.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story a que pertence (US1, US2, US3, US4)
- Inclui caminhos exatos de arquivo nas descrições

## Path Conventions

- **Single project**: `src/`, `tests/` na raiz do repositório
- Estrutura definida em plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização do projeto e estrutura básica

- [ ] T001 Adicionar dependências `openai>=1.0.0` e `motor>=3.3.0` em pyproject.toml
- [ ] T002 Criar diretório src/models/catalog/ para entidades do catálogo
- [ ] T003 [P] Criar diretório src/repositories/ para implementação Repository pattern
- [ ] T004 [P] Atualizar src/config.py com novas variáveis: DATA_ENVIRONMENT, SCHEMA_SAMPLE_SIZE, ENUMERABLE_CARDINALITY_LIMIT, REQUIRED_FIELD_THRESHOLD, OPENAI_MODEL, LLM_MAX_RETRIES
- [ ] T005 [P] Criar arquivo .env.example com variáveis documentadas em quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura core que DEVE estar completa antes de QUALQUER user story

**⚠️ CRITICAL**: Nenhum trabalho de user story pode começar até esta fase estar completa

- [ ] T006 Criar enums ExtractionStatus, EnrichmentStatus, InferredType em src/models/catalog/enums.py
- [ ] T007 Criar modelo ExternalSource em src/models/catalog/external_source.py (entidade do data-model.md)
- [ ] T008 Criar modelo ColumnMetadata em src/models/catalog/column_metadata.py (entidade do data-model.md)
- [ ] T009 [P] Criar exceções de domínio em src/core/exceptions.py: SourceNotFoundError, ExtractionInProgressError, EnrichmentError
- [ ] T010 Criar migration 001_create_catalog_tables.sql com script do data-model.md em scripts/ ou alembic/versions/
- [ ] T011 Criar interface abstrata ExternalDataRepository em src/repositories/base.py (conforme research.md)
- [ ] T012 [P] Criar MockDataRepository em src/repositories/mock_data_repository.py implementando interface de base.py
- [ ] T013 [P] Criar MongoDataRepository em src/repositories/mongo_data_repository.py implementando interface de base.py
- [ ] T014 Criar factory get_repository() em src/repositories/base.py para seleção de ambiente MOCK/PROD
- [ ] T015 Criar CatalogRepository em src/repositories/catalog_repository.py para operações CRUD no PostgreSQL

**Checkpoint**: Fundação pronta - implementação de user stories pode começar em paralelo

---

## Phase 3: User Story 1 - Descoberta Automática de Schema (Priority: P1) 🎯 MVP

**Goal**: Extrair automaticamente a estrutura de dados de tabelas externas a partir de amostras JSON

**Independent Test**: Fornecer arquivo JSON de amostra e verificar se o schema extraído contém todos os campos com tipos corretos inferidos

### Implementation for User Story 1

- [ ] T016 [P] [US1] Criar DTOs ExtractionRequest, ExtractionStartedResponse, ExtractionStatusResponse em src/schemas/schema_extraction.py (conforme contracts/schema-api.yaml)
- [ ] T017 [US1] Implementar lógica de inferência de tipos com TYPE_PRIORITY em src/services/schema_extractor.py (conforme research.md)
- [ ] T018 [US1] Implementar detecção de campos obrigatórios/opcionais (threshold 95%) em src/services/schema_extractor.py
- [ ] T019 [US1] Implementar detecção de colunas enumeráveis por cardinalidade em src/services/schema_extractor.py (FR-025 a FR-029)
- [ ] T020 [US1] Implementar flatten_schema() para estruturas aninhadas com dot notation em src/services/schema_extractor.py
- [ ] T021 [US1] Implementar endpoint POST /extraction em src/api/routes/schema.py (operationId: startExtraction)
- [ ] T022 [US1] Implementar endpoint GET /extraction/{source_id}/status em src/api/routes/schema.py (operationId: getExtractionStatus)
- [ ] T023 [US1] Adicionar validação de padrão de nomenclatura {db_name}.{table_name}.json para arquivos mock
- [ ] T024 [US1] Adicionar logging estruturado com structlog para operações de extração

**Checkpoint**: User Story 1 deve estar funcional e testável independentemente

---

## Phase 4: User Story 2 - Persistência de Schemas no Catálogo Local (Priority: P1)

**Goal**: Persistir schemas extraídos no PostgreSQL local em formato estruturado

**Independent Test**: Verificar que após a extração, as tabelas do catálogo no PostgreSQL contêm os metadados esperados

### Implementation for User Story 2

- [ ] T025 [P] [US2] Criar DTOs SourceSummary, SourceDetailResponse, PaginatedSourcesResponse em src/schemas/catalog.py
- [ ] T026 [P] [US2] Criar DTOs ColumnMetadataResponse, ColumnsResponse em src/schemas/catalog.py
- [ ] T027 [US2] Implementar CatalogService.save_schema() para persistir schema extraído em src/services/catalog_service.py
- [ ] T028 [US2] Implementar CatalogService.update_schema() para re-extração preservando ou sobrescrevendo em src/services/catalog_service.py (FR-008)
- [ ] T029 [US2] Implementar lógica de identificação única db_name + table_name em src/services/catalog_service.py
- [ ] T030 [US2] Integrar SchemaExtractor com CatalogService para persistência automática após extração
- [ ] T031 [US2] Adicionar atualização de total_columns e enriched_columns em ExternalSource
- [ ] T032 [US2] Adicionar logging para operações de persistência no catálogo

**Checkpoint**: User Stories 1 E 2 devem funcionar independentemente

---

## Phase 5: User Story 3 - Enriquecimento de Metadados via LLM (Priority: P2)

**Goal**: LLM analisa schemas e gera descrições semânticas para cada coluna

**Independent Test**: Enviar schema para LLM e verificar se descrições coerentes são geradas para cada coluna

### Implementation for User Story 3

- [ ] T033 [P] [US3] Criar DTOs EnrichmentRequest, EnrichmentStartedResponse, EnrichmentRetryResponse em src/schemas/schema_extraction.py
- [ ] T034 [US3] Implementar integração com OpenAI SDK em src/services/schema_enricher.py
- [ ] T035 [US3] Implementar prompt ENRICHMENT_PROMPT conforme research.md em src/services/schema_enricher.py
- [ ] T036 [US3] Implementar batch processing de colunas para reduzir chamadas API em src/services/schema_enricher.py
- [ ] T037 [US3] Implementar fallback com status pending_enrichment quando LLM falhar (FR-023)
- [ ] T038 [US3] Implementar retry automático com exponential backoff (MAX_RETRY_ATTEMPTS=3) em src/services/schema_enricher.py
- [ ] T039 [US3] Implementar endpoint POST /enrichment em src/api/routes/schema.py (operationId: startEnrichment)
- [ ] T040 [US3] Implementar endpoint POST /enrichment/retry em src/api/routes/schema.py (operationId: retryEnrichment)
- [ ] T041 [US3] Atualizar CatalogService para salvar descrições e status de enriquecimento
- [ ] T042 [US3] Adicionar logging para operações de enriquecimento (sucesso, falha, retry)

**Checkpoint**: User Story 3 deve funcionar independentemente (com User Stories 1 e 2)

---

## Phase 6: User Story 4 - Interface de Consulta ao Catálogo (Priority: P3)

**Goal**: Consultar catálogo de schemas para entender dados disponíveis nas fontes externas

**Independent Test**: Acessar endpoint que lista schemas disponíveis com suas colunas e descrições

### Implementation for User Story 4

- [ ] T043 [P] [US4] Criar DTO CatalogSearchResponse em src/schemas/catalog.py
- [ ] T044 [US4] Implementar CatalogService.list_sources() com filtros e paginação em src/services/catalog_service.py
- [ ] T045 [US4] Implementar CatalogService.get_source_detail() em src/services/catalog_service.py
- [ ] T046 [US4] Implementar CatalogService.list_columns() com filtros (is_required, is_enumerable, enrichment_status) em src/services/catalog_service.py
- [ ] T047 [US4] Implementar CatalogService.search_catalog() para busca por termo em src/services/catalog_service.py
- [ ] T048 [US4] Implementar endpoint GET /sources em src/api/routes/schema.py (operationId: listSources)
- [ ] T049 [US4] Implementar endpoint GET /sources/{source_id} em src/api/routes/schema.py (operationId: getSource)
- [ ] T050 [US4] Implementar endpoint GET /sources/{source_id}/columns em src/api/routes/schema.py (operationId: listSourceColumns)
- [ ] T051 [US4] Implementar endpoint GET /catalog/search em src/api/routes/schema.py (operationId: searchCatalog)
- [ ] T052 [US4] Adicionar tratamento de erros e mensagens em português para endpoints de consulta

**Checkpoint**: Todas as user stories devem estar funcionando independentemente

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T053 [P] Registrar router de schema em src/main.py ou src/api/__init__.py
- [ ] T054 [P] Atualizar __init__.py dos módulos com exports públicos
- [ ] T055 Validar fluxo completo com quickstart.md: extrair 4 tabelas identificadas
- [ ] T056 [P] Executar linters (ruff, black, mypy) e corrigir warnings
- [ ] T057 Documentar endpoints no README.md ou docs/
- [ ] T058 Validar performance: extração <30s, consultas <1s (p95) conforme spec.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode iniciar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as user stories
- **User Stories (Phase 3-6)**: Todas dependem de Foundational phase completion
  - US1 e US2 são P1 e devem ser completadas antes de US3
  - US3 (P2) pode iniciar após US1+US2
  - US4 (P3) pode iniciar após US2 (precisa do catálogo)
- **Polish (Phase 7)**: Depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **User Story 1 (P1)**: Pode iniciar após Foundational - Extração de schema (core)
- **User Story 2 (P1)**: Pode iniciar após US1 parcialmente completa - Persistência no catálogo
- **User Story 3 (P2)**: Depende de US1 + US2 - Precisa do schema extraído e persistido para enriquecer
- **User Story 4 (P3)**: Depende de US2 - Precisa do catálogo para consultas

### Within Each User Story

- DTOs antes de services
- Services antes de endpoints
- Implementação core antes de integração
- Story completa antes de mover para próxima prioridade

### Parallel Opportunities

- Todas as tarefas Setup marcadas [P] podem executar em paralelo
- Todas as tarefas Foundational marcadas [P] podem executar em paralelo (dentro da Phase 2)
- Após Foundational completa, US1 e US2 podem ter tarefas paralelas
- DTOs de diferentes stories marcados [P] podem executar em paralelo

---

## Parallel Example: User Story 1

```bash
# Launch DTOs em paralelo:
Task: T016 "Criar DTOs ExtractionRequest, ExtractionStartedResponse em src/schemas/schema_extraction.py"

# Launch models da Foundational em paralelo:
Task: T007 "Criar modelo ExternalSource em src/models/catalog/external_source.py"
Task: T008 "Criar modelo ColumnMetadata em src/models/catalog/column_metadata.py"
```

---

## Parallel Example: Foundational Repositories

```bash
# Launch repositories em paralelo (após T011 base.py):
Task: T012 "Criar MockDataRepository em src/repositories/mock_data_repository.py"
Task: T013 "Criar MongoDataRepository em src/repositories/mongo_data_repository.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - bloqueia todas as stories)
3. Complete Phase 3: User Story 1 (Extração)
4. Complete Phase 4: User Story 2 (Persistência)
5. **STOP and VALIDATE**: Testar extração e consulta básica das 4 tabelas
6. Deploy/demo se pronto - sistema funcional sem enriquecimento LLM

### Incremental Delivery

1. Complete Setup + Foundational → Fundação pronta
2. Add User Story 1 + 2 → Testar independentemente → Deploy/Demo (MVP!)
3. Add User Story 3 → Testar enriquecimento → Deploy/Demo
4. Add User Story 4 → Testar consultas avançadas → Deploy/Demo
5. Cada story adiciona valor sem quebrar stories anteriores

### Parallel Team Strategy

Com múltiplos desenvolvedores:

1. Time completa Setup + Foundational juntos
2. Após Foundational completa:
   - Developer A: User Story 1 (Extração)
   - Developer B: User Story 2 (Persistência) - pode iniciar DTOs em paralelo
3. Após US1+US2:
   - Developer A: User Story 3 (Enriquecimento)
   - Developer B: User Story 4 (Consultas)
4. Stories completam e integram independentemente

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica para rastreabilidade
- Cada user story deve ser completável e testável independentemente
- Commit após cada task ou grupo lógico
- Pare em qualquer checkpoint para validar story independentemente
- Evite: tasks vagas, conflitos de mesmo arquivo, dependências cross-story que quebrem independência
- **Arquivos mock disponíveis**: res/db/card_account_authorization.account_main.json, card_main.json, credit.invoice.json, credit.closed_invoice.json
