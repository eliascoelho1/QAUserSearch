# Quickstart: Extração Automática de Schema

**Feature Branch**: `001-external-schema-extraction`

## Pré-requisitos

- Python 3.11+
- PostgreSQL (catálogo local)
- Docker (opcional, para ambiente completo)
- Credenciais OpenAI (para enriquecimento)

## Setup Rápido

### 1. Configuração do Ambiente

```bash
# Clonar e entrar no projeto
cd QAUserSearch

# Criar e ativar ambiente virtual
uv venv
source .venv/bin/activate

# Instalar dependências (incluindo novas do plano)
uv pip install -e ".[dev]"
```

### 2. Configurar Variáveis de Ambiente

Copiar e editar `.env`:

```bash
cp .env.example .env
```

Variáveis relevantes para esta feature:

```env
# Ambiente de dados (MOCK = JSON local, PROD = MongoDB real)
DATA_ENVIRONMENT=MOCK

# PostgreSQL local (catálogo)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/qausersearch

# Extração de schema
SCHEMA_SAMPLE_SIZE=500
REQUIRED_FIELD_THRESHOLD=0.95
ENUMERABLE_CARDINALITY_LIMIT=50

# OpenAI (enriquecimento)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LLM_MAX_RETRIES=3

# MongoDB (apenas para PROD)
MONGO_URI=mongodb://host:27017
MONGO_CONNECTION_TIMEOUT=30
```

### 3. Inicializar Banco de Dados

```bash
# Rodar migrations
alembic upgrade head

# Verificar tabelas criadas
psql $DATABASE_URL -c "\dt"
# Deve mostrar: external_sources, column_metadata
```

### 4. Executar Extração (Ambiente MOCK)

```bash
# Iniciar servidor
uvicorn src.main:app --reload

# Em outro terminal, iniciar extração
curl -X POST http://localhost:8000/api/v1/extraction \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "card_account_authorization",
    "table_name": "account_main"
  }'

# Resposta esperada:
# {
#   "source_id": "550e8400-...",
#   "status": "in_progress",
#   "message": "Extração iniciada com sucesso"
# }
```

### 5. Verificar Status

```bash
# Consultar status da extração
curl http://localhost:8000/api/v1/extraction/{source_id}/status

# Listar colunas extraídas
curl http://localhost:8000/api/v1/sources/{source_id}/columns
```

### 6. Executar Enriquecimento (requer OpenAI)

```bash
# Enriquecer colunas de uma fonte
curl -X POST http://localhost:8000/api/v1/enrichment \
  -H "Content-Type: application/json" \
  -d '{"source_id": "550e8400-..."}'

# Retry de colunas com falha
curl -X POST http://localhost:8000/api/v1/enrichment/retry
```

## Arquivos Mock Disponíveis

Os seguintes arquivos em `res/db/` podem ser usados para testes:

| Arquivo | Banco | Tabela |
|---------|-------|--------|
| `card_account_authorization.account_main.json` | card_account_authorization | account_main |
| `card_account_authorization.card_main.json` | card_account_authorization | card_main |
| `credit.invoice.json` | credit | invoice |
| `credit.closed_invoice.json` | credit | closed_invoice |

## Executar Testes

```bash
# Testes unitários
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Testes de contrato
pytest tests/contract/ -v

# Todos os testes com cobertura
pytest --cov=src --cov-report=html
```

## Troubleshooting

### Erro: "Fonte não encontrada"
- Verifique se o arquivo JSON existe em `res/db/`
- Confirme o padrão de nomenclatura: `{db_name}.{table_name}.json`

### Erro: "OpenAI rate limit"
- Reduza `SCHEMA_SAMPLE_SIZE` ou aumente intervalo entre requests
- Colunas ficarão com status `pending_enrichment` para retry posterior

### Erro: "Connection refused" (PROD)
- Verifique `MONGO_URI` em `.env`
- Confirme conectividade de rede com MongoDB externo
- Verifique se `DATA_ENVIRONMENT=PROD` está configurado

## Próximos Passos

1. Extrair schemas das 4 tabelas identificadas
2. Revisar descrições geradas pela LLM
3. Integrar catálogo com módulo de geração de queries
