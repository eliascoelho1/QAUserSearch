# Quickstart: Extração Automática de Schema

**Feature Branch**: `001-external-schema-extraction`  
**Date**: 2026-01-30

## Pré-requisitos

- Python 3.11+
- PostgreSQL 14+ (local ou Docker)
- uv (gerenciador de pacotes)

## Setup Rápido

### 1. Configuração do Ambiente

```bash
# Clone e entre no diretório
cd QAUserSearch

# Instale dependências
uv sync

# Configure variáveis de ambiente
cp .env.example .env
```

### 2. Configure o `.env`

```bash
# Adicione ao .env:

# Ambiente de fonte de dados (MOCK ou PROD)
DATA_SOURCE_ENVIRONMENT=MOCK

# Configurações de extração
SCHEMA_SAMPLE_SIZE=500
ENUMERABLE_CARDINALITY_LIMIT=50

# MongoDB (apenas para PROD)
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
```

### 3. Execute as Migrations

```bash
# Certifique-se que o PostgreSQL está rodando
docker compose up -d postgres

# Execute migrations
uv run alembic upgrade head
```

### 4. Inicie a Aplicação

```bash
uv run uvicorn src.main:app --reload
```

---

## Usando a API

### Extrair Schema de Uma Fonte

```bash
# Inicia extração assíncrona
curl -X POST http://localhost:8000/api/v1/catalog/extraction \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "card_account_authorization",
    "table_name": "account_main"
  }'

# Resposta:
# {
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "pending",
#   "message": "Extração iniciada com sucesso"
# }
```

### Consultar Status da Extração

```bash
curl http://localhost:8000/api/v1/catalog/extraction/550e8400-e29b-41d4-a716-446655440000

# Resposta (em progresso):
# {
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "running",
#   "progress": { "current": 250, "total": 500 }
# }

# Resposta (concluído):
# {
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "completed",
#   "result": {
#     "source_id": 1,
#     "columns_extracted": 45,
#     "enumerable_columns": 8
#   }
# }
```

### Extrair Todas as Fontes Conhecidas

```bash
curl -X POST http://localhost:8000/api/v1/catalog/extraction/all

# Inicia extração das 4 tabelas configuradas
```

### Listar Fontes Catalogadas

```bash
curl http://localhost:8000/api/v1/catalog/sources

# Resposta:
# {
#   "items": [
#     {
#       "id": 1,
#       "db_name": "card_account_authorization",
#       "table_name": "account_main",
#       "column_count": 45,
#       "enumerable_count": 8
#     }
#   ],
#   "total": 1
# }
```

### Consultar Detalhes de Uma Fonte

```bash
curl http://localhost:8000/api/v1/catalog/sources/1

# Retorna detalhes completos incluindo todas as colunas
```

### Listar Colunas com Filtros

```bash
# Apenas colunas obrigatórias
curl "http://localhost:8000/api/v1/catalog/sources/1/columns?is_required=true"

# Apenas colunas enumeráveis
curl "http://localhost:8000/api/v1/catalog/sources/1/columns?is_enumerable=true"

# Filtrar por tipo
curl "http://localhost:8000/api/v1/catalog/sources/1/columns?type=string"
```

---

## Ambientes

### MOCK (Desenvolvimento)

O ambiente MOCK usa arquivos JSON em `res/db/`:

```
res/db/
├── card_account_authorization.account_main.json
├── card_account_authorization.card_main.json
├── credit.invoice.json
└── credit.closed_invoice.json
```

Configure no `.env`:
```bash
DATA_SOURCE_ENVIRONMENT=MOCK
```

### PROD (Produção)

O ambiente PROD conecta diretamente aos bancos MongoDB externos.

Configure no `.env`:
```bash
DATA_SOURCE_ENVIRONMENT=PROD
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
```

---

## Estrutura de Arquivos JSON (MOCK)

Os arquivos seguem a nomenclatura `{db_name}.{table_name}.json`:

```json
[
  {
    "_id": "68e527ed7fc3841868bef0aa",
    "consumer_id": "26160269",
    "status": "A",
    "product_data": {
      "type": "HYBRID_LEVERAGED",
      "origin_flow": "manual-processing"
    },
    "created_at": "2025-10-07T11:47:09.803Z"
  }
]
```

---

## Testes

```bash
# Executar todos os testes
uv run pytest

# Apenas testes unitários
uv run pytest tests/unit/

# Apenas testes de integração
uv run pytest tests/integration/

# Com cobertura
uv run pytest --cov=src --cov-report=term-missing
```

---

## Troubleshooting

### Erro: "Arquivo JSON não encontrado"

Verifique se os arquivos existem em `res/db/` e seguem a nomenclatura correta.

### Erro: "Conexão com PostgreSQL falhou"

```bash
# Verifique se o container está rodando
docker compose ps

# Verifique a DATABASE_URL no .env
echo $DATABASE_URL
```

### Erro: "Conexão com MongoDB falhou" (PROD)

```bash
# Verifique a MONGODB_URI
# Certifique-se que o IP está na whitelist do cluster

# Teste conexão manual
uv run python -c "from motor.motor_asyncio import AsyncIOMotorClient; c = AsyncIOMotorClient('sua_uri'); print(c.server_info())"
```

---

## Próximos Passos

1. **Extrair schemas**: Execute extração das 4 tabelas iniciais
2. **Consultar catálogo**: Use a API para explorar os metadados
3. **Integrar com busca**: Use o catálogo para gerar queries dinâmicas (feature futura)
4. **Enriquecer com LLM**: Adicionar descrições semânticas (v2)
