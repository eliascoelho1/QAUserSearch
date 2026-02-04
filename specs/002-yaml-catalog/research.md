# Research: Catálogo de Metadados em YAML

**Feature Branch**: `002-yaml-catalog`  
**Date**: 2026-02-03

## Summary

Este documento consolida as pesquisas técnicas necessárias para implementar a migração do catálogo de metadados de PostgreSQL para arquivos YAML.

---

## 1. YAML Library Selection

### Decision: PyYAML (sem preservação de comentários)

**Rationale**: O user input especificou usar PyYAML (já instalado no projeto). Após análise da spec, a funcionalidade de preservar comentários YAML (FR-015) durante re-extração é uma feature "nice-to-have" mas não crítica para a primeira versão.

**Alternativas Consideradas**:

| Library | Preserva Comentários | Performance | Complexidade |
|---------|---------------------|-------------|--------------|
| PyYAML | Não | Rápido (LibYAML) | Simples |
| ruamel.yaml | Sim | Mais lento | Mais complexo |

**Trade-off**: Se a preservação de comentários se tornar crítica no futuro, pode-se migrar para `ruamel.yaml` com refactoring mínimo (mesmo API básica).

### Implementation Pattern

```python
import yaml
from typing import Any
from pathlib import Path

def load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load YAML file using safe loader."""
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data

def dump_yaml(data: dict[str, Any], path: Path) -> None:
    """Dump data to YAML file with consistent formatting."""
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )
```

---

## 2. In-Memory Cache with TTL

### Decision: AsyncTTLCache with threading.Lock + asyncio.Lock

**Rationale**: FastAPI usa modelo híbrido (async + thread pool). Precisamos de:
- `threading.Lock` para proteger a estrutura de dados
- `asyncio.Lock` por chave para evitar thundering herd

**Alternativas Consideradas**:

| Approach | Thread-Safe | Thundering Herd | Complexidade |
|----------|-------------|-----------------|--------------|
| Simple dict + Lock | Sim | Não | Baixa |
| cachetools.TTLCache | Sim | Não | Baixa |
| Custom AsyncTTLCache | Sim | Sim | Média |
| Redis | Sim | Sim | Alta |

**Trade-off**: O user input especificou "dict simples + timestamps (sem dependência extra)". A implementação inclui prevenção de thundering herd porque é crítico para evitar I/O excessivo quando o cache expira.

### Implementation Pattern

```python
from dataclasses import dataclass
from typing import Generic, TypeVar
import threading
import asyncio
import time

T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class CacheEntry(Generic[T]):
    value: T
    expires_at: float

class AsyncTTLCache(Generic[T]):
    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self._ttl = ttl_seconds
        self._data: dict[str, CacheEntry[T]] = {}
        self._data_lock = threading.Lock()
        self._key_locks: dict[str, asyncio.Lock] = {}
        self._key_locks_lock = asyncio.Lock()

    async def get_or_load(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
    ) -> T:
        # Fast path: check valid cache
        cached = self._get_if_valid(key)
        if cached is not None:
            return cached

        # Slow path: acquire per-key lock
        key_lock = await self._get_key_lock(key)
        async with key_lock:
            # Double-check after lock
            cached = self._get_if_valid(key)
            if cached is not None:
                return cached

            # Load and cache
            value = await loader()
            self._set(key, value)
            return value
```

---

## 3. JSON Schema Validation

### Decision: jsonschema library with types-jsonschema

**Rationale**: 
- Única opção com type stubs oficiais para mypy strict
- Suporte a Draft-07 e drafts mais recentes
- Mensagens de erro detalhadas (path, context)

**Alternativas Consideradas**:

| Library | Type Stubs | Performance | Draft Support |
|---------|------------|-------------|---------------|
| jsonschema | Sim (oficial) | 0.44s compiled | 04-2020-12 |
| fastjsonschema | Não | 0.1s | 04-07 only |

**Trade-off**: Performance ligeiramente inferior, mas type safety é crítico para o projeto.

### Implementation Pattern

```python
from typing import Any
from jsonschema import Draft7Validator, ValidationError

SOURCE_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "db_name": {"type": "string", "minLength": 1},
        "table_name": {"type": "string", "minLength": 1},
        "document_count": {"type": "integer", "minimum": 0},
        "extracted_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "columns": {
            "type": "array",
            "items": {"$ref": "#/$defs/column"},
            "minItems": 1,
        },
    },
    "required": ["db_name", "table_name", "document_count", "extracted_at", "columns"],
    "$defs": {
        "column": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "required": {"type": "boolean"},
                "nullable": {"type": "boolean"},
                "enumerable": {"type": "boolean"},
                "presence_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                "sample_values": {"type": "array"},
                "unique_values": {"type": "array"},
                "description": {"type": "string"},
                "enrichment_status": {"type": "string"},
            },
            "required": ["path", "name", "type", "required", "nullable", "enumerable", "presence_ratio"],
        },
    },
}

class CatalogValidator:
    def __init__(self) -> None:
        Draft7Validator.check_schema(SOURCE_SCHEMA)
        self._validator = Draft7Validator(SOURCE_SCHEMA)

    def validate(self, data: dict[str, Any]) -> list[str]:
        errors = list(self._validator.iter_errors(data))
        return [
            f"Campo '{'.'.join(str(p) for p in e.absolute_path) or 'root'}': {e.message}"
            for e in errors
        ]
```

