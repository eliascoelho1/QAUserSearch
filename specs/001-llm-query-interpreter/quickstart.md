# Quickstart: Interpretador LLM para Geração de Queries

**Feature Branch**: `001-llm-query-interpreter`

## Pré-requisitos

- Python 3.11+
- PostgreSQL (banco de QA)
- Chave de API OpenAI (GPT-4)

## Setup

### 1. Instalar dependências

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências (incluindo novas)
uv sync
```

### 2. Configurar variáveis de ambiente

```bash
# Copiar exemplo se ainda não existir
cp .env.example .env

# Adicionar/editar as seguintes variáveis:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT=15
OPENAI_MAX_RETRIES=3
```

### 3. Executar migrations (se houver novas tabelas)

```bash
alembic upgrade head
```

### 4. Iniciar servidor

```bash
uvicorn src.main:app --reload
```

## Uso via REST API

### Interpretar um prompt

```bash
curl -X POST http://localhost:8000/api/v1/query/interpret \
  -H "Content-Type: application/json" \
  -d '{"prompt": "usuários com cartão de crédito ativo"}'
```

**Resposta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ready",
  "summary": "Buscarei usuários onde: cartão de crédito = ativo",
  "entities": [
    {"name": "usuário", "table_name": "users"},
    {"name": "cartão de crédito", "table_name": "credit_cards"}
  ],
  "filters": [
    {"field": "status", "operator": "=", "value": "active"}
  ],
  "confidence": 0.95,
  "query": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "sql": "SELECT u.* FROM users u JOIN credit_cards cc ON u.id = cc.user_id WHERE cc.status = 'active' LIMIT 100",
    "is_valid": true,
    "validation_errors": []
  }
}
```

### Executar a query

```bash
curl -X POST http://localhost:8000/api/v1/query/550e8400-e29b-41d4-a716-446655440001/execute \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

## Uso via WebSocket (Streaming)

### Conectar e interpretar com streaming

```python
import asyncio
import websockets
import json

async def interpret_with_streaming():
    uri = "ws://localhost:8000/ws/query/interpret"
    
    async with websockets.connect(uri) as ws:
        # Enviar prompt
        await ws.send(json.dumps({
            "type": "interpret",
            "prompt": "usuários com fatura vencida há mais de 30 dias"
        }))
        
        # Receber mensagens de streaming
        async for message in ws:
            data = json.loads(message)
            
            if data["type"] == "status":
                print(f"Status: {data['data']['status']} - {data['data']['message']}")
            
            elif data["type"] == "chunk":
                print(data["data"]["content"], end="", flush=True)
            
            elif data["type"] == "interpretation":
                print(f"\n\nInterpretação: {data['data']['summary']}")
            
            elif data["type"] == "query":
                print(f"Query gerada: {data['data']['sql']}")
                break
            
            elif data["type"] == "error":
                print(f"Erro: {data['data']['message']}")
                break

asyncio.run(interpret_with_streaming())
```

### Exemplo de output de streaming

```
Status: interpreting - Analisando prompt...
Identificando entidades... usuário, fatura...
Extraindo filtros... vencimento, período...
Mapeando para tabelas... users, invoices...

Interpretação: Buscarei usuários onde: fatura = vencida E dias de atraso > 30

Query gerada: SELECT u.* FROM users u JOIN invoices i ON u.id = i.user_id WHERE i.status = 'overdue' AND i.due_date < NOW() - INTERVAL '30 days' LIMIT 100
```

## Tratamento de Erros

### Query bloqueada (comando proibido)

```json
{
  "type": "error",
  "data": {
    "code": "SQL_COMMAND_BLOCKED",
    "message": "Comando DELETE não é permitido. Apenas consultas SELECT são aceitas.",
    "details": {
      "blocked_command": "DELETE"
    },
    "suggestions": [
      "Reformule seu pedido para buscar dados em vez de modificá-los",
      "Use termos como 'buscar', 'encontrar', 'listar'"
    ]
  }
}
```

### Timeout do LLM

```json
{
  "type": "error",
  "data": {
    "code": "LLM_TIMEOUT",
    "message": "O serviço de interpretação demorou mais que o esperado. Tente novamente.",
    "suggestions": [
      "Simplifique seu prompt",
      "Divida em buscas menores"
    ]
  }
}
```

## Testes

### Executar testes unitários

```bash
pytest tests/unit -v
```

### Executar testes de integração

```bash
pytest tests/integration -v
```

### Executar todos os testes com cobertura

```bash
pytest --cov=src --cov-report=term-missing
```

## Estrutura de Diretórios Relevantes

```
src/
├── agents/                 # CrewAI agents
│   ├── config/
│   │   ├── agents.yaml     # Definições dos agentes
│   │   └── tasks.yaml      # Definições das tasks
│   └── interpreter_crew.py # Crew principal
├── api/v1/
│   ├── endpoints/
│   │   └── query_interpreter.py  # REST endpoints
│   └── websocket/
│       ├── connection_manager.py # Gerenciador WS
│       └── handlers.py           # Handlers WS
└── services/
    ├── llm/
    │   └── openai_client.py      # Cliente OpenAI
    └── query/
        ├── interpreter_service.py # Serviço principal
        └── validator_service.py   # Validação SQL
```

## Próximos Passos

1. Executar `/speckit.tasks` para gerar as tasks de implementação
2. Implementar seguindo o ciclo TDD (Red-Green-Refactor)
3. Validar cobertura ≥80% antes de submeter PR
