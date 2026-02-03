# Data Model: Catálogo de Metadados em YAML

**Feature Branch**: `002-yaml-catalog`  
**Date**: 2026-02-03

## Entity Overview

Este documento define as entidades e estruturas de dados para o catálogo de metadados em YAML.

---

## 1. CatalogIndex

**Propósito**: Índice global listando todas as sources disponíveis no catálogo.

**Localização**: `catalog/catalog.yaml`

### Campos

| Campo | Tipo | Required | Descrição |
|-------|------|----------|-----------|
| version | string | Sim | Versão do formato do índice (semver) |
| generated_at | datetime (ISO 8601) | Sim | Timestamp da última geração |
| sources | list[IndexEntry] | Sim | Lista de sources indexadas |

### IndexEntry (item em sources)

| Campo | Tipo | Required | Descrição |
|-------|------|----------|-----------|
| db_name | string | Sim | Nome do banco de dados |
| table_name | string | Sim | Nome da tabela/collection |
| last_extracted | datetime (ISO 8601) | Sim | Timestamp da última extração |
| file_path | string | Sim | Caminho relativo ao arquivo YAML |

### Exemplo YAML

```yaml
version: "1.0"
generated_at: "2026-02-03T10:30:00Z"
sources:
  - db_name: credit
    table_name: invoice
    last_extracted: "2026-02-03T10:30:00Z"
    file_path: sources/credit/invoice.yaml
```

### Pydantic Schema

```python
from datetime import datetime
from pydantic import BaseModel, Field

class IndexEntry(BaseModel):
    db_name: str = Field(..., min_length=1)
    table_name: str = Field(..., min_length=1)
    last_extracted: datetime
    file_path: str

class CatalogIndex(BaseModel):
    version: str = Field(default="1.0")
    generated_at: datetime
    sources: list[IndexEntry] = Field(default_factory=list)
```

---

## 2. SourceMetadata

**Propósito**: Metadados completos de uma source específica.

**Localização**: `catalog/sources/{db_name}/{table_name}.yaml`

### Campos

| Campo | Tipo | Required | Default | Descrição |
|-------|------|----------|---------|-----------|
| db_name | string | Sim | - | Nome do banco de dados |
| table_name | string | Sim | - | Nome da tabela/collection |
| document_count | integer | Sim | - | Quantidade de documentos amostrados |
| extracted_at | datetime | Sim | - | Timestamp da extração original |
| updated_at | datetime | Não | extracted_at | Timestamp da última atualização |
| columns | list[ColumnMetadata] | Sim | - | Lista de colunas/campos |

### Exemplo YAML

```yaml
db_name: credit
table_name: invoice
document_count: 15234
extracted_at: "2026-02-03T10:30:00Z"
updated_at: "2026-02-03T10:30:00Z"
columns:
  - path: _id
    name: _id
    type: objectid
    required: true
    nullable: false
    enumerable: false
    presence_ratio: 1.0
    sample_values:
      - "507f1f77bcf86cd799439011"
```

### Pydantic Schema (extensão de catalog.py)

```python
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class SourceMetadataYaml(BaseModel):
    """Source metadata for YAML serialization."""
    
    db_name: str = Field(..., min_length=1)
    table_name: str = Field(..., min_length=1)
    document_count: int = Field(..., ge=0)
    extracted_at: datetime
    updated_at: datetime | None = None
    columns: list["ColumnMetadataYaml"]

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization."""
        return {
            "db_name": self.db_name,
            "table_name": self.table_name,
            "document_count": self.document_count,
            "extracted_at": self.extracted_at.isoformat(),
            "updated_at": (self.updated_at or self.extracted_at).isoformat(),
            "columns": [col.to_yaml_dict() for col in self.columns],
        }

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "SourceMetadataYaml":
        """Create from parsed YAML dict."""
        return cls(
            db_name=data["db_name"],
            table_name=data["table_name"],
            document_count=data["document_count"],
            extracted_at=datetime.fromisoformat(data["extracted_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            columns=[ColumnMetadataYaml.from_yaml_dict(c) for c in data["columns"]],
        )
```

---

## 3. ColumnMetadata

**Propósito**: Metadados detalhados de uma coluna/campo.

### Campos

| Campo | Tipo | Required | Default | Descrição |
|-------|------|----------|---------|-----------|
| path | string | Sim | - | Caminho completo (dot notation) |
| name | string | Sim | - | Nome do campo (última parte do path) |
| type | InferredType | Sim | - | Tipo inferido do campo |
| required | boolean | Sim | - | Se o campo está presente em >= 95% dos docs |
| nullable | boolean | Sim | - | Se o campo pode ser null |
| enumerable | boolean | Sim | - | Se tem cardinalidade baixa (< 50 valores únicos) |
| presence_ratio | float | Sim | - | Percentual de presença (0.0 a 1.0) |
| sample_values | list[Any] | Sim | [] | Valores de exemplo (até 10) |
| unique_values | list[Any] | Não | null | Valores únicos (se enumerable) |
| description | string | Não | null | Descrição manual do campo |
| enrichment_status | EnrichmentStatus | Não | not_enriched | Status de enriquecimento LLM |

### InferredType (Enum)

```python
class InferredType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    OBJECTID = "objectid"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    UNKNOWN = "unknown"
```

### EnrichmentStatus (Enum)

```python
class EnrichmentStatus(str, Enum):
    NOT_ENRICHED = "not_enriched"
    PENDING_ENRICHMENT = "pending_enrichment"
    ENRICHED = "enriched"
```

### Exemplo YAML

