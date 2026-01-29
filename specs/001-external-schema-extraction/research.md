# Research: Extração Automática de Schema de Bancos Externos

**Feature Branch**: `001-external-schema-extraction`  
**Date**: 2026-01-29  
**Status**: Complete

## Research Tasks

### 1. Inferência de Tipos em Documentos JSON/MongoDB

**Contexto**: Sistema precisa inferir tipos de dados a partir de amostras JSON sem schema pré-definido.

**Decision**: Implementar inferência de tipos usando análise estatística de valores com regras hierárquicas.

**Rationale**: 
- MongoDB não possui schema rígido; tipos devem ser inferidos dinamicamente
- Análise de múltiplas amostras (500 por padrão) permite detecção confiável de campos opcionais
- Hierarquia de tipos: null < boolean < number < string (promoção de tipo quando há conflito)

**Alternatives Considered**:
1. **Usar biblioteca jsonschema-inference**: Rejeitado - não suporta detecção de campos opcionais por frequência
2. **Schema estático via configuração**: Rejeitado - viola requisito de descoberta automática (FR-001)
3. **Análise de 100% dos documentos**: Rejeitado - impraticável em PROD com grandes volumes

**Implementation Approach**:
```python
# Regras de inferência de tipo
TYPE_PRIORITY = {
    "null": 0,
    "boolean": 1, 
    "integer": 2,
    "number": 3,
    "date": 4,
    "string": 5,
    "array": 6,
    "object": 7
}

# Campo obrigatório: presente em >95% das amostras
# Campo opcional: presente em ≤95% das amostras
REQUIRED_THRESHOLD = 0.95
```

---

### 2. Detecção de Colunas Enumeráveis

**Contexto**: Sistema deve identificar colunas com conjunto finito de valores (enums) para otimizar queries e UX.

**Decision**: Detecção puramente estatística baseada em cardinalidade, sem participação de LLM.

**Rationale**:
- Critério objetivo e determinístico (cardinalidade ≤ limite configurável)
- Evita custos desnecessários com chamadas LLM
- Limite padrão de 50 valores únicos cobre maioria dos casos práticos
- Configurável via `ENUMERABLE_CARDINALITY_LIMIT` em Settings/.env

**Alternatives Considered**:
1. **LLM para classificar colunas**: Rejeitado - conforme clarificação do usuário, LLM foca apenas em descrições semânticas
2. **Heurística por nome de coluna**: Rejeitado - não confiável (ex: "status" pode ter 2 ou 200 valores)
3. **Limite fixo hardcoded**: Rejeitado - diferentes domínios têm necessidades diferentes

**Implementation Approach**:
```python
def is_enumerable(unique_values: set, limit: int = 50) -> bool:
    """Coluna é enumerável se cardinalidade <= limite."""
    return len(unique_values) <= limit
```

---

### 3. Integração com OpenAI para Enriquecimento Semântico

**Contexto**: LLM deve gerar descrições em linguagem natural para cada coluna do schema.

**Decision**: Usar OpenAI GPT-4o-mini com prompts estruturados e fallback gracioso.

**Rationale**:
- GPT-4o-mini oferece bom balanço custo/qualidade para geração de descrições
- Batch processing reduz número de chamadas API
- Fallback com status "pending_enrichment" garante sistema funcional mesmo sem LLM

**Alternatives Considered**:
1. **HubAI**: Rejeitado - conforme clarificação, usar OpenAI
2. **Processamento síncrono por coluna**: Rejeitado - muito lento e custoso
3. **Falha total se LLM indisponível**: Rejeitado - viola FR-023 (sistema deve continuar sem descrição)

**Implementation Approach**:
```python
ENRICHMENT_PROMPT = """
Analise o schema da tabela "{table_name}" do banco "{db_name}" e gere descrições 
em português para cada coluna. Considere o contexto de dados financeiros/cartão.

Schema:
{schema_json}

Valores de exemplo (quando disponíveis):
{sample_values}

Responda em JSON com formato: {"column_name": "descrição semântica"}
"""

# Retry automático para colunas pending_enrichment
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 60
```

---

### 4. Padrão Repository para Múltiplos Ambientes

**Contexto**: Sistema deve operar em MOCK (JSON local) e PROD (MongoDB real) com mesma interface.

**Decision**: Abstract Repository Pattern com Factory para seleção de ambiente.

**Rationale**:
- Isola lógica de negócio da fonte de dados
- Permite testes unitários com mock repository
- Troca de ambiente via configuração sem alteração de código (FR-019)
- Alinhado com arquitetura existente do projeto

**Alternatives Considered**:
1. **Adapter Pattern**: Rejeitado - Repository é mais natural para acesso a dados
2. **Conexão direta com if/else**: Rejeitado - viola SRP e dificulta testes
3. **Microserviços separados por ambiente**: Rejeitado - complexidade desnecessária

