# Data Model: Extração Automática de Schema de Bancos Externos

**Feature Branch**: `001-external-schema-extraction`  
**Date**: 2026-01-29  
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CATALOG SCHEMA                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐         ┌─────────────────────────────────────────────┐
│   ExternalSource    │ 1     * │              ColumnMetadata                 │
├─────────────────────┤─────────├─────────────────────────────────────────────┤
│ id: UUID [PK]       │         │ id: UUID [PK]                               │
│ db_name: str        │         │ source_id: UUID [FK]                        │
│ table_name: str     │         │ column_name: str                            │
│ created_at: datetime│         │ column_path: str                            │
│ updated_at: datetime│         │ inferred_type: str                          │
│ extraction_status:  │         │ is_required: bool                           │
│   enum              │         │ is_enumerable: bool                         │
│ total_columns: int  │         │ enumerable_values: JSON                     │
│ enriched_columns:   │         │ semantic_description: str|null              │
│   int               │         │ enrichment_status: enum                     │
└─────────────────────┘         │ sample_values: JSON                         │
         │                      │ parent_path: str|null                       │
         │                      │ depth: int                                  │
         │                      │ occurrence_rate: float                      │
         │                      │ created_at: datetime                        │
         │                      │ updated_at: datetime                        │
         │                      └─────────────────────────────────────────────┘
         │
         │ (UNIQUE: db_name + table_name)
         │
```

## Entities

### ExternalSource

Representa uma fonte de dados externa (combinação de banco + tabela).

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | PK, auto-generated | Identificador único |
| `db_name` | VARCHAR(100) | NOT NULL | Nome do banco externo (ex: `card_account_authorization`) |
| `table_name` | VARCHAR(100) | NOT NULL | Nome da tabela (ex: `account_main`) |
| `created_at` | TIMESTAMP | NOT NULL, default NOW | Data de criação do registro |
| `updated_at` | TIMESTAMP | NOT NULL, onupdate NOW | Data da última atualização |
| `extraction_status` | ENUM | NOT NULL, default 'pending' | Status: `pending`, `in_progress`, `completed`, `failed` |
| `total_columns` | INTEGER | default 0 | Total de colunas extraídas |
| `enriched_columns` | INTEGER | default 0 | Colunas com descrição semântica |

**Constraints**:
- `UNIQUE(db_name, table_name)` - Identificação única da fonte

**Business Rules**:
- Combinação `db_name` + `table_name` identifica unicamente uma fonte (FR-006)
- `updated_at` reflete timestamp da última extração (FR-007)
- Re-extração atualiza colunas existentes (FR-008)

---

### ColumnMetadata

Representa uma coluna dentro de uma fonte externa com seus metadados.

| Campo | Tipo | Constraints | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | PK, auto-generated | Identificador único |
| `source_id` | UUID | FK → ExternalSource.id, NOT NULL | Referência à fonte |
| `column_name` | VARCHAR(200) | NOT NULL | Nome do campo (último segmento do path) |
| `column_path` | VARCHAR(500) | NOT NULL | Path completo com dot notation (ex: `product_data.type`) |
| `inferred_type` | VARCHAR(50) | NOT NULL | Tipo inferido: `string`, `number`, `boolean`, `date`, `array`, `object`, `null`, `unknown` |
| `is_required` | BOOLEAN | NOT NULL, default true | Campo obrigatório (presente em >95% das amostras) |
| `is_enumerable` | BOOLEAN | NOT NULL, default false | Cardinalidade ≤ limite configurável (FR-025) |
| `enumerable_values` | JSONB | nullable | Lista de valores únicos quando `is_enumerable=true` (FR-026) |
| `semantic_description` | TEXT | nullable | Descrição gerada pela LLM |
| `enrichment_status` | ENUM | NOT NULL, default 'pending' | Status: `pending`, `enriched`, `pending_enrichment`, `skipped` |
| `sample_values` | JSONB | nullable | Até 5 valores de exemplo para contexto |
| `parent_path` | VARCHAR(500) | nullable | Path do objeto pai (para campos aninhados) |
| `depth` | INTEGER | NOT NULL, default 1 | Nível de aninhamento (1 = root) |
| `occurrence_rate` | DECIMAL(5,4) | NOT NULL | % de documentos que contêm este campo (0.0000 a 1.0000) |
| `created_at` | TIMESTAMP | NOT NULL, default NOW | Data de criação |
| `updated_at` | TIMESTAMP | NOT NULL, onupdate NOW | Data da última atualização |

**Constraints**:
- `UNIQUE(source_id, column_path)` - Um path é único por fonte
- `FK(source_id) → ExternalSource(id) ON DELETE CASCADE`

**Business Rules**:
- `is_required = occurrence_rate >= 0.95` (FR-003)
- `is_enumerable = true` quando cardinalidade ≤ `ENUMERABLE_CARDINALITY_LIMIT` (FR-027)
- `enumerable_values` preenchido apenas quando `is_enumerable=true` (FR-026)
- `enrichment_status = 'pending_enrichment'` quando LLM falha (FR-023)
- `depth = column_path.count('.') + 1` (campos aninhados)

---

## Enums

### ExtractionStatus

```python
class ExtractionStatus(str, Enum):
    PENDING = "pending"           # Aguardando extração
    IN_PROGRESS = "in_progress"   # Extração em andamento
    COMPLETED = "completed"       # Extração concluída com sucesso
    FAILED = "failed"             # Extração falhou
