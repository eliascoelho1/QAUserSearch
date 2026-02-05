# Feature Specification: Enriquecimento Semantico do Catalogo com IA

**Feature Branch**: `004-catalog-ai-enrichment`  
**Created**: 2026-02-05  
**Status**: Draft  
**Input**: User description: "Pipeline para adicionar metadados semanticos ao catalogo YAML existente usando LLM (OpenAI)"  
**Dependency**: Depende da spec [003-cli-shared-ui](../003-cli-shared-ui/spec.md) (infraestrutura compartilhada de UI)

---

## Clarifications

### Session 2026-02-05

- Q: What should be the timeout behavior for LLM calls? → A: 30 seconds per field, 10 minutes total timeout
- Q: What is the default OpenAI model for enrichment? → A: gpt-4o-mini (good quality, ~$0.01/field)
- Q: What is the maximum number of search_synonyms per field? → A: Maximum 10 synonyms per field

---

## Contexto do Problema

O catalogo de metadados atual (`catalog/sources/**/*.yaml`) contem informacoes tecnicas extraidas automaticamente das fontes MongoDB:
- Tipos de dados (`string`, `integer`, `boolean`, etc.)
- Valores de exemplo (`sample_values`)
- Cardinalidade (`enumerable`, `unique_values`)
- Metricas de presenca (`presence_ratio`, `required`)

**O que falta**: Contexto semantico para que o LLM interprete corretamente prompts de usuarios e gere queries precisas.

### Exemplo do Problema

```yaml
# ANTES: Dados tecnicos sem contexto
- path: block_code
  name: block_code
  type: string
  unique_values: ['', 'R', 'F', 'P', 'B', 'J']
  # Usuario busca "cartao roubado" -> LLM nao mapeia para block_code = 'R'
  # LLM nao sabe que 'J' significa "CRELI (inadimplencia grave)"
```

### Solucao Proposta

Enriquecer o catalogo com **5 novos campos semanticos** por coluna:

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `description` | `string` | Descricao semantica em portugues (max 100 chars) |
| `domain_category` | `enum` | Categoria de negocio (`status`, `financial`, `temporal`, `identification`, `configuration`) |
| `search_synonyms` | `list[str]` | Termos alternativos para busca natural (max 10 itens) |
| `enum_meanings` | `dict[str, str]` | Significado de valores enumeraveis |
| `business_rules` | `string \| null` | Regras de negocio associadas |

---

## User Scenarios & Testing

### User Story 1 - Enriquecimento Individual via CLI (Priority: P1)

Como desenvolvedor/analista, quero enriquecer campos de uma tabela especifica usando IA, para que o LLM possa interpretar corretamente buscas em linguagem natural.

**Why this priority**: Esta e a funcionalidade core do sistema. Sem ela, nenhum campo pode ser enriquecido. Permite validacao humana do output da IA antes de persistir.

**Independent Test**: Pode ser testado executando `uv run qa-catalog enrich credit invoice` e validando que o YAML foi atualizado corretamente com campos semanticos.

**Acceptance Scenarios**:

1. **Given** um catalogo YAML existente para `credit.invoice` com campos `status`, `block_code`, `archived`
   **When** usuario executa `uv run qa-catalog enrich credit invoice`
   **Then** sistema exibe painel com enriquecimento gerado pela IA para cada campo prioritario
   **And** usuario pode aprovar, editar ou rejeitar cada enriquecimento
   **And** campos aprovados sao persistidos no YAML com `enrichment_status: enriched`

2. **Given** um campo `status` com `unique_values: [OPEN, CLOSED, DELAYED, ADVANCE_PAYMENT, OPEN_PAYMENT]`
   **When** IA processa o campo
   **Then** `enum_meanings` contem significado para todos os 5 valores
   **And** `search_synonyms` contem termos como "situacao da fatura", "fatura aberta", "fatura atrasada"
   **And** `domain_category` e definido como "status"

