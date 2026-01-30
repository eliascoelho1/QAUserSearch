# Research: Extração Automática de Schema de Bancos Externos

**Feature Branch**: `001-external-schema-extraction`  
**Date**: 2026-01-30  
**Status**: Complete

## 1. Inferência de Tipos JSON em Python

### Decision: Implementação customizada com Pydantic para validação

### Rationale
- **genson** gera JSON Schema mas é overkill para nosso caso (apenas precisamos inferir tipos, não gerar schema completo)
- **pydantic** já está no projeto (v2.10+) e oferece validação de tipos robusta
- Implementação customizada permite controle fino sobre regras específicas do domínio (datas ISO 8601, ObjectId do MongoDB)

### Alternatives Considered
| Alternativa | Motivo da Rejeição |
|-------------|-------------------|
| genson | Dependência adicional, output JSON Schema não necessário |
| jsonschema | Foco em validação, não inferência |
| dataclasses-json | Menos flexível que Pydantic |

### Implementation Pattern

```python
from typing import Any
from datetime import datetime
import re

class TypeInferrer:
    """Infere tipos de dados a partir de valores JSON."""
    
    ISO8601_PATTERN = re.compile(
        r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
    )
    OBJECTID_PATTERN = re.compile(r'^[a-f0-9]{24}$')
    
    def infer_type(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            if self.ISO8601_PATTERN.match(value):
                return "datetime"
            if self.OBJECTID_PATTERN.match(value):
                return "objectid"
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        return "unknown"
```

---

## 2. Detecção de Campos Obrigatórios vs Opcionais

### Decision: Análise estatística com threshold de 95%

### Rationale
- Campos presentes em >95% dos documentos são considerados obrigatórios (FR-003)
- Threshold configurável permite ajuste por tabela se necessário
- Simples de implementar e entender

### Implementation Pattern

```python
from collections import defaultdict
from typing import Any

def analyze_field_presence(documents: list[dict[str, Any]]) -> dict[str, float]:
    """Retorna porcentagem de presença de cada campo."""
    total = len(documents)
    if total == 0:
        return {}
    
    field_counts = defaultdict(int)
    
    for doc in documents:
        for field in _flatten_fields(doc):
            field_counts[field] += 1
    
    return {
        field: count / total 
        for field, count in field_counts.items()
    }

def is_required(presence_ratio: float, threshold: float = 0.95) -> bool:
    """Determina se campo é obrigatório baseado no threshold."""
    return presence_ratio >= threshold
```

---

## 3. Tratamento de Estruturas Aninhadas

### Decision: Notação de caminho com ponto (dot notation)

### Rationale
- Padrão amplamente utilizado (MongoDB, Elasticsearch, jq)
- Permite reconstrução da hierarquia quando necessário
- Facilita queries e filtros no catálogo

### Implementation Pattern

```python
def flatten_fields(obj: dict, prefix: str = "") -> dict[str, Any]:
    """Achata estruturas aninhadas usando dot notation."""
    fields = {}
    
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            fields.update(flatten_fields(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Array de objetos: usa notação [*]
            fields.update(flatten_fields(value[0], f"{full_key}[*]"))
        else:
            fields[full_key] = value
    
    return fields
```

### Exemplo de Output

```json
// Input
{
  "product_data": {
    "origin_flow": "manual",
    "type": "HYBRID"
  },
  "guaranteed_limit": {
    "enabled": false
  }
}

// Output (campos achatados)
{
  "product_data.origin_flow": "manual",
  "product_data.type": "HYBRID",
  "guaranteed_limit.enabled": false
}
```

---

## 4. Detecção de Colunas Enumeráveis

### Decision: Análise estatística de cardinalidade (sem LLM)

### Rationale
- FR-028 especifica detecção puramente estatística
- Limite configurável de 50 valores únicos por padrão (FR-029)
- LLM focará apenas em descrições semânticas (escopo futuro v2)

### Implementation Pattern

```python
from collections import Counter

def analyze_cardinality(
    values: list[Any], 
    limit: int = 50
) -> tuple[bool, list[Any] | None]:
    """
    Analisa cardinalidade de valores para detecção de enumeráveis.
    
    Returns:
        (is_enumerable, unique_values or None)
    """
    # Remove None values para análise
    non_null = [v for v in values if v is not None]
    
    if not non_null:
        return False, None
    
    unique = set(non_null)
    
    if len(unique) <= limit:
        # Ordena por frequência (mais comum primeiro)
        counter = Counter(non_null)
        sorted_values = [v for v, _ in counter.most_common()]
        return True, sorted_values
    
    return False, None
```

---

## 5. SQLAlchemy 2.0 Async - Padrões de Implementação

### Decision: Repository Pattern com Generic Base + Session injetada

### Rationale
- Projeto já usa SQLAlchemy 2.0 async com asyncpg
- Padrão Repository facilita testes (mock de session)
- Generic base evita duplicação de CRUD

### Implementation Pattern