---

## 4. Protocol Design for Repository Abstraction

### Decision: Python Protocol (PEP 544) para duck typing

**Rationale**: O projeto já usa Protocol para `ExternalDataSource`. Manter consistência com padrão existente.

### Implementation Pattern

```python
from typing import Protocol, Any

class CatalogRepositoryProtocol(Protocol):
    """Protocol for catalog data access."""

    def get_source_by_id(self, source_id: str) -> dict[str, Any] | None:
        """Get source metadata by ID (db_name.table_name)."""
        ...

    def get_source_by_identity(
        self, db_name: str, table_name: str
    ) -> dict[str, Any] | None:
        """Get source by database and table name."""
        ...

    def list_sources(
        self, db_name: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List sources with optional filtering."""
        ...

    def count_sources(self, db_name: str | None = None) -> int:
        """Count total sources."""
        ...
```

**Nota**: O Protocol define interface sync, mas a implementação do `CatalogFileRepository` usa async internamente para o loader do cache. A interface do Protocol é sync porque o cache retorna imediatamente quando há hit.

---

## 5. YAML File Structure

### Decision: Estrutura hierárquica por db_name/table_name

```
catalog/
├── catalog.yaml              # Índice global
├── schema/
│   └── source.schema.json    # JSON Schema para validação
└── sources/
    ├── credit/
    │   ├── invoice.yaml
    │   └── closed_invoice.yaml
    └── card_account_authorization/
        ├── account_main.yaml
        └── card_main.yaml
```

### Index File Format (catalog.yaml)

```yaml
# Catalog Index - Auto-generated by qa-catalog CLI
version: "1.0"
generated_at: "2026-02-03T10:30:00Z"
sources:
  - db_name: credit
    table_name: invoice
    last_extracted: "2026-02-03T10:30:00Z"
    file_path: sources/credit/invoice.yaml
  - db_name: credit
    table_name: closed_invoice
    last_extracted: "2026-02-03T10:30:00Z"
    file_path: sources/credit/closed_invoice.yaml
```

### Source File Format ({table_name}.yaml)

```yaml
# Source: credit.invoice
# Extracted: 2026-02-03T10:30:00Z
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
      - "507f1f77bcf86cd799439012"
    description: null  # Editable by QA
    enrichment_status: not_enriched

  - path: status
    name: status
    type: string
    required: true
    nullable: false
    enumerable: true
    presence_ratio: 1.0
    unique_values:
      - OPEN
      - PAID
      - OVERDUE
      - CANCELLED
    sample_values:
      - OPEN
      - PAID
    description: "Status da fatura"  # Manually added
    enrichment_status: enriched
```

---

## 6. Dependencies to Add

### Production Dependencies

```toml
# Already installed:
# - pyyaml>=6.0.0

# New:
jsonschema = ">=4.26.0"
```

### Dev Dependencies

```toml
# New:
types-jsonschema = ">=4.26.0"
```

**Installation**:
```bash
uv add jsonschema
uv add --dev types-jsonschema
```

---

## 7. API ID Strategy

### Decision: Use composite key `{db_name}.{table_name}` as string ID

**Rationale**: Com a migração para arquivos YAML, não há mais IDs numéricos auto-incrementados do PostgreSQL. O identificador natural é a combinação `db_name.table_name`.

**Alternativas Consideradas**:

| Strategy | Pros | Cons |
|----------|------|------|
| Numeric (hash) | Backward compatible | Não determinístico, colisões |
| Composite string | Natural, legível, único | Breaking change na API |
| UUID | Único, padrão | Não legível, sem significado |

**Migration Path**: 
- GET `/catalog/sources` retorna `id` como string `"credit.invoice"`
- GET `/catalog/sources/{source_id}` aceita tanto `"credit.invoice"` quanto formato legado `"1"` (para compatibilidade temporária)

---

## 8. Configuration Settings

### New Settings to Add

```python
# src/config/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Catalog YAML Storage
    catalog_path: str = Field(
        default="catalog",
        description="Path to catalog YAML files directory",
    )
    catalog_cache_ttl_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="TTL for catalog cache in seconds",
    )
```

---

## Resolved Clarifications

| Item | Resolution |
|------|------------|
| Comment preservation | Deferred - PyYAML sem preservação por ora |
| Cache thread safety | AsyncTTLCache com dual-lock pattern |
| JSON Schema library | jsonschema com types-jsonschema |
| Repository interface | Protocol sync com cache async interno |
| API ID format | Composite string `db_name.table_name` |