**Implementation Approach**:
```python
from abc import ABC, abstractmethod

class ExternalDataRepository(ABC):
    @abstractmethod
    async def get_sample_documents(
        self, db_name: str, table_name: str, limit: int = 500
    ) -> list[dict]:
        """Retorna amostra de documentos para extração de schema."""
        pass

class MockDataRepository(ExternalDataRepository):
    """Implementação para arquivos JSON em res/db/"""
    pass

class MongoDataRepository(ExternalDataRepository):
    """Implementação para MongoDB externo"""
    pass

def get_repository(environment: str) -> ExternalDataRepository:
    """Factory para seleção de repositório baseado em ambiente."""
    if environment == "MOCK":
        return MockDataRepository()
    return MongoDataRepository()
```

---

### 5. Estruturas Aninhadas (Nested Objects)

**Contexto**: Documentos MongoDB frequentemente têm objetos aninhados (ex: `product_data`, `guaranteed_limit`).

**Decision**: Representação hierárquica com path notation (dot notation) no catálogo.

**Rationale**:
- Permite queries em campos aninhados (`product_data.type`)
- Mantém estrutura flat no banco relacional PostgreSQL
- Facilita exibição em interfaces (expandir/colapsar)

**Alternatives Considered**:
1. **Flatten completo**: Rejeitado - perde contexto hierárquico
2. **JSON column no PostgreSQL**: Rejeitado - dificulta queries e indexação
3. **Tabela separada para hierarquia**: Rejeitado - complexidade excessiva para o caso de uso

**Implementation Approach**:
```python
# Exemplo de representação no catálogo:
# Campo: guaranteed_limit.enabled
# Path: "guaranteed_limit.enabled"
# Parent: "guaranteed_limit"
# Depth: 2

def flatten_schema(obj: dict, prefix: str = "") -> list[ColumnMetadata]:
    """Converte objeto aninhado em lista flat com paths."""
    columns = []
    for key, value in obj.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            columns.extend(flatten_schema(value, path))
        else:
            columns.append(ColumnMetadata(
                name=key,
                path=path,
                parent_path=prefix or None,
                depth=path.count('.') + 1
            ))
    return columns
```

---

### 6. Versionamento de Schema

**Contexto**: Schemas podem mudar ao longo do tempo; sistema deve suportar re-extração.

**Decision**: Sobrescrita simples com timestamp de última atualização (sem histórico completo).

**Rationale**:
- Requisito FR-007 exige apenas timestamp de última atualização
- FR-008 permite re-extração sem perda de dados (idempotente)
- Histórico completo não está nos requisitos e adiciona complexidade
- Pode evoluir para versionamento completo se necessário no futuro

**Alternatives Considered**:
1. **Versionamento completo com histórico**: Rejeitado - não está nos requisitos, complexidade prematura
2. **Append-only com soft delete**: Rejeitado - complica queries e aumenta storage
3. **Schema comparison automático**: Considerado para futuro - detectar breaking changes

**Implementation Approach**:
```python
class ExternalSource(Base):
    __tablename__ = "external_sources"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    db_name: Mapped[str] = mapped_column(String(100))
    table_name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)
    
    # Unique constraint para identificação
    __table_args__ = (UniqueConstraint('db_name', 'table_name'),)
```

---

## Configuration Parameters

| Parâmetro | Variável de Ambiente | Default | Descrição |
|-----------|---------------------|---------|-----------|
| Ambiente | `DATA_ENVIRONMENT` | `MOCK` | `MOCK` ou `PROD` |
| Tamanho da amostra | `SCHEMA_SAMPLE_SIZE` | `500` | Documentos analisados para inferência |
| Limite enumerável | `ENUMERABLE_CARDINALITY_LIMIT` | `50` | Cardinalidade máxima para enumerável |
| Threshold obrigatório | `REQUIRED_FIELD_THRESHOLD` | `0.95` | % para considerar campo obrigatório |
| OpenAI Model | `OPENAI_MODEL` | `gpt-4o-mini` | Modelo para enriquecimento |
| Retry LLM | `LLM_MAX_RETRIES` | `3` | Tentativas para pending_enrichment |

---

## Dependencies to Add

```toml
# pyproject.toml - dependencies adicionais
[project]
dependencies = [
    # Existentes...
    "openai>=1.0.0",        # SDK OpenAI para enriquecimento
    "motor>=3.3.0",         # Driver async MongoDB (PROD)
]
```

---

## Risks & Mitigations

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| OpenAI rate limiting | Média | Médio | Batch processing + exponential backoff |
| Schema muito diferente entre amostras | Baixa | Alto | Análise de 500 docs + threshold 95% |
| MongoDB timeout em PROD | Média | Alto | Connection pooling + timeouts configuráveis |
| Campos com tipos mistos | Alta | Médio | Promoção de tipo + warning no log |

---

## Research Status: ✅ COMPLETE

Todos os NEEDS CLARIFICATION foram resolvidos através de:
1. Clarificações do usuário na spec (OpenAI vs HubAI, detecção estatística de enumeráveis)
2. Análise da estrutura existente do projeto (pyproject.toml, src/, tests/)
3. Análise dos arquivos JSON de exemplo em res/db/
