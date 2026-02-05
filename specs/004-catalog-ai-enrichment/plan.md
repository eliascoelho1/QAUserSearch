# Implementation Plan: Enriquecimento Semantico do Catalogo com IA

**Branch**: `004-catalog-ai-enrichment` | **Date**: 2026-02-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/speckit.specify`

---

## Summary

Pipeline para adicionar metadados semanticos ao catalogo YAML existente usando LLM (OpenAI). O sistema enriquece campos do catalogo com 5 novos atributos semanticos (`description`, `domain_category`, `search_synonyms`, `enum_meanings`, `business_rules`) para que o LLM interprete corretamente buscas em linguagem natural.

**Abordagem Tecnica**: Servico de enriquecimento com OpenAI, validacao humana interativa via CLI (usando infraestrutura existente em `cli/shared/ui`), e persistencia em YAML com merge inteligente de campos existentes.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.115+, OpenAI API (via httpx/asyncio), Pydantic 2.10+, structlog, typer, rich, questionary
**Storage**: YAML files (catalog/sources/), JSON Schema para validacao
**Testing**: pytest 8.3+, pytest-asyncio, pytest-cov (TDD obrigatorio)
**Target Platform**: Linux server / macOS (CLI)
**Project Type**: Single project (extensao do projeto existente)
**Performance Goals**: <5 minutos para enriquecer tabela media (20 campos), <$0.02/campo
**Constraints**: Timeout 30s/campo, 10min/sessao, max 10 synonyms, max 100 chars description
**Scale/Scope**: 4 tabelas conhecidas, ~130 campos totais, expansivel

---

## Constitution Check

*GATE: Validado contra `.specify/memory/constitution.md`*

| Principio | Status | Notas |
|-----------|--------|-------|
| I. Qualidade de Codigo | OK | Lint/mypy strict, SRP, funcoes tipadas |
| II. TDD | OK | Testes unitarios + integracao + contrato obrigatorios |
| III. UX Consistency | OK | Usa componentes de `cli/shared/ui` existentes |
| IV. Performance | OK | SLAs definidos (30s/campo, 10min/sessao) |

**Quality Gates**:
- Lint zero warnings: Obrigatorio
- Cobertura >= 80%: Obrigatorio
- mypy strict: Obrigatorio
- Code review: Obrigatorio

---

## Project Structure

### Documentation (this feature)

```text
specs/004-catalog-ai-enrichment/
├── spec.md         # Feature specification
├── plan.md         # Este arquivo - Implementation plan
└── tasks.md        # Tasks breakdown
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── catalog.py                      # MODIFICAR: adicionar commands enrich*
│   └── enrichment/                     # NOVO: UI especifica de enriquecimento
│       ├── __init__.py
│       └── panels.py                   # Paineis de exibicao de enriquecimento
│
├── schemas/
│   ├── catalog_yaml.py                 # MODIFICAR: estender ColumnMetadataYaml
│   ├── enums.py                        # MODIFICAR: adicionar DomainCategory
│   └── enrichment.py                   # NOVO: schemas de enriquecimento
│
├── services/
│   └── enrichment/                     # NOVO: servico de enriquecimento
│       ├── __init__.py
│       ├── llm_enricher.py             # OpenAI client + retry
│       ├── context_builder.py          # Monta prompt com contexto
│       ├── field_selector.py           # Seleciona campos prioritarios
│       ├── validator.py                # Valida output do LLM
│       └── prompts.py                  # Templates de prompt
│
├── config/
│   └── config.py                       # MODIFICAR: adicionar configs de enrichment
│
catalog/
└── schema/
    └── source.schema.json              # MODIFICAR: adicionar campos semanticos

docs/
└── context/                            # EXISTENTE: documentacao de dominio
    ├── card_status_bloqueios.md        # EXISTENTE
    ├── invoice_status.md               # NOVO (opcional)
    └── account_types.md                # NOVO (opcional)