```

### EnrichmentStatus

```python
class EnrichmentStatus(str, Enum):
    PENDING = "pending"                    # Aguardando enriquecimento
    ENRICHED = "enriched"                  # Descrição gerada com sucesso
    PENDING_ENRICHMENT = "pending_enrichment"  # Falha na LLM, aguardando retry (FR-023)
    SKIPPED = "skipped"                    # Enriquecimento ignorado (campo técnico)
```

### InferredType

```python
class InferredType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE = "date"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    UNKNOWN = "unknown"  # Quando não foi possível inferir (FR-003 scenario 3)
```

---

## State Transitions

### ExternalSource.extraction_status

```
         ┌──────────┐
         │ pending  │
         └────┬─────┘
              │ start_extraction()
              ▼
       ┌─────────────┐
       │ in_progress │
       └──────┬──────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌───────────┐     ┌─────────┐
│ completed │     │ failed  │
└───────────┘     └────┬────┘
                       │ retry_extraction()
                       └──────► pending
```

### ColumnMetadata.enrichment_status

```
         ┌──────────┐
         │ pending  │
         └────┬─────┘
              │ enrich()
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌──────────┐    ┌───────────────────┐
│ enriched │    │ pending_enrichment│
└──────────┘    └─────────┬─────────┘
                          │ retry_enrich()
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
          ┌──────────┐    ┌───────────────────┐
          │ enriched │    │ skipped (max retry)│
          └──────────┘    └───────────────────┘
```

---

## Validation Rules

### ExternalSource

| Campo | Validação | Mensagem de Erro |
|-------|-----------|------------------|
| `db_name` | min_length=1, max_length=100, pattern=`^[a-z_]+$` | "Nome do banco deve conter apenas letras minúsculas e underscore" |
| `table_name` | min_length=1, max_length=100, pattern=`^[a-z_]+$` | "Nome da tabela deve conter apenas letras minúsculas e underscore" |

### ColumnMetadata

| Campo | Validação | Mensagem de Erro |
|-------|-----------|------------------|
| `column_path` | pattern=`^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$` | "Path inválido" |
| `occurrence_rate` | ge=0.0, le=1.0 | "Taxa de ocorrência deve estar entre 0 e 1" |
| `enumerable_values` | max_items=50 quando `is_enumerable=true` | "Máximo de 50 valores enumeráveis" |

---

## Indexes

### ExternalSource

```sql
-- Busca por fonte específica
CREATE UNIQUE INDEX idx_external_sources_db_table 
ON external_sources(db_name, table_name);

-- Listagem por status
CREATE INDEX idx_external_sources_status 
ON external_sources(extraction_status);
```

### ColumnMetadata

```sql
-- Busca de colunas por fonte
CREATE INDEX idx_column_metadata_source_id 
ON column_metadata(source_id);

-- Busca por path (para queries em campos aninhados)
CREATE INDEX idx_column_metadata_path 
ON column_metadata(column_path);

-- Busca de colunas pendentes de enriquecimento
CREATE INDEX idx_column_metadata_enrichment_status 
ON column_metadata(enrichment_status) 
WHERE enrichment_status IN ('pending', 'pending_enrichment');

