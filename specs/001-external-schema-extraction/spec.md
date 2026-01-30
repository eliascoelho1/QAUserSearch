<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Feature Specification: Extração Automática de Schema de Bancos Externos

**Feature Branch**: `001-external-schema-extraction`  
**Created**: 2026-01-29  
**Status**: Draft  
**Input**: User description: "Arquitetura para extração automática de schema de bancos externos, persistência no PostgreSQL local e uso de LLM para enriquecimento de metadados"

## Clarifications

### Session 2026-01-29

- Q: Como funciona a estratégia de ambientes para acesso aos dados externos? → A: Dois ambientes isolados - MOCK (arquivos JSON locais em `res/db/`) e PROD (conexão direta aos bancos externos reais). Cada ambiente é um repositório apartado, configurável via Settings/.env.
- Q: Em ambiente PROD, como o schema deve ser extraído do MongoDB externo? → A: Analisa uma amostra de N documentos em runtime (mesmo approach do MOCK, mas com dados reais)
- Q: Qual o tamanho padrão da amostra de documentos para extração de schema? → A: 500 documentos por padrão (maior precisão), configurável via Settings/.env
- Q: Como o sistema deve se comportar quando a LLM não está disponível ou falha? → A: Continuar sem descrição, marcar coluna como "pending_enrichment" para retry posterior
- Q: Qual LLM será utilizada para enriquecimento? → A: OpenAI (não HubAI como assumido inicialmente)
- Q: Como identificar e extrair valores únicos para colunas enumeráveis? → A: Extrair apenas para colunas com cardinalidade ≤50 valores únicos, marcando-as como "enumerável"
- Q: A LLM deve participar da detecção de colunas enumeráveis? → A: Não, detecção é puramente estatística (cardinalidade). LLM foca apenas em descrições semânticas.
- Q: O limite de cardinalidade para colunas enumeráveis deve ser configurável? → A: Sim, parametrizável via Settings/.env (padrão: 50)

### Session 2026-01-30

- Q: Os enriquecimentos que dependem de LLM devem fazer parte desta versão? → A: Mover LLM para versão futura, mas preparar estrutura de dados agora (campos de descrição e status `pending_enrichment` já presentes no modelo)
- Q: Como o versionamento de schemas deve funcionar na re-extração? → A: Sobrescrever schema atual sem histórico de versões em v1 (SchemaVersion será implementado em versão futura se necessário)

## Contexto e Motivação

A aplicação QAUserSearch precisa consultar múltiplos bancos de dados externos (MongoDB) para buscar massas de teste em ambiente QA. Para evitar acoplamento forte com a estrutura atual desses bancos, e permitir que o sistema gere queries dinâmicas de forma inteligente, é necessário:

1. **Extrair automaticamente o schema** de cada tabela externa, utilizando uma das fontes de dados conforme o ambiente configurado
2. **Persistir os schemas** no banco local PostgreSQL, criando um catálogo de metadados
3. **Enriquecer os metadados** usando LLM para gerar descrições semânticas de cada coluna
4. **Estabelecer padrões arquiteturais** que permitam expansão futura para novos bancos/tabelas

### Bancos e Tabelas Identificados

| Banco                        | Tabela       | Propósito                              |
| ---------------------------- | ------------ | -------------------------------------- |
| card_account_authorization   | account_main | Dados de contas de cartão              |
| card_account_authorization   | card_main    | Dados de cartões físicos/virtuais      |
| credit                       | invoice      | Faturas abertas                        |
| credit                       | closed_invoice | Faturas fechadas (com transações)    |

### Estratégia de Ambientes

O sistema opera em dois modos de acesso às fontes de dados externas:

| Ambiente | Fonte de Dados | Propósito |
| -------- | -------------- | --------- |
| **MOCK** | Arquivos JSON locais em `res/db/` | Desenvolvimento, testes, demonstrações offline |
| **PROD** | Conexão direta aos bancos MongoDB externos | Ambiente de produção com dados reais |

