# Quickstart: Catálogo de Metadados em YAML

**Feature Branch**: `002-yaml-catalog`  
**Date**: 2026-02-03

## Visão Geral

Este documento descreve como usar o novo catálogo de metadados baseado em arquivos YAML.

---

## 1. Estrutura de Arquivos

Após a implementação, a estrutura do catálogo será:

```
catalog/
├── catalog.yaml              # Índice global de sources
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

---

## 2. Extraindo Metadados via CLI

### Extrair uma source específica

```bash
# Sintaxe
uv run qa-catalog extract <db_name> <table_name> [--sample-size N]

# Exemplo
uv run qa-catalog extract credit invoice --sample-size 500
```

### Extrair todas as sources conhecidas

```bash
uv run qa-catalog extract-all --sample-size 500
```

### Listar sources disponíveis

```bash
uv run qa-catalog list-known
```

### Validar arquivos YAML

```bash
# Validar todos os arquivos
uv run qa-catalog validate

# Validar um arquivo específico
uv run qa-catalog validate catalog/sources/credit/invoice.yaml
```

---

## 3. Consultando via API

### Listar todas as sources

```bash
curl http://localhost:8000/api/v1/catalog/sources
```

Resposta:
```json
{
  "items": [
    {
      "id": "credit.invoice",
      "db_name": "credit",
      "table_name": "invoice",
      "column_count": 45,
      "enumerable_count": 8,
      "cataloged_at": "2026-02-03T10:30:00Z",
      "updated_at": "2026-02-03T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

### Obter detalhes de uma source

```bash
curl http://localhost:8000/api/v1/catalog/sources/credit.invoice
```

### Listar colunas com filtros

```bash
# Apenas colunas enumeráveis
curl "http://localhost:8000/api/v1/catalog/sources/credit.invoice/columns?is_enumerable=true"

# Apenas colunas do tipo string
curl "http://localhost:8000/api/v1/catalog/sources/credit.invoice/columns?type=string"
```

---

## 4. Editando Metadados Manualmente

### Adicionando descrições a campos

Abra o arquivo YAML e adicione/edite o campo `description`:

```yaml
# catalog/sources/credit/invoice.yaml
columns:
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
    sample_values:
      - OPEN
      - PAID
    description: "Status atual da fatura. OPEN=aberta, PAID=paga, OVERDUE=vencida"
    enrichment_status: enriched  # Marcar como enriquecido
```

### Campos editáveis manualmente

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `description` | string | Descrição do campo |
| `enrichment_status` | enum | Status de enriquecimento (enriched, pending_enrichment) |

**Nota**: Outros campos são gerenciados automaticamente pela extração.

---

## 5. Configuração

### Variáveis de ambiente

```env
# Caminho para o diretório do catálogo (default: catalog)
CATALOG_PATH=catalog

# TTL do cache em segundos (default: 60)
CATALOG_CACHE_TTL_SECONDS=60
```

### Exemplo de .env

```env
# Existing settings
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/qausersearch
DATA_SOURCE_ENVIRONMENT=MOCK

# New settings for YAML catalog
CATALOG_PATH=catalog
CATALOG_CACHE_TTL_SECONDS=60
```

---

## 6. Workflow Típico

### Primeira extração

```bash
# 1. Extrair todas as sources conhecidas
uv run qa-catalog extract-all

# 2. Validar arquivos gerados
uv run qa-catalog validate

# 3. Verificar via API
curl http://localhost:8000/api/v1/catalog/sources
```

### Atualização de metadados

```bash
# 1. Re-extrair source específica
uv run qa-catalog extract credit invoice

# 2. Validar
uv run qa-catalog validate

# 3. Commitar alterações
git add catalog/
git commit -m "feat(catalog): update credit.invoice metadata"
```

### Enriquecimento manual

```bash
# 1. Editar arquivo YAML
vim catalog/sources/credit/invoice.yaml

# 2. Validar estrutura
uv run qa-catalog validate

# 3. Commitar
git add catalog/sources/credit/invoice.yaml
git commit -m "docs(catalog): add descriptions to credit.invoice fields"
```

---

## 7. Troubleshooting

### Cache não atualiza após edição

O cache tem TTL de 60 segundos por padrão. Aguarde ou reinicie a aplicação.

```bash
# Reiniciar para limpar cache
pkill -f uvicorn
uv run uvicorn src.main:app --reload
```

### Erro de validação JSON Schema

```bash
# Ver erros detalhados
uv run qa-catalog validate --verbose
```

### Source não aparece na API

Verifique se:
1. O arquivo existe em `catalog/sources/{db_name}/{table_name}.yaml`
2. O índice `catalog/catalog.yaml` inclui a source
3. O arquivo YAML é válido (`uv run qa-catalog validate`)

---

## 8. Migração do PostgreSQL

Se você já tem dados no PostgreSQL, exporte para YAML:

```bash
# 1. Com ambiente MOCK, extraia do PostgreSQL
# (implementação futura - por ora, re-extrair do MongoDB)

# 2. Re-extrair todas as sources
uv run qa-catalog extract-all

# 3. Validar e commitar
uv run qa-catalog validate
git add catalog/
git commit -m "feat(catalog): migrate catalog to YAML"
```

---

## Referências

- [Spec](./spec.md) - Especificação completa da feature
- [Data Model](./data-model.md) - Modelo de dados
- [OpenAPI](./contracts/openapi.yaml) - Especificação da API
- [JSON Schema](./contracts/source.schema.json) - Schema para validação