-- Busca de colunas enumeráveis
CREATE INDEX idx_column_metadata_enumerable 
ON column_metadata(is_enumerable) 
WHERE is_enumerable = true;
```

---

## Sample Data

### ExternalSource

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "db_name": "card_account_authorization",
  "table_name": "account_main",
  "created_at": "2026-01-29T10:00:00Z",
  "updated_at": "2026-01-29T10:05:00Z",
  "extraction_status": "completed",
  "total_columns": 35,
  "enriched_columns": 32
}
```

### ColumnMetadata

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "column_name": "status",
    "column_path": "status",
    "inferred_type": "string",
    "is_required": true,
    "is_enumerable": true,
    "enumerable_values": ["A", "B", "C", "I"],
    "semantic_description": "Status da conta: A (Ativa), B (Bloqueada), C (Cancelada), I (Inativa)",
    "enrichment_status": "enriched",
    "sample_values": ["A", "A", "B", "A", "C"],
    "parent_path": null,
    "depth": 1,
    "occurrence_rate": 1.0000,
    "created_at": "2026-01-29T10:00:00Z",
    "updated_at": "2026-01-29T10:05:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "column_name": "type",
    "column_path": "product_data.type",
    "inferred_type": "string",
    "is_required": true,
    "is_enumerable": true,
    "enumerable_values": ["HYBRID_LEVERAGED", "PURE_CREDIT", "DEBIT"],
    "semantic_description": "Tipo de produto do cartão: alavancado híbrido, crédito puro ou débito",
    "enrichment_status": "enriched",
    "sample_values": ["HYBRID_LEVERAGED", "HYBRID_LEVERAGED", "PURE_CREDIT"],
    "parent_path": "product_data",
    "depth": 2,
    "occurrence_rate": 0.9800,
    "created_at": "2026-01-29T10:00:00Z",
    "updated_at": "2026-01-29T10:05:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440003",
    "source_id": "550e8400-e29b-41d4-a716-446655440000",
    "column_name": "annual_fee",
    "column_path": "annual_fee",
    "inferred_type": "number",
    "is_required": false,
    "is_enumerable": false,
    "enumerable_values": null,
    "semantic_description": null,
    "enrichment_status": "pending_enrichment",
    "sample_values": [null, null, 99.90, null, 149.90],
    "parent_path": null,
    "depth": 1,
    "occurrence_rate": 0.1200,
    "created_at": "2026-01-29T10:00:00Z",
    "updated_at": "2026-01-29T10:05:00Z"
  }
]
```

---

## Migration Script

```sql
-- Migration: 001_create_catalog_tables.sql

CREATE TYPE extraction_status AS ENUM (
    'pending', 'in_progress', 'completed', 'failed'
);

CREATE TYPE enrichment_status AS ENUM (
    'pending', 'enriched', 'pending_enrichment', 'skipped'
);

CREATE TABLE external_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    db_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    extraction_status extraction_status NOT NULL DEFAULT 'pending',
    total_columns INTEGER NOT NULL DEFAULT 0,
    enriched_columns INTEGER NOT NULL DEFAULT 0,
    UNIQUE(db_name, table_name)
);

CREATE TABLE column_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES external_sources(id) ON DELETE CASCADE,
    column_name VARCHAR(200) NOT NULL,
    column_path VARCHAR(500) NOT NULL,
    inferred_type VARCHAR(50) NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT true,
    is_enumerable BOOLEAN NOT NULL DEFAULT false,
    enumerable_values JSONB,
    semantic_description TEXT,
    enrichment_status enrichment_status NOT NULL DEFAULT 'pending',
    sample_values JSONB,
    parent_path VARCHAR(500),
    depth INTEGER NOT NULL DEFAULT 1,
    occurrence_rate DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(source_id, column_path)
);

-- Indexes
CREATE INDEX idx_external_sources_status ON external_sources(extraction_status);
CREATE INDEX idx_column_metadata_source_id ON column_metadata(source_id);
CREATE INDEX idx_column_metadata_path ON column_metadata(column_path);
CREATE INDEX idx_column_metadata_enrichment_status ON column_metadata(enrichment_status) 
    WHERE enrichment_status IN ('pending', 'pending_enrichment');
CREATE INDEX idx_column_metadata_enumerable ON column_metadata(is_enumerable) 
    WHERE is_enumerable = true;

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_external_sources_updated_at
    BEFORE UPDATE ON external_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_column_metadata_updated_at
    BEFORE UPDATE ON column_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```