- Cada ambiente utiliza um **repositório de dados apartado** (implementação distinta do conector)
- A seleção do ambiente é feita via variável de configuração em **Settings/.env**
- A interface de acesso aos dados é **idêntica** independente do ambiente, garantindo que a lógica de negócio não precise conhecer a origem
- **Extração de schema em PROD**: Analisa uma amostra de N documentos em runtime, utilizando a mesma lógica de inferência do ambiente MOCK
- **Tamanho da amostra**: 500 documentos por padrão (garante precisão na detecção de campos opcionais), configurável via Settings/.env por tabela

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descoberta Automática de Schema (Priority: P1)

Como desenvolvedor da plataforma QAUserSearch, preciso que o sistema extraia automaticamente a estrutura de dados de tabelas externas a partir de amostras JSON, para que eu não precise mapear manualmente cada campo e possa acompanhar mudanças estruturais.

**Why this priority**: Esta é a funcionalidade fundamental que habilita todas as outras. Sem o schema extraído, não há como gerar queries dinâmicas ou fornecer contexto para a LLM.

**Independent Test**: Pode ser testado fornecendo um arquivo JSON de amostra e verificando se o schema extraído contém todos os campos com tipos corretos inferidos.

**Acceptance Scenarios**:

1. **Given** um arquivo JSON com registros de exemplo de uma tabela externa, **When** o sistema processa este arquivo, **Then** um schema é gerado contendo nome do campo, tipo de dado inferido, e indicação de aninhamento (nested objects).
2. **Given** múltiplos registros com estruturas ligeiramente diferentes (campos opcionais), **When** o sistema processa estes registros, **Then** o schema identifica corretamente quais campos são obrigatórios e quais são opcionais.
3. **Given** campos com valores nulos em todas as amostras, **When** o sistema processa estes registros, **Then** o campo é mapeado como tipo "unknown/nullable" para posterior revisão.

---

### User Story 2 - Persistência de Schemas no Catálogo Local (Priority: P1)

Como desenvolvedor da plataforma, preciso que os schemas extraídos sejam persistidos no PostgreSQL local em um formato estruturado, para que possam ser consultados por outros componentes do sistema (geração de queries, interface de usuário).

**Why this priority**: A persistência é essencial para que o conhecimento sobre as tabelas externas seja reutilizável e consultável por toda a aplicação.

**Independent Test**: Pode ser testado verificando que após a extração, as tabelas do catálogo no PostgreSQL contêm os metadados esperados.

**Acceptance Scenarios**:

1. **Given** um schema extraído de uma tabela externa, **When** o sistema persiste este schema, **Then** os metadados são armazenados no PostgreSQL local de forma normalizada (tabela de sources, tabela de columns).
2. **Given** uma tabela já catalogada, **When** uma nova extração é executada com mudanças estruturais, **Then** o catálogo é atualizado preservando histórico de versões ou sobrescrevendo conforme configuração.
3. **Given** múltiplas tabelas de diferentes bancos externos, **When** todas são catalogadas, **Then** cada uma possui identificação única combinando nome do banco e nome da tabela.

---

### User Story 3 - Enriquecimento de Metadados via LLM (Priority: FUTURE - Escopo v2)

> ⚠️ **ESCOPO FUTURO**: Esta user story foi movida para uma versão futura. A estrutura de dados (campos `description`, `enrichment_status`) será criada nesta versão para facilitar a implementação posterior.

Como desenvolvedor da plataforma, preciso que uma LLM analise os schemas extraídos e gere descrições semânticas para cada coluna, para que usuários e o próprio sistema de geração de queries tenham contexto sobre o significado dos dados.

**Why this priority**: O enriquecimento semântico é valioso mas não bloqueia a funcionalidade básica de busca. Será implementado em versão futura após o catálogo básico estar funcional e validado.

**Independent Test**: Pode ser testado enviando um schema para a LLM e verificando se descrições coerentes são geradas para cada coluna.

**Acceptance Scenarios**:

1. **Given** um schema catalogado com nomes de colunas técnicos (ex: `consumer_id`, `due_date`), **When** a LLM processa este schema, **Then** descrições em linguagem natural são geradas (ex: "Identificador único do consumidor", "Data de vencimento da fatura").
2. **Given** colunas com valores de exemplo disponíveis, **When** a LLM processa o schema, **Then** as descrições consideram o contexto dos valores para maior precisão.
3. **Given** um schema já enriquecido anteriormente, **When** o processo é executado novamente, **Then** o sistema oferece opção de manter descrições existentes ou regenerá-las.

