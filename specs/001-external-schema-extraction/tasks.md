<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Tasks: Extração Automática de Schema de Bancos Externos

**Input**: Design documents from `/specs/001-external-schema-extraction/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Incluídos conforme especificado na Constitution Check (TDD obrigatório, cobertura 80%+)

**Organization**: Tasks organizadas por user story para permitir implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual user story a task pertence (US1, US2, US4 - US3 é escopo futuro)
- Caminhos exatos de arquivos incluídos nas descrições

---

## Phase 1: Setup (Infraestrutura Compartilhada)

**Purpose**: Inicialização do projeto e estrutura básica

- [ ] T001 Adicionar dependências ao pyproject.toml: aiofiles>=24.1.0, motor>=3.6.0
- [ ] T002 [P] Criar enums DataSourceEnvironment, EnrichmentStatus, InferredType em src/schemas/enums.py
- [ ] T003 [P] Adicionar variáveis de configuração ao src/config.py: DATA_SOURCE_ENVIRONMENT, SCHEMA_SAMPLE_SIZE, ENUMERABLE_CARDINALITY_LIMIT, MONGODB_URI

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes)

**Purpose**: Infraestrutura core que DEVE estar completa antes de QUALQUER user story

**⚠️ CRÍTICO**: Nenhum trabalho de user story pode começar até esta fase estar completa

- [ ] T004 Criar modelo SQLAlchemy ExternalSource em src/models/catalog/external_source.py
- [ ] T005 [P] Criar modelo SQLAlchemy ColumnMetadata em src/models/catalog/column_metadata.py
- [ ] T006 Criar __init__.py para src/models/catalog/ exportando ExternalSource e ColumnMetadata
- [ ] T007 Gerar migration Alembic para tabelas external_sources e column_metadata
- [ ] T008 [P] Criar interface Protocol ExternalDataSource em src/repositories/external/base.py
- [ ] T009 [P] Criar Pydantic schemas de request/response em src/schemas/catalog.py (ExtractionRequest, SourceSummary, SourceDetailResponse, ColumnDetail, etc.)

**Checkpoint**: Foundation pronta - implementação de user stories pode começar em paralelo

---

## Phase 3: User Story 1 - Descoberta Automática de Schema (Priority: P1) 🎯 MVP

**Goal**: Extrair automaticamente estrutura de dados de tabelas externas a partir de amostras JSON

**Independent Test**: Fornecer um arquivo JSON de amostra e verificar se o schema extraído contém todos os campos com tipos corretos inferidos

### Tests para User Story 1 ⚠️

> **NOTE: Escrever estes testes PRIMEIRO, garantir que FALHEM antes da implementação**

- [ ] T010 [P] [US1] Unit test para TypeInferrer em tests/unit/test_extractor.py (tipos: string, integer, number, boolean, datetime, objectid, array, object, null)
- [ ] T011 [P] [US1] Unit test para flatten_fields em tests/unit/test_extractor.py (dot notation para estruturas aninhadas)
- [ ] T012 [P] [US1] Unit test para analyze_field_presence em tests/unit/test_analyzer.py (campos obrigatórios vs opcionais com threshold 95%)
- [ ] T013 [P] [US1] Unit test para analyze_cardinality em tests/unit/test_analyzer.py (detecção de enumeráveis com limite configurável)
- [ ] T014 [P] [US1] Integration test para extração completa de schema em tests/integration/test_schema_extraction.py

### Implementation para User Story 1

- [ ] T015 [P] [US1] Implementar TypeInferrer em src/services/schema_extraction/extractor.py (inferência de tipos com regex para datetime e objectid)
- [ ] T016 [P] [US1] Implementar flatten_fields em src/services/schema_extraction/extractor.py (achatamento de estruturas aninhadas com dot notation)
- [ ] T017 [US1] Implementar SchemaExtractor em src/services/schema_extraction/extractor.py (orquestra inferência de tipos e achatamento)
- [ ] T018 [P] [US1] Implementar analyze_field_presence em src/services/schema_extraction/analyzer.py (cálculo de presence_ratio)
- [ ] T019 [P] [US1] Implementar analyze_cardinality em src/services/schema_extraction/analyzer.py (detecção de enumeráveis e extração de valores únicos)
- [ ] T020 [US1] Implementar SchemaAnalyzer em src/services/schema_extraction/analyzer.py (orquestra análise de presença e cardinalidade)
- [ ] T021 [US1] Criar __init__.py para src/services/schema_extraction/ exportando SchemaExtractor e SchemaAnalyzer
- [ ] T022 [US1] Implementar MockExternalDataSource em src/repositories/external/mock_repository.py (leitura de arquivos JSON de res/db/)
- [ ] T023 [US1] Implementar ProdExternalDataSource em src/repositories/external/prod_repository.py (conexão MongoDB com Motor, $sample aggregation)
- [ ] T024 [US1] Criar factory get_external_data_source em src/repositories/external/__init__.py (seleção por DATA_SOURCE_ENVIRONMENT)

**Checkpoint**: User Story 1 está funcional - extração de schema funciona independentemente da persistência

---

## Phase 4: User Story 2 - Persistência de Schemas no Catálogo Local (Priority: P1)

**Goal**: Persistir schemas extraídos no PostgreSQL local em formato estruturado

**Independent Test**: Verificar que após extração, as tabelas do catálogo no PostgreSQL contêm os metadados esperados

### Tests para User Story 2 ⚠️

- [ ] T025 [P] [US2] Unit test para CatalogRepository em tests/unit/test_catalog_repository.py (CRUD de ExternalSource e ColumnMetadata)
- [ ] T026 [P] [US2] Integration test para persistência de schema em tests/integration/test_schema_extraction.py (extração + persistência end-to-end)

### Implementation para User Story 2

- [ ] T027 [US2] Implementar CatalogRepository em src/repositories/catalog/catalog_repository.py (CRUD com upsert para re-extração)
- [ ] T028 [US2] Criar __init__.py para src/repositories/catalog/ exportando CatalogRepository
- [ ] T029 [US2] Implementar CatalogService em src/services/catalog_service.py (orquestra extração, análise e persistência)
- [ ] T030 [US2] Adicionar lógica de upsert ao CatalogService para sobrescrever schemas existentes (sem versionamento em v1)
- [ ] T031 [US2] Adicionar logging estruturado com structlog ao CatalogService

**Checkpoint**: User Stories 1 E 2 funcionam independentemente - extração e persistência completas

---

## Phase 5: User Story 4 - Interface de Consulta ao Catálogo (Priority: P3)

**Goal**: Consultar catálogo de schemas para entender quais dados estão disponíveis nas fontes externas

**Independent Test**: Acessar endpoint que lista schemas disponíveis com suas colunas e descrições

### Tests para User Story 4 ⚠️

- [ ] T032 [P] [US4] Contract test para GET /catalog/sources em tests/contract/test_catalog_contracts.py
- [ ] T033 [P] [US4] Contract test para GET /catalog/sources/{source_id} em tests/contract/test_catalog_contracts.py
- [ ] T034 [P] [US4] Contract test para GET /catalog/sources/{source_id}/columns em tests/contract/test_catalog_contracts.py
- [ ] T035 [P] [US4] Contract test para POST /catalog/extraction em tests/contract/test_catalog_contracts.py
- [ ] T036 [P] [US4] Contract test para GET /catalog/extraction/{task_id} em tests/contract/test_catalog_contracts.py
- [ ] T037 [P] [US4] Contract test para POST /catalog/extraction/all em tests/contract/test_catalog_contracts.py
- [ ] T038 [P] [US4] Contract test para DELETE /catalog/sources/{source_id} em tests/contract/test_catalog_contracts.py

### Implementation para User Story 4

- [ ] T039 [US4] Implementar endpoint GET /catalog/sources em src/api/v1/catalog.py (listagem com paginação e filtro por db_name)
- [ ] T040 [US4] Implementar endpoint GET /catalog/sources/{source_id} em src/api/v1/catalog.py (detalhes com estatísticas)
- [ ] T041 [US4] Implementar endpoint DELETE /catalog/sources/{source_id} em src/api/v1/catalog.py (remoção com cascade)
- [ ] T042 [US4] Implementar endpoint GET /catalog/sources/{source_id}/columns em src/api/v1/catalog.py (filtros: type, is_required, is_enumerable)
- [ ] T043 [US4] Implementar endpoint POST /catalog/extraction em src/api/v1/catalog.py (extração assíncrona com task_id)
- [ ] T044 [US4] Implementar endpoint GET /catalog/extraction/{task_id} em src/api/v1/catalog.py (status da tarefa)
- [ ] T045 [US4] Implementar endpoint POST /catalog/extraction/all em src/api/v1/catalog.py (extração em lote das 4 tabelas)
- [ ] T046 [US4] Registrar router do catálogo no src/main.py (prefix /api/v1)
- [ ] T047 [US4] Implementar mecanismo de task tracking para extrações assíncronas (in-memory ou Redis se disponível)

**Checkpoint**: Todas as user stories estão funcionais independentemente

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [ ] T048 [P] Atualizar documentação em docs/ com instruções de uso da API de catálogo
- [ ] T049 [P] Validar quickstart.md com todos os cenários de teste
- [ ] T050 Code cleanup e validação de código com ruff e black
- [ ] T051 [P] Adicionar unit tests complementares para cobertura mínima de 80% em tests/unit/
- [ ] T052 Verificar performance: extração < 30s, consulta p95 < 1s
- [ ] T053 Executar extração das 4 tabelas iniciais para validação final

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as user stories
- **User Story 1 (Phase 3)**: Depende de Foundational
- **User Story 2 (Phase 4)**: Depende de Foundational e US1 (usa extração)
- **User Story 4 (Phase 5)**: Depende de Foundational e US2 (consulta dados persistidos)
- **Polish (Phase 6)**: Depende de todas as user stories desejadas estarem completas

### User Story Dependencies

- **User Story 1 (P1)**: Pode começar após Foundational - Base para todas as outras
- **User Story 2 (P1)**: Depende de US1 para extração - Persiste os resultados
- **User Story 4 (P3)**: Depende de US2 para dados - Expõe via API

> **Nota**: User Story 3 (Enriquecimento LLM) foi movida para v2 conforme especificação

### Dentro de Cada User Story

- Tests DEVEM ser escritos e FALHAR antes da implementação (TDD)
- Models antes de services
- Services antes de endpoints
- Implementação core antes de integração
- Story completa antes de mover para próxima prioridade

### Oportunidades de Paralelização

**Phase 1 (Setup):**
```bash
# Paralelo:
Task: T002 - Criar enums em src/schemas/enums.py
Task: T003 - Adicionar variáveis de configuração ao src/config.py
```

**Phase 2 (Foundational):**
```bash
# Sequencial primeiro:
Task: T004 - Criar modelo ExternalSource
# Depois paralelo:
Task: T005 - Criar modelo ColumnMetadata
Task: T008 - Criar interface Protocol ExternalDataSource
Task: T009 - Criar Pydantic schemas
```

**Phase 3 (User Story 1 - Tests):**
```bash
# Todos os tests em paralelo:
Task: T010 - Unit test para TypeInferrer
Task: T011 - Unit test para flatten_fields
Task: T012 - Unit test para analyze_field_presence
Task: T013 - Unit test para analyze_cardinality
Task: T014 - Integration test para extração
```

**Phase 3 (User Story 1 - Implementation):**
```bash
# Paralelo:
Task: T015 - Implementar TypeInferrer
Task: T016 - Implementar flatten_fields
Task: T018 - Implementar analyze_field_presence
Task: T019 - Implementar analyze_cardinality
```

**Phase 5 (User Story 4 - Tests):**
```bash
# Todos os contract tests em paralelo:
Task: T032-T038 - Contract tests para todos os endpoints
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRÍTICO - bloqueia todas as stories)
3. Complete Phase 3: User Story 1 (Extração de Schema)
4. Complete Phase 4: User Story 2 (Persistência)
5. **PARAR e VALIDAR**: Testar extração e persistência end-to-end
6. Deploy/demo se pronto - catálogo funcional sem API REST

### Incremental Delivery

1. Setup + Foundational → Foundation pronta
2. User Story 1 → Testar independentemente → Extração funciona
3. User Story 2 → Testar independentemente → Persistência funciona (MVP!)
4. User Story 4 → Testar independentemente → API REST funciona
5. Cada story adiciona valor sem quebrar stories anteriores

### Success Criteria Tracking

| Critério | User Story | Status |
|----------|------------|--------|
| SC-001: 4 tabelas catalogadas | US1 + US2 | ⬜ |
| SC-002: Extração < 30s | US1 | ⬜ |
| SC-004: Consulta p95 < 1s | US4 | ⬜ |
| SC-005: Nova tabela sem alteração de código | US1 | ⬜ |
| SC-006: Campos description/enrichment_status preparados | US2 | ⬜ |

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica para rastreabilidade
- Cada user story deve ser independentemente completável e testável
- Verificar que tests falham antes de implementar
- Commit após cada task ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
- User Story 3 (LLM) está fora do escopo v1 - estrutura de dados preparada para v2
- Evitar: tasks vagas, conflitos no mesmo arquivo, dependências cross-story que quebram independência