3. **Given** usuario quer enriquecer apenas campos especificos
   **When** executa `uv run qa-catalog enrich credit invoice --fields status,block_code`
   **Then** apenas os campos `status` e `block_code` sao processados

4. **Given** usuario quer aprovar tudo automaticamente (CI/CD)
   **When** executa `uv run qa-catalog enrich credit invoice --auto-approve`
   **Then** todos os enriquecimentos sao salvos sem interacao humana

---

### User Story 2 - Validacao Interativa de Enriquecimento (Priority: P1)

Como analista de QA, quero revisar e editar os enriquecimentos gerados pela IA, para garantir que os metadados estejam corretos antes de serem salvos.

**Why this priority**: A validacao humana e essencial para garantir qualidade dos metadados. LLMs podem gerar informacoes incorretas que precisam ser corrigidas.

**Independent Test**: Pode ser testado simulando input do usuario via mock de `questionary` e validando que edicoes sao aplicadas corretamente.

**Acceptance Scenarios**:

1. **Given** IA gerou enriquecimento para campo `block_code`
   **When** usuario seleciona "Editar description"
   **Then** prompt de texto permite digitar nova descricao
   **And** nova descricao substitui a gerada pela IA

2. **Given** IA gerou `enum_meanings` incompleto (faltou valor 'G')
   **When** usuario seleciona "Editar enum_meanings"
   **Then** sistema exibe editor para corrigir/adicionar significados
   **And** significado para 'G' pode ser adicionado manualmente

3. **Given** usuario quer rejeitar enriquecimento completamente
   **When** seleciona "Rejeitar"
   **Then** campo e marcado como `enrichment_status: pending_enrichment`
   **And** YAML nao e alterado para aquele campo

4. **Given** usuario quer pular campo para revisar depois
   **When** seleciona "Pular"
   **Then** campo mantem `enrichment_status: not_enriched`
   **And** sistema continua para proximo campo

---

### User Story 3 - Atualizacao de Schemas JSON e Pydantic (Priority: P1)

Como desenvolvedor, quero que os schemas JSON e Pydantic suportem os novos campos semanticos, para que a validacao e serializacao funcionem corretamente.

**Why this priority**: E pre-requisito tecnico para todas as outras funcionalidades. Sem schemas atualizados, nao e possivel persistir os novos campos.

**Independent Test**: Pode ser testado criando um YAML com todos os novos campos e validando contra o JSON Schema, alem de testar serializacao/deserializacao via Pydantic.

**Acceptance Scenarios**:

1. **Given** um arquivo YAML com campos semanticos novos
   **When** executado `uv run qa-catalog validate`
   **Then** validacao passa sem erros

2. **Given** classe `ColumnMetadataYaml` em Pydantic
   **When** carregado YAML com `enum_meanings`, `search_synonyms`, `domain_category`
   **Then** campos sao deserializados corretamente
   **And** `to_yaml_dict()` preserva todos os campos na serializacao

3. **Given** re-extracao de schema (`uv run qa-catalog extract credit invoice`)
   **When** arquivo YAML ja possui campos semanticos enriquecidos
   **Then** campos semanticos sao preservados (merge)
   **And** apenas campos tecnicos sao atualizados

---

### User Story 4 - Servico de Enriquecimento com OpenAI (Priority: P1)

Como desenvolvedor, quero um servico robusto que chame a API OpenAI com retry e validacao, para gerar enriquecimentos de forma confiavel.

**Why this priority**: E a integracao central com LLM. Sem este servico, nao ha geracao automatica de metadados.

**Independent Test**: Pode ser testado com mocks da API OpenAI retornando JSON valido/invalido e verificando comportamento de retry e validacao.

**Acceptance Scenarios**:

1. **Given** campo `status` com tipo `string` e `unique_values`
   **When** `LLMEnricher.enrich_field()` e chamado
   **Then** retorna `FieldEnrichment` com todos os 5 campos preenchidos
   **And** `enum_meanings` contem entrada para cada valor em `unique_values`