---

### User Story 4 - Interface de Consulta ao Catálogo (Priority: P3)

Como desenvolvedor ou usuário da plataforma, preciso consultar o catálogo de schemas para entender quais dados estão disponíveis nas fontes externas, facilitando a construção de buscas personalizadas.

**Why this priority**: É uma conveniência que melhora a experiência, mas a funcionalidade principal de busca pode operar apenas com acesso programático ao catálogo.

**Independent Test**: Pode ser testado acessando um endpoint ou comando que lista os schemas disponíveis com suas colunas e descrições.

**Acceptance Scenarios**:

1. **Given** múltiplas tabelas catalogadas, **When** um usuário solicita listagem de fontes disponíveis, **Then** todas as fontes são retornadas com nome do banco, tabela e contagem de colunas.
2. **Given** uma fonte específica selecionada, **When** o usuário solicita detalhes, **Then** todas as colunas são listadas com nome, tipo, se é obrigatória/opcional, e descrição semântica.

---

### Edge Cases

- O que acontece quando um campo contém tipos mistos (ex: string em um registro, número em outro)?
- Como o sistema lida com campos profundamente aninhados (objetos dentro de objetos dentro de arrays)?
- O que acontece quando o arquivo JSON de amostra está vazio ou malformado?
- Como tratar campos que aparecem em menos de 5% dos registros (outliers)?
- O que acontece quando a LLM não consegue gerar uma descrição coerente para um campo?
  - **Resposta**: *(Escopo v2)* Sistema continua sem descrição, marca coluna como `pending_enrichment` para retry automático posterior

## Requirements *(mandatory)*

### Functional Requirements

**Extração de Schema:**
- **FR-001**: Sistema DEVE extrair schema a partir de arquivos JSON seguindo o padrão de nomenclatura `${db_name}.${table_name}.json`
- **FR-002**: Sistema DEVE inferir tipos de dados (string, number, boolean, date, object, array) baseado na análise de valores
- **FR-003**: Sistema DEVE identificar campos obrigatórios (presentes em >95% dos registros) vs opcionais
- **FR-004**: Sistema DEVE suportar estruturas aninhadas (nested objects) com representação hierárquica
- **FR-025**: Sistema DEVE identificar colunas enumeráveis (cardinalidade ≤ limite configurável na amostra, padrão: 50)
- **FR-026**: Sistema DEVE extrair e armazenar a lista de valores únicos para colunas identificadas como enumeráveis
- **FR-027**: Sistema DEVE marcar colunas como "is_enumerable=true" quando atenderem ao critério de cardinalidade
- **FR-028**: Sistema DEVE detectar colunas enumeráveis usando análise estatística de cardinalidade (LLM NÃO participa desta detecção)
- **FR-029**: Sistema DEVE permitir configuração do limite de cardinalidade para detecção de enumeráveis via Settings/.env (ENUMERABLE_CARDINALITY_LIMIT, padrão: 50)

**Persistência:**
- **FR-005**: Sistema DEVE armazenar schemas em tabelas dedicadas no PostgreSQL local
- **FR-006**: Sistema DEVE manter relação entre fonte externa (db + tabela) e suas colunas
- **FR-007**: Sistema DEVE registrar timestamp de última atualização do schema
- **FR-008**: Sistema DEVE permitir re-extração de schema sobrescrevendo dados anteriores (sem versionamento em v1)

**Enriquecimento LLM (ESCOPO FUTURO - v2):**
> ⚠️ Os requisitos abaixo serão implementados em versão futura. A estrutura de dados será preparada nesta versão.
- **FR-009**: ~~Sistema DEVE enviar contexto de schema para LLM (OpenAI) para geração de descrições~~ → *FUTURO*
- **FR-010**: ~~Sistema DEVE armazenar descrições geradas pela LLM junto aos metadados da coluna~~ → *FUTURO (estrutura de dados preparada)*
- **FR-011**: ~~Sistema DEVE permitir execução do enriquecimento de forma assíncrona/batch~~ → *FUTURO*
- **FR-023**: ~~Sistema DEVE marcar colunas como "pending_enrichment" quando LLM falhar ou estiver indisponível~~ → *FUTURO (campo preparado)*
- **FR-024**: ~~Sistema DEVE implementar mecanismo de retry automático para colunas com status "pending_enrichment"~~ → *FUTURO*