tests/
├── unit/
│   └── services/
│       └── enrichment/                 # NOVO: testes unitarios
│           ├── test_llm_enricher.py
│           ├── test_context_builder.py
│           ├── test_field_selector.py
│           ├── test_validator.py
│           └── test_prompts.py
├── integration/
│   └── test_enrichment_flow.py         # NOVO: fluxo completo
└── contract/
    └── test_enrichment_schema.py       # NOVO: validacao JSON Schema
```

**Structure Decision**: Extensao do projeto existente (Option 1 - Single project). Novos modulos seguem padrao estabelecido com servicos em `src/services/`, schemas em `src/schemas/`, CLI em `src/cli/`.

---

## Complexity Tracking

> Nenhuma violacao identificada. Arquitetura segue padroes existentes.

---

## Phase 0: Research & Dependencies

### 0.1 Dependencias Existentes Verificadas

| Dependencia | Versao | Status |
|-------------|--------|--------|
| openai (indireto via crewai) | - | Verificar se precisa adicao direta |
| httpx | 0.28.0 | Disponivel para async HTTP |
| rich | 14.3.2 | Disponivel |
| questionary | 2.1.1 | Disponivel |
| typer | 0.15.0 | Disponivel |

**Decisao**: Usar `httpx` diretamente para chamadas OpenAI API (mais controle sobre retry/timeout) em vez de SDK oficial.

### 0.2 Padroes Existentes a Reutilizar

1. **CLI UI Components** (`src/cli/shared/ui/`) - Veja [../003-cli-shared-ui](../003-cli-shared-ui/spec.md):
   - `spinner()`, `PhaseSpinner` para progresso
   - `ask_approval()`, `ask_text()`, `ask_select()` para interacao
   - `success_panel()`, `error_panel()`, `info_panel()` para feedback
   - `COLORS`, `ICONS` para tema consistente

2. **Schemas Pydantic** (`src/schemas/`):
   - Padrao `to_yaml_dict()` / `from_yaml_dict()` para serializacao
   - Campos opcionais com `Field(default=None)`
   - Enums com `str, Enum` para JSON serialization

3. **Config** (`src/config/config.py`):
   - Ja possui `openai_api_key`, `openai_model`, `openai_timeout`, `openai_max_retries`
   - Adicionar configs especificas de enrichment

4. **Catalog Validator** (`src/services/catalog_validator.py`):
   - Reutilizar para validar YAMLs apos enriquecimento

---

## Phase 1: Data Model & Contracts

### 1.1 Novos Schemas Pydantic

#### `src/schemas/enums.py` - Adicoes

```python
class DomainCategory(str, Enum):
    """Categoria de dominio de negocio para campos."""
    
    STATUS = "status"           # Estados, flags, situacoes
    FINANCIAL = "financial"     # Valores monetarios, limites
    TEMPORAL = "temporal"       # Datas, periodos, timestamps
    IDENTIFICATION = "identification"  # IDs, codigos, chaves
    CONFIGURATION = "configuration"    # Configs, parametros
```

#### `src/schemas/enrichment.py` - Novo

```python
class FieldEnrichment(BaseModel):
    """Enriquecimento semantico de um campo."""
    
    description: str = Field(..., max_length=100)
    domain_category: DomainCategory
    search_synonyms: list[str] = Field(default_factory=list, max_length=10)
    enum_meanings: dict[str, str] | None = Field(default=None)
    business_rules: str | None = Field(default=None)

class EnrichmentRequest(BaseModel):
    """Request para enriquecimento de campo."""
    
    db_name: str
    table_name: str
    field_path: str
    field_type: InferredType
    sample_values: list[Any]
    unique_values: list[Any] | None = None
    is_enumerable: bool = False

class EnrichmentResult(BaseModel):
    """Resultado de enriquecimento com metadados."""
    
    field_path: str
    enrichment: FieldEnrichment | None
    status: EnrichmentStatus
    error: str | None = None
    tokens_used: int = 0
    latency_ms: int = 0