2. **Given** API OpenAI retorna erro 429 (rate limit)
   **When** `LLMEnricher.enrich_field()` e chamado
   **Then** sistema faz retry com backoff exponencial
   **And** maximo de 3 tentativas antes de falhar

3. **Given** API OpenAI retorna JSON malformado
   **When** resposta e validada
   **Then** erro e logado e campo e marcado para retry
   **And** `enrichment_status: pending_enrichment`

4. **Given** campo e do tipo `objectid` ou `_class` (interno)
   **When** filtrado pelo `FieldSelector`
   **Then** campo e ignorado (nao enviado para IA)

---

### User Story 5 - Visualizacao de Status de Enriquecimento (Priority: P2)

Como analista, quero visualizar o progresso de enriquecimento do catalogo, para saber quais tabelas precisam de atencao.

**Why this priority**: Importante para gestao do catalogo, mas nao bloqueia funcionalidade principal de enriquecimento.

**Independent Test**: Pode ser testado executando `uv run qa-catalog enrich-status` e verificando output formatado.

**Acceptance Scenarios**:

1. **Given** catalogo com 4 tabelas (credit.invoice, credit.closed_invoice, card_account.card_main, card_account.account_main)
   **When** usuario executa `uv run qa-catalog enrich-status`
   **Then** exibe tabela com progresso por fonte
   **And** mostra total de campos, enriquecidos e percentual

```
+----------------------+---------+----------+-------------+
| Source               | Total   | Enriched | Progress    |
+----------------------+---------+----------+-------------+
| credit.invoice       | 21      | 15       | ########-- 71% |
| credit.closed_invoice| 28      | 0        | ----------  0% |
| card_account.card_main| 45     | 12       | ###------- 27% |
| card_account.account_main| 38  | 0        | ----------  0% |
+----------------------+---------+----------+-------------+
```

2. **Given** usuario quer ver campos pendentes
   **When** executa `uv run qa-catalog enrich-pending`
   **Then** lista campos com `enrichment_status != enriched` agrupados por tabela

---

### User Story 6 - Enriquecimento em Batch (Priority: P2)

Como desenvolvedor, quero enriquecer todas as tabelas de uma vez, para configurar o catalogo inicial rapidamente.

**Why this priority**: Util para setup inicial, mas enriquecimento individual e suficiente para MVP.

**Independent Test**: Pode ser testado executando `uv run qa-catalog enrich-all --priority-only` e verificando que multiplas tabelas sao processadas.

**Acceptance Scenarios**:

1. **Given** 4 tabelas conhecidas no catalogo
   **When** usuario executa `uv run qa-catalog enrich-all`
   **Then** todas as tabelas sao processadas em sequencia
   **And** progresso e exibido em tempo real

2. **Given** usuario quer apenas campos prioritarios
   **When** executa `uv run qa-catalog enrich-all --priority-only`
   **Then** apenas campos com `presence_ratio >= 0.9` e `enumerable = true` sao processados

3. **Given** usuario quer revisar em batches
   **When** executa `uv run qa-catalog enrich-all --interactive --batch-size 5`
   **Then** sistema pausa a cada 5 campos para revisao

---

### User Story 7 - Documentacao de Contexto de Dominio (Priority: P3)

Como desenvolvedor, quero documentar contexto de dominio em arquivos Markdown, para que a IA use informacoes corretas ao gerar enriquecimentos.

**Why this priority**: Melhora qualidade dos enriquecimentos, mas IA pode funcionar sem contexto adicional.

**Independent Test**: Pode ser testado verificando que `ContextBuilder` injeta conteudo de `docs/context/*.md` nos prompts da IA.

**Acceptance Scenarios**:

1. **Given** arquivo `docs/context/invoice_status.md` existente
   **When** IA processa campo `status` da tabela `credit.invoice`
   **Then** conteudo de `invoice_status.md` e incluido no prompt
   **And** IA usa informacoes do documento para gerar `enum_meanings` mais precisos

