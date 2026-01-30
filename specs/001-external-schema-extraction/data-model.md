# Data Model: Extração Automática de Schema de Bancos Externos

**Feature Branch**: `001-external-schema-extraction`  
**Date**: 2026-01-30  
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CATALOG (PostgreSQL)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐         1:N         ┌────────────────────────┐ │
│  │   ExternalSource    │◄────────────────────│    ColumnMetadata      │ │
│  ├─────────────────────┤                     ├────────────────────────┤ │
│  │ id: int (PK)        │                     │ id: int (PK)           │ │
│  │ db_name: str        │                     │ source_id: int (FK)    │ │
│  │ table_name: str     │                     │ column_name: str       │ │
│  │ cataloged_at: dt    │                     │ column_path: str       │ │
│  │ updated_at: dt      │                     │ inferred_type: str     │ │
│  │ document_count: int │                     │ is_required: bool      │ │
│  └─────────────────────┘                     │ is_nullable: bool      │ │
│                                              │ is_enumerable: bool    │ │
│         ▲                                    │ unique_values: json    │ │
│         │                                    │ sample_values: json    │ │
│         │                                    │ presence_ratio: float  │ │
│         │ UNIQUE(db_name, table_name)        │ description: str?      │ │
│                                              │ enrichment_status: str │ │
│                                              │ created_at: dt         │ │
│                                              │ updated_at: dt         │ │
│                                              └────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL DATA SOURCES                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐        ┌──────────────────────┐              │
│  │   MOCK Environment   │        │   PROD Environment   │              │
│  ├──────────────────────┤        ├──────────────────────┤              │
│  │ res/db/*.json        │        │ MongoDB Atlas        │              │
│  │                      │        │                      │              │
│  │ account_main.json    │        │ card_account_auth DB │              │
│  │ card_main.json       │        │ credit DB            │              │
│  │ invoice.json         │        │                      │              │
│  │ closed_invoice.json  │        │                      │              │
│  └──────────────────────┘        └──────────────────────┘              │
│            │                              │                             │
│            └──────────┬───────────────────┘                             │
│                       ▼                                                 │
│          ┌────────────────────────┐                                     │
│          │  ExternalDataSource    │                                     │
│          │      (Protocol)        │                                     │
│          ├────────────────────────┤                                     │
│          │ get_sample_documents() │                                     │
│          └────────────────────────┘                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Entity Definitions

### ExternalSource

Representa uma fonte de dados externa (combinação de nome do banco + nome da tabela).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, auto-increment | Identificador único |
| `db_name` | `str(100)` | NOT NULL, indexed | Nome do banco de dados externo |
| `table_name` | `str(100)` | NOT NULL, indexed | Nome da tabela/collection |
| `cataloged_at` | `datetime` | NOT NULL, default=now() | Data da primeira catalogação |
| `updated_at` | `datetime` | NOT NULL, auto-update | Data da última atualização |
| `document_count` | `int` | NOT NULL, default=0 | Número de documentos na última amostra |

**Constraints**:
- UNIQUE(`db_name`, `table_name`) - Combinação única de banco + tabela

**SQLAlchemy Model**:

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class ExternalSource(Base):
    __tablename__ = "external_sources"
    __table_args__ = (
        UniqueConstraint("db_name", "table_name", name="uq_source_identity"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    db_name: Mapped[str] = mapped_column(String(100), index=True)
    table_name: Mapped[str] = mapped_column(String(100), index=True)
    cataloged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationship
    columns: Mapped[list["ColumnMetadata"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
```

---

### ColumnMetadata

Representa uma coluna dentro de uma fonte externa.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `int` | PK, auto-increment | Identificador único |
| `source_id` | `int` | FK(external_sources.id), NOT NULL | Referência à fonte |
| `column_name` | `str(255)` | NOT NULL | Nome da coluna (último segmento do path) |
| `column_path` | `str(500)` | NOT NULL | Caminho completo no JSON (dot notation) |
| `inferred_type` | `str(50)` | NOT NULL | Tipo inferido (string, integer, number, boolean, datetime, objectid, array, object, null, unknown) |
| `is_required` | `bool` | NOT NULL, default=False | True se presente em ≥95% dos documentos |
| `is_nullable` | `bool` | NOT NULL, default=True | True se pelo menos um valor null encontrado |
| `is_enumerable` | `bool` | NOT NULL, default=False | True se cardinalidade ≤ limite configurado |
| `unique_values` | `json` | NULL | Lista de valores únicos (quando is_enumerable=True) |
| `sample_values` | `json` | NULL | Amostra de 5 valores para referência |
| `presence_ratio` | `float` | NOT NULL | Porcentagem de documentos com este campo (0.0-1.0) |
| `description` | `str(1000)` | NULL | Descrição semântica (futuro: preenchida por LLM) |
| `enrichment_status` | `str(20)` | NOT NULL, default='not_enriched' | Status: not_enriched, pending_enrichment, enriched |
| `created_at` | `datetime` | NOT NULL, default=now() | Data de criação |
| `updated_at` | `datetime` | NOT NULL, auto-update | Data da última atualização |

**Constraints**:
- UNIQUE(`source_id`, `column_path`) - Combinação única de fonte + caminho
- CHECK(`presence_ratio` >= 0.0 AND `presence_ratio` <= 1.0)
- CHECK(`enrichment_status` IN ('not_enriched', 'pending_enrichment', 'enriched'))

**SQLAlchemy Model**:

```python
from datetime import datetime
from typing import Any
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class ColumnMetadata(Base):
    __tablename__ = "column_metadata"
    __table_args__ = (
        UniqueConstraint("source_id", "column_path", name="uq_column_identity"),
        CheckConstraint("presence_ratio >= 0.0 AND presence_ratio <= 1.0", name="ck_presence_ratio"),
        CheckConstraint(
            "enrichment_status IN ('not_enriched', 'pending_enrichment', 'enriched')", 
            name="ck_enrichment_status"
        ),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"), index=True)
    column_name: Mapped[str] = mapped_column(String(255))
    column_path: Mapped[str] = mapped_column(String(500))
    inferred_type: Mapped[str] = mapped_column(String(50))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enumerable: Mapped[bool] = mapped_column(Boolean, default=False)
    unique_values: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    sample_values: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    presence_ratio: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enrichment_status: Mapped[str] = mapped_column(String(20), default="not_enriched")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationship
    source: Mapped["ExternalSource"] = relationship(back_populates="columns")
```

---

## Enums

### EnrichmentStatus

```python
class EnrichmentStatus(str, Enum):
    """Status de enriquecimento via LLM."""
    NOT_ENRICHED = "not_enriched"        # Padrão: nunca processado
    PENDING_ENRICHMENT = "pending_enrichment"  # Falha/timeout, aguardando retry
    ENRICHED = "enriched"                # Descrição gerada com sucesso
```

### InferredType

```python
class InferredType(str, Enum):
    """Tipos de dados inferidos do JSON."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"          # Float
    BOOLEAN = "boolean"
    DATETIME = "datetime"      # ISO 8601 strings
    OBJECTID = "objectid"      # MongoDB ObjectId (24 hex chars)
    ARRAY = "array"
    OBJECT = "object"          # Nested object
    NULL = "null"              # Apenas null encontrado
    UNKNOWN = "unknown"        # Tipo não determinado
```

### DataSourceEnvironment

```python
class DataSourceEnvironment(str, Enum):
    """Ambiente de fonte de dados externos."""
    MOCK = "MOCK"    # Arquivos JSON locais em res/db/
    PROD = "PROD"    # Conexão direta ao MongoDB
```

---

## Validation Rules

### ExternalSource

| Rule | Validation |
|------|------------|
| db_name | 1-100 caracteres, apenas alfanumérico + underscore |
| table_name | 1-100 caracteres, apenas alfanumérico + underscore |

### ColumnMetadata

| Rule | Validation |
|------|------------|
| column_name | 1-255 caracteres, não pode iniciar com número |
| column_path | 1-500 caracteres, formato dot notation válido |
| inferred_type | Deve ser valor válido do enum InferredType |
| presence_ratio | 0.0 ≤ valor ≤ 1.0 |
| unique_values | Quando is_enumerable=True, deve ter 1-50 valores |
| enrichment_status | Deve ser valor válido do enum EnrichmentStatus |

---

## State Transitions

### EnrichmentStatus

```
                    ┌─────────────────┐
                    │  not_enriched   │ (estado inicial)
                    └────────┬────────┘
                             │
                             │ trigger_enrichment()
                             │ (futuro: v2)
                             ▼
           ┌─────────────────────────────────┐
           │                                 │
    LLM OK │                                 │ LLM fail/timeout
           │                                 │
           ▼                                 ▼
┌──────────────────┐              ┌────────────────────────┐
│     enriched     │              │  pending_enrichment    │
└──────────────────┘              └───────────┬────────────┘
                                              │
                                              │ retry_enrichment()
                                              │
                                              ▼
                                   (retorna ao fluxo acima)
```

---

## Database Indexes

```sql
-- ExternalSource
CREATE INDEX ix_external_sources_db_name ON external_sources(db_name);
CREATE INDEX ix_external_sources_table_name ON external_sources(table_name);

-- ColumnMetadata
CREATE INDEX ix_column_metadata_source_id ON column_metadata(source_id);
CREATE INDEX ix_column_metadata_inferred_type ON column_metadata(inferred_type);
CREATE INDEX ix_column_metadata_is_enumerable ON column_metadata(is_enumerable);
CREATE INDEX ix_column_metadata_enrichment_status ON column_metadata(enrichment_status);
```

---

## Sample Data

### ExternalSource

| id | db_name | table_name | cataloged_at | document_count |
|----|---------|------------|--------------|----------------|
| 1 | card_account_authorization | account_main | 2026-01-30 10:00:00 | 500 |
| 2 | card_account_authorization | card_main | 2026-01-30 10:01:00 | 500 |
| 3 | credit | invoice | 2026-01-30 10:02:00 | 500 |
| 4 | credit | closed_invoice | 2026-01-30 10:03:00 | 500 |

### ColumnMetadata (amostra para account_main)

| id | source_id | column_name | column_path | inferred_type | is_required | is_enumerable | unique_values |
|----|-----------|-------------|-------------|---------------|-------------|---------------|---------------|
| 1 | 1 | _id | _id | objectid | true | false | null |
| 2 | 1 | consumer_id | consumer_id | string | true | false | null |
| 3 | 1 | status | status | string | true | true | ["A", "B", "C"] |
| 4 | 1 | issuer | issuer | string | true | true | ["PICPAY", "VISA"] |
| 5 | 1 | type | product_data.type | string | false | true | ["HYBRID_LEVERAGED", "STANDARD"] |
| 6 | 1 | enabled | guaranteed_limit.enabled | boolean | false | true | [false, true] |
