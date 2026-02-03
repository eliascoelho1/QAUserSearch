<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.         ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Feature Specification: Catálogo de Metadados em YAML

**Feature Branch**: `002-yaml-catalog`  
**Created**: 2026-02-03  
**Status**: Draft  
**Input**: Migrar o armazenamento do catálogo de metadados de fontes externas (external_sources e column_metadata) do PostgreSQL para arquivos YAML versionados no repositório.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta de Catálogo via API (Priority: P1)

Como **aplicação QAUserSearch**, preciso consultar o catálogo de metadados de fontes externas para que o sistema possa identificar quais campos estão disponíveis em cada fonte de dados MongoDB.

**Why this priority**: Esta é a funcionalidade core - sem leitura do catálogo, nenhuma busca de massas de QA funciona. Mantém compatibilidade com APIs existentes.

**Independent Test**: Pode ser testado iniciando a aplicação sem PostgreSQL e fazendo requisições GET para os endpoints de catálogo, verificando que retornam dados válidos dos arquivos YAML.

**Acceptance Scenarios**:

1. **Given** arquivos YAML existem em `catalog/sources/{db_name}/{table_name}.yaml`, **When** requisito GET /catalog/sources, **Then** sistema retorna lista de todas as sources com seus metadados básicos
2. **Given** arquivo YAML existe para source "credit/invoice", **When** requisito GET /catalog/sources/{id}, **Then** sistema retorna metadados completos incluindo colunas
3. **Given** requisição já foi feita para mesma source, **When** nova requisição é feita dentro do TTL do cache, **Then** sistema retorna dados do cache sem ler arquivo novamente
4. **Given** arquivo YAML não existe para source solicitada, **When** requisito GET /catalog/sources/{id}, **Then** sistema retorna erro 404 com mensagem clara

---

### User Story 2 - Extração de Metadados via CLI (Priority: P2)

Como **desenvolvedor**, preciso extrair metadados de fontes MongoDB e salvar em arquivos YAML para que o catálogo seja atualizado com novas sources ou mudanças de schema.

**Why this priority**: Essencial para popular e manter o catálogo atualizado. Sem extração, o catálogo fica obsoleto.

**Independent Test**: Pode ser testado executando `qa-catalog extract credit invoice` e verificando que arquivo YAML foi criado/atualizado corretamente em `catalog/sources/credit/invoice.yaml`.

**Acceptance Scenarios**:

1. **Given** conexão MongoDB disponível para "credit", **When** executo `qa-catalog extract credit invoice`, **Then** arquivo `catalog/sources/credit/invoice.yaml` é criado com metadados extraídos
2. **Given** arquivo YAML já existe para source, **When** executo `qa-catalog extract credit invoice`, **Then** arquivo é atualizado preservando campos editados manualmente (description, enrichment_status)
3. **Given** múltiplas known sources configuradas, **When** executo `qa-catalog extract-all`, **Then** todos os arquivos YAML são gerados/atualizados e índice `catalog/catalog.yaml` é atualizado
4. **Given** extração concluída com sucesso, **When** verifico índice `catalog/catalog.yaml`, **Then** source extraída aparece listada com timestamp de última extração

---

### User Story 3 - Edição Manual de Metadados (Priority: P3)

Como **QA**, preciso editar manualmente descrições e enriquecimentos nos arquivos YAML para que o catálogo tenha informações contextuais sobre cada campo.

**Why this priority**: Agrega valor ao catálogo com conhecimento humano, mas não bloqueia funcionalidade básica.

**Independent Test**: Pode ser testado editando manualmente um arquivo YAML, adicionando description em um campo, e verificando que a API retorna essa descrição.

**Acceptance Scenarios**:

1. **Given** arquivo YAML existe para source, **When** edito campo "description" de uma coluna, **Then** próxima leitura via API retorna descrição atualizada
2. **Given** edição manual foi feita em arquivo YAML, **When** executo `qa-catalog extract` para mesma source, **Then** campos editados manualmente são preservados
3. **Given** arquivo YAML editado manualmente, **When** executo `qa-catalog validate`, **Then** sistema valida estrutura contra JSON Schema e reporta erros se houver

---

### User Story 4 - Validação de Arquivos YAML (Priority: P4)

Como **desenvolvedor**, preciso validar arquivos YAML do catálogo antes de commitar para garantir que seguem o schema esperado.

**Why this priority**: Previne erros de formato que quebrariam a aplicação, mas pode ser feito manualmente até automação estar pronta.

**Independent Test**: Pode ser testado executando `qa-catalog validate` e verificando que arquivos válidos passam e inválidos falham com mensagens claras.

**Acceptance Scenarios**:

1. **Given** arquivos YAML válidos em `catalog/`, **When** executo `qa-catalog validate`, **Then** sistema reporta sucesso
2. **Given** arquivo YAML com campo obrigatório faltando, **When** executo `qa-catalog validate`, **Then** sistema reporta erro indicando arquivo e campo faltante
3. **Given** arquivo YAML com tipo incorreto em campo, **When** executo `qa-catalog validate`, **Then** sistema reporta erro indicando tipo esperado vs encontrado

---

### Edge Cases

- O que acontece quando arquivo YAML está corrompido (sintaxe inválida)?
  - Sistema deve logar erro e retornar 500 com mensagem amigável
- O que acontece quando diretório `catalog/` não existe?
  - CLI deve criar estrutura de diretórios automaticamente na primeira extração
- O que acontece quando cache TTL expira durante requisição concorrente?
  - Sistema deve garantir que apenas uma thread recarrega o arquivo (evitar thundering herd)
- O que acontece quando arquivo é editado enquanto está em cache?
  - Cache usa TTL configurável; alterações só são vistas após expiração do TTL
- O que acontece quando extração falha no meio (conexão MongoDB cai)?
  - Arquivo parcial não deve ser salvo; manter versão anterior intacta

## Requirements *(mandatory)*

### Functional Requirements

**Leitura do Catálogo:**

- **FR-001**: Sistema DEVE carregar metadados de arquivos YAML localizados em `catalog/sources/{db_name}/{table_name}.yaml`
- **FR-002**: Sistema DEVE manter índice global em `catalog/catalog.yaml` listando todas as sources disponíveis
- **FR-003**: Sistema DEVE implementar cache em memória com TTL configurável (padrão: 5 minutos) para evitar I/O excessivo
- **FR-004**: APIs REST GET /catalog/sources e GET /catalog/sources/{id} DEVEM continuar funcionando, lendo de YAML
- **FR-005**: Sistema DEVE invalidar cache quando TTL expira, recarregando arquivo na próxima requisição

**Escrita do Catálogo:**

- **FR-006**: Comando CLI `qa-catalog extract <db> <table>` DEVE gerar/atualizar arquivo YAML da source
- **FR-007**: Comando CLI `qa-catalog extract-all` DEVE gerar/atualizar todas as known sources e o índice
- **FR-008**: Extração DEVE atualizar automaticamente o índice `catalog/catalog.yaml`
- **FR-009**: Extração DEVE preservar campos editados manualmente (description, enrichment_status) ao atualizar
- **FR-010**: Comando CLI `qa-catalog validate` DEVE validar arquivos YAML contra JSON Schema

**Formato de Arquivo:**

- **FR-011**: Cada arquivo YAML DEVE conter: db_name, table_name, document_count, extracted_at, updated_at
- **FR-012**: Colunas DEVEM conter: path, name, type, required, nullable, enumerable, presence_ratio, sample_values
- **FR-013**: Colunas enumeráveis DEVEM conter unique_values
- **FR-014**: Colunas DEVEM suportar campos opcionais: description, enrichment_status
- **FR-015**: Arquivos DEVEM suportar comentários YAML para anotações manuais (preservados em re-extração)
- **FR-016**: JSON Schema DEVE ser fornecido para validação da estrutura dos arquivos

**Remoção de Funcionalidades:**

- **FR-017**: Endpoint DELETE /catalog/sources/{id} DEVE ser removido
- **FR-018**: Dependência de AsyncSession/SQLAlchemy DEVE ser removida dos serviços de catálogo

### Key Entities

- **CatalogIndex**: Índice global listando todas as sources disponíveis (db_name, table_name, last_extracted)
- **SourceMetadata**: Metadados de uma source específica (db_name, table_name, document_count, timestamps, columns)
- **ColumnMetadata**: Metadados de uma coluna (path, name, type, constraints, statistics, enrichments)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Catálogo funciona 100% sem conexão PostgreSQL configurada
- **SC-002**: CLI gera arquivos YAML que passam validação de schema em 100% dos casos
- **SC-003**: APIs de leitura retornam mesmos dados estruturais que implementação anterior (compatibilidade)
- **SC-004**: Cache reduz operações de I/O em pelo menos 90% para requisições repetidas dentro do TTL
- **SC-005**: Arquivos YAML são legíveis e editáveis por humanos (formato indentado, com comentários)
- **SC-006**: Tempo de resposta das APIs de catálogo permanece abaixo de 200ms (p95) após migração
- **SC-007**: Validação de arquivos YAML completa em menos de 5 segundos para catálogo com 50 sources

## Assumptions

- TTL padrão do cache será 5 minutos (300 segundos), configurável via variável de ambiente
- Campos editados manualmente são identificados por presença de valor não-nulo em `description` ou `enrichment_status`
- Estrutura de diretórios `catalog/sources/{db_name}/` é criada automaticamente se não existir
- JSON Schema para validação será armazenado em `catalog/schema/source.schema.json`
- Comentários YAML são preservados usando biblioteca que suporta round-trip (como ruamel.yaml)