2. **Given** novo campo sem documentacao de contexto
   **When** IA processa o campo
   **Then** enriquecimento e gerado apenas com informacoes do schema (sample_values, unique_values, tipo)

---

### Edge Cases

- **E se API OpenAI estiver indisponivel?**: Sistema exibe erro claro e permite retry manual. Campos nao processados ficam como `pending_enrichment`.
- **E se LLM gerar enum_meanings com valores que nao existem em unique_values?**: Validator rejeita e loga warning. Apenas valores existentes sao aceitos.
- **E se arquivo YAML for editado manualmente durante enriquecimento?**: Sistema faz backup antes de salvar e preserva campos manuais via merge.
- **E se campo ja estiver enriquecido?**: Por padrao, sistema pula. Flag `--force` permite re-enriquecer.
- **E se descricao exceder 100 caracteres?**: Validator trunca com warning no log.
- **E se campo tiver >50 valores unicos?**: `enumerable = false`, logo `enum_meanings` nao e gerado (apenas description e synonyms).
- **E se LLM gerar mais de 10 synonyms?**: Validator mantém apenas os 10 primeiros com warning no log.

---

## Requirements

### Functional Requirements

**Schemas e Persistencia**:
- **FR-001**: Sistema DEVE atualizar `source.schema.json` com propriedades `description`, `domain_category`, `search_synonyms`, `enum_meanings`, `business_rules`
- **FR-002**: Sistema DEVE atualizar `ColumnMetadataYaml` em Pydantic com os 5 novos campos opcionais
- **FR-003**: Sistema DEVE criar enum `DomainCategory` com valores: `financial`, `temporal`, `identification`, `status`, `configuration`
- **FR-004**: Sistema DEVE preservar campos semanticos ao re-extrair schema (merge inteligente)
- **FR-005**: Sistema DEVE fazer backup do YAML antes de qualquer modificacao

**Servico de Enriquecimento**:
- **FR-006**: Sistema DEVE implementar `LLMEnricher` com client OpenAI configuravel
- **FR-007**: Sistema DEVE implementar retry com backoff exponencial (3 tentativas, 2-8s delay)
- **FR-008**: Sistema DEVE validar JSON retornado pela IA contra schema esperado
- **FR-009**: Sistema DEVE priorizar campos: `presence_ratio >= 0.9`, `enumerable = true`, excluindo `_id`, `_class`, `version`
- **FR-010**: Sistema DEVE usar documentacao de contexto (`docs/context/*.md`) quando disponivel
- **FR-019**: Sistema DEVE aplicar timeout de 30 segundos por campo e 10 minutos para sessao total de enriquecimento

**CLI Interativo**:
- **FR-011**: Sistema DEVE implementar comando `enrich` com validacao humana usando componentes de `cli/shared/ui`
- **FR-012**: Sistema DEVE permitir opcoes: aprovar, editar (description, enum_meanings), rejeitar, pular, cancelar
- **FR-013**: Sistema DEVE exibir progresso em tempo real com PhaseSpinner
- **FR-014**: Sistema DEVE implementar modo `--auto-approve` para CI/CD
- **FR-015**: Sistema DEVE implementar comando `enrich-status` para visualizacao de progresso
- **FR-016**: Sistema DEVE implementar comando `enrich-all` para batch processing

**Configuracao**:
- **FR-017**: Sistema DEVE ler configuracoes LLM de `Settings` (ja existente: `openai_api_key`, `openai_model`, etc.)
- **FR-018**: Sistema DEVE suportar flag `--model` para override de modelo no CLI
- **FR-020**: Sistema DEVE usar `gpt-4o-mini` como modelo padrao para enriquecimento (custo estimado ~$0.01/campo)

### Key Entities