```python
from typing import Generic, TypeVar, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self._session = session
        self._model = model
    
    async def get_by_id(self, id: int) -> T | None:
        result = await self._session.execute(
            select(self._model).where(self._model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> Sequence[T]:
        result = await self._session.execute(select(self._model))
        return result.scalars().all()
    
    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        return entity
```

### Relacionamentos One-to-Many (ExternalSource → ColumnMetadata)

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class ExternalSource(Base):
    __tablename__ = "external_sources"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    db_name: Mapped[str]
    table_name: Mapped[str]
    
    columns: Mapped[list["ColumnMetadata"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin"  # Async-safe loading
    )

class ColumnMetadata(Base):
    __tablename__ = "column_metadata"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("external_sources.id"))
    
    source: Mapped["ExternalSource"] = relationship(back_populates="columns")
```

---

## 6. Conexão MongoDB em Ambiente PROD

### Decision: Motor (driver async oficial) com connection pooling

### Rationale
- Motor é o único driver async-first para MongoDB
- FastAPI requer operações não-bloqueantes
- Pool de conexões essencial para performance em produção

### Implementation Pattern

```python
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

class MongoDBManager:
    def __init__(self, uri: str):
        self._client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            connectTimeoutMS=10000,
            maxPoolSize=50,
            minPoolSize=10,
            retryWrites=True,
        )
    
    async def sample_documents(
        self, 
        db_name: str, 
        collection_name: str, 
        sample_size: int = 500
    ) -> list[dict]:
        """Amostra documentos para inferência de schema."""
        db = self._client[db_name]
        collection = db[collection_name]
        
        # $sample para amostragem aleatória eficiente
        pipeline = [{"$sample": {"size": sample_size}}]
        cursor = collection.aggregate(pipeline)
        return await cursor.to_list(length=sample_size)
    
    async def close(self):
        self._client.close()
```

### Configuração Recomendada (.env)

```bash
# MongoDB External (PROD only)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
MONGODB_SAMPLE_SIZE=500
```

---

## 7. Estratégia de Ambientes (MOCK vs PROD)

### Decision: Interface abstrata com implementações apartadas

### Rationale
- FR-018 exige repositórios apartados com interface comum
- Factory Pattern seleciona implementação baseado em configuração
- Código de negócio não conhece a origem dos dados (FR-019)

### Implementation Pattern

```python
from abc import ABC, abstractmethod
from typing import Protocol

class ExternalDataSource(Protocol):
    """Interface para acesso a dados externos."""
    
    async def get_sample_documents(
        self, 
        db_name: str, 
        table_name: str, 
        sample_size: int
    ) -> list[dict]:
        """Retorna amostra de documentos para inferência."""
        ...

class MockExternalDataSource:
    """Implementação MOCK - lê arquivos JSON locais."""
    
    def __init__(self, base_path: str = "res/db"):
        self._base_path = base_path
    
    async def get_sample_documents(
        self, db_name: str, table_name: str, sample_size: int
    ) -> list[dict]:
        import aiofiles
        import json
        
        filename = f"{db_name}.{table_name}.json"
        path = f"{self._base_path}/{filename}"
        
        async with aiofiles.open(path) as f:
            content = await f.read()
            documents = json.loads(content)
            return documents[:sample_size]

class ProdExternalDataSource:
    """Implementação PROD - conecta ao MongoDB real."""
    
    def __init__(self, mongodb_manager: MongoDBManager):
        self._mongo = mongodb_manager
    
    async def get_sample_documents(
        self, db_name: str, table_name: str, sample_size: int
    ) -> list[dict]:
        return await self._mongo.sample_documents(
            db_name, table_name, sample_size
        )

# Factory
def get_external_data_source(env: str) -> ExternalDataSource:
    if env == "MOCK":
        return MockExternalDataSource()
    elif env == "PROD":
        return ProdExternalDataSource(get_mongodb_manager())
    raise ValueError(f"Unknown environment: {env}")
```

---

## 8. Dependências Adicionais Necessárias

### Novas dependências para pyproject.toml

```toml
dependencies = [
    # ... existentes ...
    "aiofiles>=24.1.0",       # Leitura async de arquivos JSON (MOCK)
    "motor>=3.6.0",           # MongoDB async driver (PROD)
]
```

### Rationale
- **aiofiles**: Operações de arquivo não-bloqueantes para ambiente MOCK
- **motor**: Driver oficial async do MongoDB para ambiente PROD

---

## Resumo de Decisões

| Área | Decisão | Justificativa |
|------|---------|---------------|
| Inferência de tipos | Implementação customizada | Controle sobre regras de domínio |
| Campos opcionais | Threshold 95% | Simplicidade + configurável |
| Estruturas aninhadas | Dot notation | Padrão de mercado |
| Enumeráveis | Cardinalidade ≤50 | FR-028/FR-029 |
| Repository | Generic Base + Session | Padrão existente no projeto |
| MongoDB driver | Motor | Único async-first |
| Ambientes | Interface + Factory | FR-018/FR-019 |
