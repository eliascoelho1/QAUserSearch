# Plan: Enriquecimento Semântico do Catálogo com IA

**Data**: 2026-02-04  
**Status**: Draft  
**Autor**: Proposta baseada em análise do catálogo atual  
**Depende de**: [`01-cli-shared-ui.md`](./01-cli-shared-ui.md)

---

## Contexto

O catálogo de metadados atual (`catalog/sources/**/*.yaml`) contém informações técnicas extraídas automaticamente das fontes MongoDB (tipos, valores de exemplo, cardinalidade). No entanto, falta **contexto semântico** para que o LLM interprete corretamente prompts de usuários e gere queries precisas.

### Problema Atual

```yaml
# ANTES: Dados técnicos sem contexto
- path: block_code
  name: block_code
  type: string
  unique_values: ['', 'R', 'F', 'P', 'B', 'J']
  # ❌ LLM não sabe o que é 'R' ou 'J'
  # ❌ Usuário busca "cartão roubado" → LLM não mapeia para block_code = 'R'
```

### Objetivo

Enriquecer o catálogo com **metadados semânticos gerados por IA** para:
1. **Melhorar interpretação de prompts** - LLM entende sinônimos e linguagem natural
2. **Explicar enums crípticos** - `R` = "Roubo", `J` = "CRELI (inadimplência grave)"
3. **Categorizar por domínio** - Separar campos financeiros, temporais, de status
4. **Documentar regras de negócio** - Ex: "Bloqueio J implica status Z"

---

## Proposta de Solução

### 1. Schema Estendido

Adicionar **5 novos campos** por coluna:

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| `description` | string | Descrição semântica em português | "Código de bloqueio do cartão segundo tabela FIS" |
| `domain_category` | enum | Categoria de negócio | `status`, `financial`, `temporal`, `identification` |
| `search_synonyms` | list[str] | Termos alternativos para busca | `["bloqueado", "travado", "suspenso"]` |
| `enum_meanings` | dict[str, str] | Significado de valores enumeráveis | `{"R": "Roubo", "F": "Fraude"}` |
| `business_rules` | string \| null | Regras de negócio associadas | "Bloqueio J implica status Z" |

### 2. Exemplo de Campo Enriquecido

```yaml
# DEPOIS: Contexto semântico completo
- path: block_code
  name: block_code
  type: string
  required: true
  nullable: true
  enumerable: true
  presence_ratio: 1.0
  unique_values: ['', 'R', 'F', 'P', 'B', 'U', 'T', 'M', 'E', 'G', 'Z', 'J']
  
  # ✅ NOVOS CAMPOS (gerados por IA)
  description: "Código de bloqueio do cartão/conta. Vazio significa ativo."
  domain_category: status
  search_synonyms:
    - "bloqueio"
    - "bloqueado"
    - "travado"
    - "motivo bloqueio"
  enum_meanings:
    '': "Sem bloqueio - cartão ativo"
    'R': "Roubo - cancelamento por roubo"
    'F': "Fraude - cancelamento por fraude"
    'P': "Perda - cancelamento por perda"
    'B': "Atraso 6-30 dias"
    'U': "Cancelamento solicitado pelo cliente"
    'T': "Em transporte - aguardando entrega"
    'M': "Falecimento"
    'E': "Extravio"
    'G': "Substituição - segunda via"
    'Z': "Bloqueio temporário"
    'J': "CRELI - inadimplência grave (>67 dias)"
  business_rules: "Bloqueio J implica status Z (charge-off). Vide docs/context/card_status_bloqueios.md"
  enrichment_status: enriched
```

---

## Categorias de Domínio