- **FieldEnrichment**: DTO com campos semanticos gerados pela IA (`description`, `domain_category`, `search_synonyms`, `enum_meanings`, `business_rules`)
- **DomainCategory**: Enum com categorias de dominio de negocio
- **EnrichmentStatus**: Enum existente - extender se necessario
- **ColumnMetadataYaml**: Entidade existente - estender com novos campos opcionais

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 80% dos campos prioritarios (enumerable + presence >= 0.9) enriquecidos em 1 mes
- **SC-002**: 90% dos enriquecimentos aprovados sem edicao manual (acuracia da IA)
- **SC-003**: Tempo de enriquecimento < 5 minutos para tabela media (20 campos)
- **SC-004**: Custo por campo < $0.02 (OpenAI API)
- **SC-005**: Cobertura de testes > 80% para servico de enriquecimento
- **SC-006**: Zero erros de mypy/ruff em todos os modulos novos
- **SC-007**: Validacao de schemas passa para todos os YAMLs com campos enriquecidos

---

## Technical Decisions (Reference)

### Estrutura de Arquivos Proposta

```
src/
├── services/
│   └── enrichment/                     # NOVO
│       ├── __init__.py
│       ├── llm_enricher.py             # OpenAI client + retry
│       ├── context_builder.py          # Monta prompt com contexto
│       ├── field_selector.py           # Seleciona campos prioritarios
│       ├── validator.py                # Valida output do LLM
│       └── prompts.py                  # Templates de prompt
│
├── cli/
│   ├── catalog.py                      # Adicionar commands enrich*
│   └── enrichment/                     # NOVO: UI especifica
│       ├── __init__.py
│       └── panels.py                   # Paineis de exibicao
│
├── schemas/
│   ├── catalog_yaml.py                 # Atualizar ColumnMetadataYaml
│   ├── enums.py                        # Adicionar DomainCategory
│   └── enrichment.py                   # NOVO: schemas de enriquecimento
│
docs/
└── context/                            # Documentacao de dominio
    ├── card_status_bloqueios.md        # Existente
    ├── invoice_status.md               # NOVO
    └── account_types.md                # NOVO
```

### Prompt Template (Referencia)

```python
ENRICHMENT_PROMPT = """
Voce e um especialista em sistemas bancarios e de pagamento do PicPay.
Seu objetivo e enriquecer metadados de campos de banco de dados com contexto semantico.

## Contexto da Tabela
- Database: {db_name}
- Table: {table_name}

## Campo a Enriquecer
- Path: {field_path}
- Type: {field_type}
- Enumerable: {is_enumerable}
- Sample Values: {sample_values}
{unique_values_section}

## Documentacao de Referencia
{context_docs}

## Tarefa
Gere um enriquecimento semantico no formato JSON:

{
  "description": "Descricao clara em portugues (max 100 chars)",
  "domain_category": "status|financial|temporal|identification|configuration",
  "search_synonyms": ["array", "de", "termos", "alternativos"],
  "enum_meanings": {"valor1": "Significado", "valor2": "Significado"},
  "business_rules": "Regras de negocio ou null"
}

Retorne APENAS o JSON, sem comentarios.
"""
```

---

## Out of Scope

- Integracao com outros LLMs alem de OpenAI (futuro)
- Interface web para enriquecimento (apenas CLI)
- Enriquecimento automatico em CI/CD sem revisao (apenas manual ou com --auto-approve explicito)
- Traducao automatica de enriquecimentos para ingles
- Versionamento de enriquecimentos (historico de mudancas)

---

## References

- [Implementation Plan](plan.md)
- [Tasks Breakdown](tasks.md)
- [Plano Detalhado (Legacy)](../../docs/plans/02P-catalog-ai-enrichment.md)
- [Dependencia: CLI Shared UI](../003-cli-shared-ui/spec.md)
- [Schema JSON Atual](../../catalog/schema/source.schema.json)
- [Schema Pydantic Atual](../../src/schemas/catalog_yaml.py)
- [Documentacao de Contexto](../../docs/context/)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