**Preparação para Enriquecimento Futuro (v1):**
- **FR-030**: Sistema DEVE incluir campos `description` (nullable) e `enrichment_status` no modelo ColumnMetadata para suportar enriquecimento LLM futuro
- **FR-031**: Sistema DEVE inicializar `enrichment_status` como "not_enriched" para todas as colunas nesta versão

**Arquitetura:**
- **FR-012**: Sistema DEVE seguir padrão de Repository para acesso a dados
- **FR-013**: Sistema DEVE utilizar injeção de dependências para serviços
- **FR-014**: Sistema DEVE separar camadas de domínio, aplicação e infraestrutura
- **FR-015**: Sistema DEVE permitir adição de novos conectores de banco sem alteração no core

**Ambientes e Configuração:**
- **FR-016**: Sistema DEVE suportar dois ambientes de fonte de dados: MOCK (arquivos JSON locais) e PROD (bancos externos reais)
- **FR-017**: Sistema DEVE permitir seleção do ambiente via arquivo de configuração Settings/.env
- **FR-018**: Sistema DEVE implementar repositórios apartados para cada ambiente, com interface comum
- **FR-019**: Sistema DEVE garantir que a troca de ambiente não requeira alteração em código de negócio
- **FR-020**: Sistema DEVE extrair schema em PROD analisando amostra de documentos em runtime, usando mesma lógica de inferência do MOCK
- **FR-021**: Sistema DEVE usar 500 documentos como tamanho padrão de amostra para extração de schema
- **FR-022**: Sistema DEVE permitir configuração do tamanho da amostra via Settings/.env (por tabela ou global)

### Key Entities

- **ExternalSource**: Representa uma fonte de dados externa (combinação de nome do banco + nome da tabela). Atributos: identificador, nome do banco, nome da tabela, timestamp de catalogação, versão do schema.

- **ColumnMetadata**: Representa uma coluna dentro de uma fonte externa. Atributos: identificador, referência à fonte, nome da coluna, tipo inferido, é obrigatório, caminho no JSON (para nested), descrição semântica (nullable, preparado para LLM futuro), valores de exemplo, status de enriquecimento (not_enriched/pending_enrichment/enriched - inicializa como "not_enriched"), é enumerável (cardinalidade ≤50), valores únicos (lista de valores distintos quando enumerável).

- **SchemaVersion**: *(ESCOPO FUTURO)* Histórico de versões de schema para uma fonte. Atributos: identificador, referência à fonte, versão, timestamp, snapshot do schema. Em v1, a re-extração sobrescreve o schema atual.

## Assumptions

- O PostgreSQL local já está configurado e acessível pela aplicação
- A LLM utilizada para enriquecimento é da **OpenAI** (configurada via Settings/.env) - **implementação prevista para v2**
- Os bancos externos são MongoDB (documentos JSON), conforme evidenciado pelos campos `_id` e `_class`
- O foco inicial são as 4 tabelas identificadas; expansão para outras tabelas seguirá o mesmo padrão
- Em ambiente MOCK, os arquivos JSON em `res/db/` são amostras representativas das tabelas externas
- Em ambiente PROD, as credenciais de acesso aos bancos externos são configuradas via Settings/.env

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das 4 tabelas identificadas (account_main, card_main, invoice, closed_invoice) têm schemas extraídos e catalogados
- **SC-002**: Extração de schema para uma nova tabela leva menos de 30 segundos
- **SC-003**: ~~90% das colunas possuem descrições semânticas geradas pela LLM~~ → *Movido para v2*
- **SC-004**: O catálogo pode ser consultado retornando resultados em menos de 1 segundo
- **SC-005**: Adicionar suporte a uma nova tabela externa requer apenas fornecer arquivo JSON de amostra, sem alterações de código
- **SC-006**: 100% das colunas têm campos `description` e `enrichment_status` preparados para enriquecimento LLM futuro