```yaml
- path: customer.address.city
  name: city
  type: string
  required: false
  nullable: true
  enumerable: true
  presence_ratio: 0.87
  unique_values:
    - "São Paulo"
    - "Rio de Janeiro"
    - "Belo Horizonte"
  sample_values:
    - "São Paulo"
    - "Rio de Janeiro"
  description: "Cidade do endereço do cliente"
  enrichment_status: enriched
```

### Pydantic Schema (extensão de catalog.py)

```python
class ColumnMetadataYaml(BaseModel):
    """Column metadata for YAML serialization."""
    
    path: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: InferredType
    required: bool
    nullable: bool
    enumerable: bool
    presence_ratio: float = Field(..., ge=0.0, le=1.0)
    sample_values: list[Any] = Field(default_factory=list)
    unique_values: list[Any] | None = None
    description: str | None = None
    enrichment_status: EnrichmentStatus = EnrichmentStatus.NOT_ENRICHED

    def to_yaml_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization."""
        result: dict[str, Any] = {
            "path": self.path,
            "name": self.name,
            "type": self.type.value,
            "required": self.required,
            "nullable": self.nullable,
            "enumerable": self.enumerable,
            "presence_ratio": self.presence_ratio,
            "sample_values": self.sample_values,
        }
        if self.unique_values is not None:
            result["unique_values"] = self.unique_values
        if self.description is not None:
            result["description"] = self.description
        if self.enrichment_status != EnrichmentStatus.NOT_ENRICHED:
            result["enrichment_status"] = self.enrichment_status.value
        return result

    @classmethod
    def from_yaml_dict(cls, data: dict[str, Any]) -> "ColumnMetadataYaml":
        """Create from parsed YAML dict."""
        return cls(
            path=data["path"],
            name=data["name"],
            type=InferredType(data["type"]),
            required=data["required"],
            nullable=data["nullable"],
            enumerable=data["enumerable"],
            presence_ratio=data["presence_ratio"],
            sample_values=data.get("sample_values", []),
            unique_values=data.get("unique_values"),
            description=data.get("description"),
            enrichment_status=EnrichmentStatus(data.get("enrichment_status", "not_enriched")),
        )
```

---

## 4. Cache Entry

**Propósito**: Estrutura interna para gerenciamento de cache.

### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| value | T (generic) | Dados cacheados |
| expires_at | float | Timestamp de expiração (monotonic) |

### Python Dataclass

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class CacheEntry(Generic[T]):
    """Immutable cache entry with value and expiration."""
    value: T
    expires_at: float
```

---

## 5. Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                      CatalogIndex                                │
│                  (catalog/catalog.yaml)                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ sources: list[IndexEntry]                               │    │
│  │   - db_name: credit                                     │    │
│  │   - table_name: invoice                                 │───┐│
│  │   - file_path: sources/credit/invoice.yaml             │   ││
│  └─────────────────────────────────────────────────────────┘   ││
└────────────────────────────────────────────────────────────────┘│
                                                                   │
     ┌─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SourceMetadata                                │
│            (catalog/sources/credit/invoice.yaml)                 │
│                                                                  │
│  db_name: credit                                                 │
│  table_name: invoice                                             │
│  document_count: 15234                                           │
│  extracted_at: 2026-02-03T10:30:00Z                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ columns: list[ColumnMetadata]                           │    │
│  │   - path: _id                                           │    │
│  │   - path: status                                        │    │
│  │   - path: customer.name                                 │    │
│  │   - ...                                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. State Transitions

### Source Lifecycle

```
                 ┌────────────────┐
                 │   Not Exists   │
                 └───────┬────────┘
                         │ CLI: qa-catalog extract
                         ▼
                 ┌────────────────┐
                 │   Extracted    │◄───────────────┐
                 │ (YAML created) │                │
                 └───────┬────────┘                │
                         │                         │
         ┌───────────────┼───────────────┐        │
         │               │               │        │
         ▼               ▼               ▼        │
    ┌─────────┐    ┌──────────┐    ┌──────────┐  │
    │  Read   │    │ Manually │    │Re-extract│──┘
    │ via API │    │  Edited  │    │          │
    └─────────┘    └──────────┘    └──────────┘
```

### Column Enrichment Status

```
┌────────────────────┐
│   NOT_ENRICHED     │ ← Default on extraction
└─────────┬──────────┘
          │ QA adds description
          ▼
┌────────────────────┐
│     ENRICHED       │
└────────────────────┘
```

---

## 7. Validation Rules

### Source Level

- `db_name`: Não vazio, alfanumérico + underscore
- `table_name`: Não vazio, alfanumérico + underscore
- `document_count`: >= 0
- `extracted_at`: ISO 8601 datetime válido
- `columns`: Lista não vazia

### Column Level

- `path`: Não vazio, formato dot-notation válido
- `name`: Não vazio
- `type`: Deve ser valor válido de InferredType
- `presence_ratio`: Entre 0.0 e 1.0
- Se `enumerable == true`, `unique_values` deve estar presente
- `enrichment_status`: Deve ser valor válido de EnrichmentStatus

---

## 8. Migration Notes

### From PostgreSQL (existing) to YAML (new)

| PostgreSQL | YAML |
|------------|------|
| `external_sources.id` (int) | `{db_name}.{table_name}` (string) |
| `external_sources.cataloged_at` | `extracted_at` |
| `external_sources.updated_at` | `updated_at` |
| `column_metadata.id` (int) | Removido (não necessário) |
| `column_metadata.source_id` | Implícito (arquivo parent) |
| `column_metadata.inferred_type` (string) | `type` (enum) |

### Breaking Changes

1. **API ID Format**: IDs numéricos substituídos por strings `db_name.table_name`
2. **DELETE Endpoint**: Removido (sources são gerenciadas via git)
3. **Database Dependency**: Endpoints de catálogo não requerem mais PostgreSQL