```yaml
domain_categories:
  financial:       # Valores monetários (value, credit, debits, minValue)
  temporal:        # Datas e timestamps (createdAt, dueDate, updatedAt)
  identification:  # IDs e chaves (consumerId, _id, account_number)
  status:          # Estados e flags (status, block_code, archived)
  configuration:   # Parâmetros do sistema (_class, version, issuer)
```

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Pipeline de Enriquecimento com IA                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                                                     │
│  │ 1. SELEÇÃO      │   Filtrar campos prioritários                      │
│  │    (Automático) │   • presence_ratio >= 0.9                          │
│  │                 │   • enumerable = true (prioridade alta)            │
│  │                 │   • enrichment_status != enriched                  │
│  │                 │   • Exclui: _id, _class, version                   │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ 2. CONTEXTO     │   Montar prompt estruturado                        │
│  │    (Automático) │   • Nome do campo + tipo + sample_values           │
│  │                 │   • Contexto da tabela (db_name.table_name)        │
│  │                 │   • Docs/context/*.md relevantes                   │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ 3. GERAÇÃO      │   Chamar OpenAI GPT-4                              │
│  │    (LLM)        │   • Prompt: "Você é especialista em bancos..."     │
│  │                 │   • Output: JSON schema estruturado                │
│  │                 │   • Retry: 3x com backoff exponencial              │
│  │                 │   • Validação: JSON schema + lógica custom         │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ 4. VALIDAÇÃO    │   CLI interativo (usa shared/prompts)        │
│  │    (Humano)     │   ┌─────────────────────────────────┐             │
│  │                 │   │ ? O que fazer?                  │             │
│  │                 │   │   ❯ ✓ Aprovar                   │             │
│  │                 │   │     ✏️  Editar description       │             │
│  │                 │   │     ✏️  Editar enum_meanings     │             │
│  │                 │   │     ✗ Rejeitar                  │             │
│  │                 │   └─────────────────────────────────┘             │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─────────────────┐                                                     │
│  │ 5. PERSISTÊNCIA │   Atualizar YAML                                   │
│  │    (Automático) │   • Merge preservando campos manuais               │
│  │                 │   • enrichment_status = enriched                   │
│  │                 │   • Backup do arquivo original                     │
│  └─────────────────┘                                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Escopo e Priorização

### Escopo Essencial (~30% dos campos)

Com base na análise do catálogo atual:

**Alta Prioridade (enriquecer primeiro):**
1. ✅ Campos `enumerable: true` com valores crípticos
   - `status`, `block_code`, `issuer`, `origin_type`, `variant`
2. ✅ Campos de identificação cross-tabela
   - `consumerId`, `account_number`, `consumer_id`
3. ✅ Flags booleanos de negócio
   - `archived`, `isFirstInvoice`, `has_divergence`

**Filtro Técnico:**
- `presence_ratio >= 0.9` (presente em 90%+ dos documentos)
- `enumerable: true` OU `type: boolean`
- Exclui campos internos: `_id`, `_class`, `version`, `hash`

**Estatísticas (catálogo atual):**
- Total de campos: ~200 (4 tabelas × ~50 campos)
- Campos essenciais: ~60 (30%)
- Custo estimado: 60 campos × $0.01/campo = **$0.60** (OpenAI)

---

## Fluxo de Validação Interativa

### Exemplo de Sessão CLI

```bash
$ qa catalog enrich credit invoice

┌─────────────────────────────────────────────────────────────────────────┐
│  🔍 Enriquecimento Semântico: credit.invoice                             │
│                                                                          │
│  📊 Campos selecionados: 15                                              │
│  🤖 Modelo: gpt-4                                                        │
│  ⏱️  Tempo estimado: ~2 minutos                                          │
└─────────────────────────────────────────────────────────────────────────┘

⠋ Gerando enriquecimentos via IA...
  ├─ ✓ status (1/15)
  ├─ ⠙ archived (2/15)
  └─ ○ dataByFile (3/15)

╭─ 🔍 Enriquecimento: credit.invoice.status ──────────────────────────────╮
│                                                                          │
│  📊 Dados do Campo:                                                      │
│  ┌────────────────┬───────────────────────────────────────────┐         │
│  │ Path           │ status                                     │         │
│  │ Type           │ string                                     │         │
│  │ Enumerable     │ true                                       │         │
│  │ Unique Values  │ CLOSED, ADVANCE_PAYMENT, DELAYED, OPEN,    │         │
│  │                │ OPEN_PAYMENT                               │         │
│  └────────────────┴───────────────────────────────────────────┘         │
│                                                                          │
│  🤖 Enriquecimento Gerado pela IA:                                       │
│                                                                          │
│  description: "Status atual da fatura de crédito"                       │
│                                                                          │
│  domain_category: status                                                 │
│                                                                          │
│  search_synonyms:                                                        │
│    - "situação da fatura"                                               │
│    - "estado da fatura"                                                 │
│    - "fatura aberta"                                                    │
│    - "fatura fechada"                                                   │
│                                                                          │
│  enum_meanings:                                                          │
│    OPEN: "Fatura aberta - período de lançamentos ativo"                 │
│    CLOSED: "Fatura fechada - aguardando pagamento"                      │
│    DELAYED: "Fatura atrasada - vencimento ultrapassado"                 │
│    ADVANCE_PAYMENT: "Pagamento antecipado realizado"                    │
│    OPEN_PAYMENT: "Fatura em período de pagamento"                       │
│                                                                          │
│  business_rules: null                                                    │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯

? O que deseja fazer com este enriquecimento?
  ❯ ✓ Aprovar e continuar (marcar como enriched)
    ✏️  Editar description
    ✏️  Editar enum_meanings
    ✏️  Adicionar business_rules
    ✗ Rejeitar e marcar para revisão
    ⏭️  Pular este campo (manter not_enriched)
    🛑 Cancelar e sair

> ✓ Aprovar e continuar

✅ Campo 'status' enriquecido com sucesso!

⠋ Continuando... (2/15)
```

---

## CLI Commands

> **Nota**: O comando `qa` é o entry point unificado. Veja [03P-cli-chat.md](./03P-cli-chat.md) para detalhes.
> O subcomando `catalog` agrupa todas as operações de catálogo.

### Enriquecimento Individual

```bash
# Enriquecer uma tabela específica (modo interativo)
qa catalog enrich credit invoice

# Enriquecer apenas campos específicos
qa catalog enrich credit invoice --fields status,block_code,archived

# Modo automático (sem validação humana) - para CI/CD
qa catalog enrich credit invoice --auto-approve

# Especificar modelo LLM
qa catalog enrich credit invoice --model gpt-4o
```

### Enriquecimento em Batch

```bash
# Enriquecer todas as tabelas conhecidas
qa catalog enrich-all

# Modo interativo com pause a cada 5 campos
qa catalog enrich-all --interactive --batch-size 5

# Apenas campos prioritários (enumerable + presence > 0.9)
qa catalog enrich-all --priority-only
```

### Status e Estatísticas

```bash
# Ver status de enriquecimento do catálogo
qa catalog enrich-status

# Exemplo de output:
# ┌─────────────────────┬───────────┬──────────┬─────────────┐
# │ Source              │ Total     │ Enriched │ Progress    │
# ├─────────────────────┼───────────┼──────────┼─────────────┤
# │ credit.invoice      │ 18        │ 15       │ ████████░ 83% │
# │ credit.closed_inv…  │ 28        │ 0        │ ░░░░░░░░░ 0%  │
# │ card_account.card…  │ 45        │ 12       │ ███░░░░░░ 27% │
# └─────────────────────┴───────────┴──────────┴─────────────┘

# Listar campos pendentes de enriquecimento
qa catalog enrich-pending

# Re-enriquecer campos já marcados como enriched
qa catalog enrich credit invoice --force
```

---

## Estrutura de Arquivos

### Novos Módulos

```
src/
├── services/
│   ├── enrichment/                     # NOVO
│   │   ├── __init__.py
│   │   ├── llm_enricher.py            # Chamadas OpenAI + retry logic
│   │   ├── context_builder.py         # Monta contexto do prompt
│   │   ├── field_selector.py          # Seleciona campos prioritários
│   │   ├── validator.py               # Valida output do LLM
│   │   └── prompts.py                 # Templates de prompt LLM
│   └── catalog_yaml_extractor.py      # (existente)
│
├── cli/
│   ├── main.py                        # Entry point unificado `qa`
│   ├── catalog.py                     # Subcomando `qa catalog` + novos commands
│   ├── shared/                        # ← Do plano 00-cli-shared-ui.md
│   │   ├── ui/
│   │   │   ├── theme.py               # Tema de cores e estilos
│   │   │   ├── components.py          # Componentes visuais
│   │   │   ├── panels.py              # Painéis especializados
│   │   │   ├── progress.py            # Spinners e barras
│   │   │   └── prompts.py             # Prompts Questionary
│   │   └── utils/
│   │       └── terminal.py            # Utilitários de terminal
│   └── enrichment/                    # NOVO: UI específica de enriquecimento
│       ├── __init__.py
│       └── panels.py                  # Painéis de exibição de enriquecimento
│
├── schemas/
│   ├── catalog_yaml.py                # (existente) + novos campos
│   └── enrichment.py                  # NOVO: schemas de enriquecimento
│
└── config/
    └── config.py                      # (existente) + LLM configs

docs/
└── context/                           # Documentação de domínio
    ├── card_status_bloqueios.md       # (existente)
    ├── invoice_status.md              # NOVO
    └── account_types.md               # NOVO
```

### Schema JSON Atualizado

```json
// catalog/schema/source.schema.json
{
  "$defs": {
    "column": {
      "properties": {
        "path": { "type": "string" },
        "name": { "type": "string" },
        "type": { "type": "string" },
        // ... campos existentes ...
        
        "description": {
          "type": ["string", "null"],
          "description": "Descrição semântica do campo"
        },
        "domain_category": {
          "type": ["string", "null"],
          "enum": ["financial", "temporal", "identification", "status", "configuration", null],
          "description": "Categoria de domínio de negócio"
        },
        "search_synonyms": {
          "type": ["array", "null"],
          "items": { "type": "string" },
          "description": "Termos alternativos para busca"
        },
        "enum_meanings": {
          "type": ["object", "null"],
          "additionalProperties": { "type": "string" },
          "description": "Significado de valores enumeráveis"
        },
        "business_rules": {
          "type": ["string", "null"],
          "description": "Regras de negócio associadas"
        },
        "enrichment_status": {
          "type": "string",
          "enum": ["not_enriched", "pending_enrichment", "enriched"],
          "default": "not_enriched"
        }
      }
    }
  }
}
```

---

## Prompt Engineering para LLM

### Template de Prompt

```python
ENRICHMENT_PROMPT = """
Você é um especialista em sistemas bancários e de pagamento do PicPay.
Seu objetivo é enriquecer metadados de campos de banco de dados com contexto semântico.

## Contexto da Tabela
- Database: {db_name}
- Table: {table_name}
- Domínio: {domain_hint}

## Campo a Enriquecer
- Path: {field_path}
- Type: {field_type}
- Enumerable: {is_enumerable}
- Sample Values: {sample_values}
{unique_values_section}

## Documentação de Referência
{context_docs}

## Tarefa
Gere um enriquecimento semântico seguindo este JSON schema:

```json
{
  "description": "string - Descrição clara em português do que o campo representa",
  "domain_category": "status|financial|temporal|identification|configuration",
  "search_synonyms": ["array", "de", "termos", "alternativos"],
  "enum_meanings": {
    "valor1": "Significado do valor1",
    "valor2": "Significado do valor2"
  },
  "business_rules": "string ou null - Regras de negócio relevantes"
}
```

## Diretrizes
1. **description**: Máximo 100 caracteres, linguagem clara
2. **search_synonyms**: 3-8 termos que usuários reais usariam
3. **enum_meanings**: Explicar TODOS os valores únicos
4. **business_rules**: Incluir apenas se houver regras importantes
5. Use informações da documentação de referência quando disponível
6. Se não tiver certeza, seja conservador (use null)

Retorne APENAS o JSON, sem comentários ou markdown.
"""
```

### Exemplo de Contexto (docs/context/)

```markdown
# docs/context/invoice_status.md

# Status de Faturas de Crédito

## Valores Possíveis

| Código | Nome | Descrição |
|--------|------|-----------|
| OPEN | Fatura Aberta | Período de lançamentos. Cliente pode usar o cartão. |
| CLOSED | Fatura Fechada | Período fechado. Aguardando pagamento. |
| DELAYED | Fatura Atrasada | Vencimento ultrapassado. Juros sendo aplicados. |
| OPEN_PAYMENT | Em Pagamento | Fatura recebendo pagamentos parcelados. |
| ADVANCE_PAYMENT | Pago Antecipado | Cliente pagou antes do vencimento. |

## Regras de Negócio

- Faturas com status DELAYED por >30 dias geram bloqueio B (block_code)
- ADVANCE_PAYMENT só ocorre se earlyPayments > 0
- Transição: OPEN → CLOSED → DELAYED (se não pago)
```

---

## Implementação: Roadmap

> **Pré-requisito**: O plano [`01-cli-shared-ui.md`](./01-cli-shared-ui.md) deve ser implementado primeiro.

### Fase 1: Infraestrutura Base (4-5h)

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E1** | Atualizar `source.schema.json` com novos campos | 1h | P0 |
| **E2** | Atualizar `ColumnMetadataYaml` em `schemas/catalog_yaml.py` | 1h | P0 |
| **E3** | Criar enum `DomainCategory` em `schemas/enums.py` | 0.5h | P0 |
| **E4** | Atualizar `catalog_file_writer.py` para preservar novos campos | 1.5h | P0 |

**Critérios de Aceite:**
- [ ] Schema JSON válido contra JSON Schema Draft 7
- [ ] Pydantic valida YAML com novos campos
- [ ] Re-extraction preserva campos enriquecidos

---

### Fase 2: Serviço de Enriquecimento (6-7h)

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E5** | Criar `llm_enricher.py` com OpenAI client + retry | 2h | P0 |
| **E6** | Criar `context_builder.py` para montar prompts | 2h | P0 |
| **E7** | Criar `field_selector.py` com lógica de priorização | 1h | P0 |
| **E8** | Criar `validator.py` para validar output LLM | 1h | P0 |
| **E9** | Criar `prompts.py` com templates de prompt | 1h | P1 |

**Critérios de Aceite:**
- [ ] OpenAI retorna JSON válido
- [ ] Retry funciona após falha transitória
- [ ] Context builder injeta docs/context quando relevante
- [ ] Validator rejeita outputs malformados

---

### Fase 3: CLI Interativo (3-4h)

> Usa componentes de `src/cli/shared/ui/` do plano 01

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E10** | Criar `src/cli/enrichment/panels.py` com painéis específicos | 1h | P0 |
| **E11** | Adicionar command `enrich` ao CLI (usa shared/prompts) | 1.5h | P0 |
| **E12** | Adicionar command `enrich-all` ao CLI | 1h | P1 |
| **E13** | Adicionar command `enrich-status` ao CLI | 0.5h | P1 |

**Critérios de Aceite:**
- [ ] CLI exibe enriquecimento com formatação clara (usa shared/panels)
- [ ] `ask_approval` do shared permite aprovar/editar/rejeitar
- [ ] Progress bar do shared atualiza em tempo real
- [ ] Modo `--auto-approve` funciona sem interação

---

### Fase 4: Documentação de Contexto (3-4h)

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E14** | Criar `docs/context/invoice_status.md` | 1h | P1 |
| **E15** | Criar `docs/context/account_types.md` | 1h | P1 |
| **E16** | Expandir `card_status_bloqueios.md` com mais exemplos | 1h | P2 |
| **E17** | Criar índice `docs/context/README.md` | 0.5h | P2 |

**Critérios de Aceite:**
- [ ] Documentos seguem formato padronizado
- [ ] LLM consegue consumir contexto de forma eficaz
- [ ] Exemplos reais de valores e significados

---

### Fase 5: Testes e Validação (4-5h)

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E18** | Testes unitários para `llm_enricher` (mock OpenAI) | 1.5h | P0 |
| **E19** | Testes unitários para `field_selector` | 1h | P0 |
| **E20** | Testes de integração do fluxo completo | 2h | P0 |
| **E21** | Testes de contrato para novos campos no schema | 1h | P1 |

**Critérios de Aceite:**
- [ ] Cobertura de testes > 80%
- [ ] Zero erros de mypy/ruff
- [ ] Testes de integração passam com mock OpenAI

---

### Fase 6: Enriquecimento Inicial (2-3h)

| ID | Tarefa | Estimativa | Prioridade |
|----|--------|------------|------------|
| **E22** | Enriquecer `credit.invoice` (15 campos) | 1h | P0 |
| **E23** | Enriquecer `credit.closed_invoice` (20 campos) | 1h | P1 |
| **E24** | Enriquecer `card_account.card_main` (25 campos) | 1.5h | P1 |

**Critérios de Aceite:**
- [ ] Campos prioritários enriquecidos e aprovados
- [ ] YAML arquivos validam contra schema
- [ ] API retorna campos enriquecidos corretamente

---

**Total Estimado**: ~21-26 horas (~3 dias de trabalho)

> Nota: Tempo reduzido em ~2-3h pois infraestrutura de UI vem do plano 00.

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **LLM gera enriquecimentos incorretos** | Média | Alto | Validação humana obrigatória no CLI; criar test cases de referência |
| **Custos de API OpenAI mais altos que estimado** | Baixa | Médio | Usar modelo mais barato (gpt-4o-mini); cache de prompts similares |
| **Context builder injeta docs errados** | Média | Médio | Testar com múltiplos cenários; permitir override manual |
| **Performance lenta em batch** | Baixa | Médio | Paralelizar chamadas OpenAI (max 5 concurrent); usar batch API se disponível |

---

## Métricas de Sucesso

### Quantitativas
1. **Cobertura de enriquecimento**: ≥80% dos campos prioritários enriquecidos em 1 mês
2. **Acurácia do LLM**: ≥90% dos enriquecimentos aprovados sem edição
3. **Tempo de enriquecimento**: <5 minutos para tabela média (20 campos)
4. **Custo por campo**: <$0.02 (OpenAI API)

### Qualitativas
1. **Melhoria na interpretação de prompts**: Usuários conseguem usar sinônimos naturais
2. **Redução de ambiguidades**: LLM entende corretamente valores de enum
3. **Documentação viva**: Catálogo serve como referência de negócio

---

## Próximos Passos

1. ✅ **Validar proposta** com stakeholders
2. ⏳ **Criar branch** `003-catalog-ai-enrichment`
3. ⏳ **Iniciar Fase 1**: Atualizar schemas
4. ⏳ **Desenvolver POC** com 1 tabela (credit.invoice)
5. ⏳ **Iterar** baseado em feedback do POC
6. ⏳ **Escalar** para todas as tabelas

---

## Referências

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [JSON Schema Draft 7](https://json-schema.org/draft-07/schema)
- [Questionary Documentation](https://questionary.readthedocs.io/)
- [Catálogo atual](../../catalog/sources/)
- [Documentação de contexto](../context/)
- [Schema JSON](../../catalog/schema/source.schema.json)

---

**Última Atualização**: 2026-02-04