```

#### `src/schemas/catalog_yaml.py` - Modificacoes

```python
class ColumnMetadataYaml(BaseModel):
    # ... campos existentes ...
    
    # Novos campos semanticos (opcionais)
    domain_category: DomainCategory | None = Field(default=None)
    search_synonyms: list[str] | None = Field(default=None)
    enum_meanings: dict[str, str] | None = Field(default=None)
    business_rules: str | None = Field(default=None)
```

### 1.2 JSON Schema Atualizado

Adicionar ao `catalog/schema/source.schema.json`:

```json
{
  "$defs": {
    "column": {
      "properties": {
        "domain_category": {
          "type": "string",
          "enum": ["status", "financial", "temporal", "identification", "configuration"],
          "description": "Categoria de dominio do campo"
        },
        "search_synonyms": {
          "type": "array",
          "items": { "type": "string" },
          "maxItems": 10,
          "description": "Termos alternativos para busca"
        },
        "enum_meanings": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Significado de valores enumeraveis"
        },
        "business_rules": {
          "type": ["string", "null"],
          "description": "Regras de negocio associadas"
        }
      }
    }
  }
}
```

### 1.3 Config Additions

```python
# src/config/config.py - Adicoes

# Enrichment Configuration
openai_enrichment_model: str = Field(
    default="gpt-4o-mini",
    description="Modelo para enriquecimento (menor custo)",
)
enrichment_timeout_per_field: int = Field(
    default=30,
    ge=10,
    le=120,
    description="Timeout por campo em segundos",
)
enrichment_session_timeout: int = Field(
    default=600,  # 10 minutos
    ge=60,
    le=3600,
    description="Timeout total da sessao de enriquecimento",
)
enrichment_max_synonyms: int = Field(
    default=10,
    ge=1,
    le=20,
    description="Maximo de sinonimos por campo",
)
enrichment_max_description_length: int = Field(
    default=100,
    ge=50,
    le=200,
    description="Tamanho maximo da descricao",
)
```

---

## Phase 2: Implementation Phases

### Fase 2.1: Schemas e Infraestrutura (P1 - Prerequisito)

**Objetivo**: Atualizar schemas e infraestrutura para suportar novos campos semanticos.

**Tarefas**:
1. Adicionar `DomainCategory` enum em `src/schemas/enums.py`
2. Criar `src/schemas/enrichment.py` com `FieldEnrichment`, `EnrichmentRequest`, `EnrichmentResult`
3. Estender `ColumnMetadataYaml` com campos semanticos
4. Atualizar `to_yaml_dict()` e `from_yaml_dict()` para novos campos
5. Atualizar `source.schema.json` com novas propriedades
6. Adicionar configs de enrichment em `config.py`
7. Escrever testes de serializacao/deserializacao

**Criterio de Aceite**: `uv run qa-catalog validate` passa com YAMLs contendo novos campos.

---

### Fase 2.2: Servico de Enriquecimento LLM (P1 - Core)

**Objetivo**: Implementar servico que chama OpenAI API com retry e validacao.

**Componentes**:

#### `src/services/enrichment/prompts.py`
- `ENRICHMENT_SYSTEM_PROMPT`: Contexto do sistema
- `ENRICHMENT_USER_PROMPT_TEMPLATE`: Template com placeholders
- `build_prompt(request: EnrichmentRequest, context: str | None) -> str`

#### `src/services/enrichment/context_builder.py`
- `ContextBuilder` class
- `load_context_for_table(db_name: str, table_name: str) -> str | None`
- Busca em `docs/context/*.md` por match de nome

#### `src/services/enrichment/field_selector.py`
- `FieldSelector` class
- `select_priority_fields(columns: list[ColumnMetadataYaml]) -> list[ColumnMetadataYaml]`
- Criterios: `presence_ratio >= 0.9`, `enumerable = true`, excluir `_id`, `_class`, `version`
- `is_enrichable(column: ColumnMetadataYaml) -> bool`

#### `src/services/enrichment/validator.py`
- `EnrichmentValidator` class
- `validate_enrichment(enrichment: FieldEnrichment, column: ColumnMetadataYaml) -> list[str]`
- Validacoes:
  - `description` <= 100 chars (truncar com warning)
  - `search_synonyms` <= 10 itens (manter primeiros)
  - `enum_meanings` keys existem em `unique_values`
  - `domain_category` e valido

#### `src/services/enrichment/llm_enricher.py`
- `LLMEnricher` class
- `async enrich_field(request: EnrichmentRequest) -> EnrichmentResult`
- Retry com backoff exponencial (3 tentativas, 2-8s delay)
- Timeout de 30s por chamada
- Parsing de JSON com fallback para erro
- Logging estruturado com tokens/latencia

**Tarefas**:
1. Criar estrutura de diretorios `src/services/enrichment/`
2. Implementar `prompts.py` com templates
3. Implementar `context_builder.py` com carga de docs
4. Implementar `field_selector.py` com filtros
5. Implementar `validator.py` com validacoes
6. Implementar `llm_enricher.py` com client async
7. Escrever testes unitarios com mocks da API

**Criterio de Aceite**: Servico retorna `FieldEnrichment` valido para campo de teste.

---

### Fase 2.3: CLI Interativo - Comando `enrich` (P1 - Core)

**Objetivo**: Implementar CLI interativo para enriquecimento com validacao humana.

**Dependencia**: Reusa infraestrutura de UI de [../003-cli-shared-ui](../003-cli-shared-ui/spec.md)

**Componentes**:

#### `src/cli/enrichment/panels.py`
- `EnrichmentPanel` class (usa `rich`)
- `render_enrichment(field: ColumnMetadataYaml, enrichment: FieldEnrichment) -> Panel`
- Exibe campo original e enriquecimento gerado lado a lado
- Destaca `enum_meanings` com tabela

#### `src/cli/catalog.py` - Novos comandos

```python
@app.command()
def enrich(
    db_name: Annotated[str, typer.Argument(...)],
    table_name: Annotated[str, typer.Argument(...)],
    fields: Annotated[list[str] | None, typer.Option("--fields", "-f")] = None,
    auto_approve: Annotated[bool, typer.Option("--auto-approve")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
    model: Annotated[str | None, typer.Option("--model")] = None,
) -> None:
    """Enrich catalog fields with AI-generated semantic metadata."""
```

**Fluxo Interativo**:
1. Carregar YAML da tabela
2. Selecionar campos (todos ou `--fields`)
3. Para cada campo:
   a. Chamar `LLMEnricher.enrich_field()`
   b. Exibir painel com resultado
   c. Se `--auto-approve`: salvar direto
   d. Senao: `ask_approval()` com opcoes:
      - Aprovar
      - Editar description
      - Editar enum_meanings
      - Rejeitar
      - Pular
      - Cancelar
4. Salvar YAML com campos aprovados
5. Exibir resumo

**Tarefas**:
1. Criar `src/cli/enrichment/__init__.py` e `panels.py`
2. Implementar `EnrichmentPanel.render_enrichment()`
3. Adicionar comando `enrich` em `catalog.py`
4. Implementar fluxo interativo com `ask_approval()`
5. Implementar edicao inline de campos
6. Implementar salvamento com backup
7. Escrever testes com mock de input

**Criterio de Aceite**: Usuario pode enriquecer `credit.invoice` e aprovar/editar campos.

---

### Fase 2.4: CLI - Status e Batch (P2)

**Objetivo**: Implementar comandos de visualizacao de status e batch processing.

#### Comando `enrich-status`

```python
@app.command()
def enrich_status() -> None:
    """Show enrichment progress for all catalog sources."""
```

Exibe tabela com:
- Source | Total | Enriched | Progress Bar | %

#### Comando `enrich-pending`

```python
@app.command()
def enrich_pending(
    source: Annotated[str | None, typer.Argument(...)] = None,
) -> None:
    """List fields pending enrichment."""
```

#### Comando `enrich-all`

```python
@app.command()
def enrich_all(
    auto_approve: Annotated[bool, typer.Option("--auto-approve")] = False,
    priority_only: Annotated[bool, typer.Option("--priority-only")] = False,
    batch_size: Annotated[int, typer.Option("--batch-size")] = 10,
) -> None:
    """Enrich all catalog sources in batch."""
```

**Tarefas**:
1. Implementar `enrich_status` com tabela rich
2. Implementar `enrich_pending` com lista agrupada
3. Implementar `enrich_all` com loop e pausa por batch
4. Escrever testes para cada comando

**Criterio de Aceite**: Usuario visualiza progresso e pode enriquecer em batch.

---

### Fase 2.5: Documentacao de Contexto (P3)

**Objetivo**: Criar documentacao de contexto para melhorar qualidade de enriquecimentos.

**Tarefas**:
1. Criar `docs/context/invoice_status.md` com descricao de status de fatura
2. Criar `docs/context/account_types.md` com tipos de conta
3. Atualizar `ContextBuilder` para carregar docs relevantes
4. Testar melhoria de qualidade com contexto

**Criterio de Aceite**: Enriquecimentos com contexto sao mais precisos.

---

## Phase 3: Testing Strategy

### 3.1 Testes Unitarios (Obrigatorios)

| Modulo | Arquivo | Cobertura |
|--------|---------|-----------|
| prompts | `test_prompts.py` | 100% |
| context_builder | `test_context_builder.py` | 100% |
| field_selector | `test_field_selector.py` | 100% |
| validator | `test_validator.py` | 100% |
| llm_enricher | `test_llm_enricher.py` | 90%+ |
| enrichment schemas | `test_enrichment_schemas.py` | 100% |

### 3.2 Testes de Integracao

| Cenario | Arquivo |
|---------|---------|
| Fluxo completo de enriquecimento | `test_enrichment_flow.py` |
| Persistencia YAML com merge | `test_yaml_persistence.py` |
| Retry e timeout | `test_llm_retry.py` |

### 3.3 Testes de Contrato

| Contrato | Arquivo |
|----------|---------|
| JSON Schema com novos campos | `test_enrichment_schema.py` |
| Pydantic serialization | `test_catalog_yaml.py` |

---

## Phase 4: Rollout Plan

### 4.1 Ordem de Implementacao

1. **Semana 1**: Fase 2.1 (Schemas) + Fase 2.2 (Servico LLM)
2. **Semana 2**: Fase 2.3 (CLI enrich)
3. **Semana 3**: Fase 2.4 (Status/Batch) + Fase 2.5 (Contexto)
4. **Semana 4**: Testes finais, documentacao, enriquecimento inicial

### 4.2 Checkpoints

| Checkpoint | Criterio |
|------------|----------|
| CP1 | Schemas validam, testes unitarios passam |
| CP2 | Servico LLM funciona com mock |
| CP3 | CLI enrich funciona interativamente |
| CP4 | Batch e status funcionam |
| CP5 | 80% dos campos prioritarios enriquecidos |

---

## Success Metrics

| Metrica | Target | Medicao |
|---------|--------|---------|
| Cobertura de testes | >= 80% | `pytest --cov` |
| Zero erros mypy/ruff | 100% | `uv run mypy && uv run ruff check` |
| Tempo por campo | < 30s | Logs de latencia |
| Custo por campo | < $0.02 | Tokens usados |
| Acuracia IA (aprovados sem edicao) | >= 90% | Metricas CLI |
| Campos prioritarios enriquecidos | >= 80% em 1 mes | `enrich-status` |

---

## References

- [Especificacao](spec.md)
- [Tasks Breakdown](tasks.md)
- [Constituicao](../../.specify/memory/constitution.md)
- [Dependencia: CLI Shared UI](../003-cli-shared-ui/spec.md)
- [Schema JSON Atual](../../catalog/schema/source.schema.json)
- [Schema Pydantic Atual](../../src/schemas/catalog_yaml.py)
- [CLI Shared UI](../../src/cli/shared/ui/)
- [Documentacao de Contexto](../../docs/context/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
