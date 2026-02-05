# 📋 Plano Final de QA - /api/v1/query/interpret

## Configuração

| Atributo | Valor |
|----------|-------|
| **REST Endpoint** | POST http://localhost:8000/api/v1/query/interpret |
| **WebSocket Endpoint** | ws://localhost:8000/ws/query/interpret |
| Request | {"prompt": "..."} |
| Timeout | 60s |
| Performance Warning | > 10s |
| Performance Failure | > 30s |
| Confidence Threshold | 0.5 |

> **Nota de Dependência**: Os testes das categorias 1 (Interpretação NL) e 2.6 (Sinônimos e Variações) dependem do **enriquecimento semântico do catálogo** estar completo. Veja [02P-catalog-ai-enrichment.md](./02P-catalog-ai-enrichment.md) para detalhes. Execute os testes de enriquecimento antes de rodar a suíte completa de QA.

---

## Catálogo de Referência (Tabelas Válidas)

| db_name.table_name | Colunas Chave |
|--------------------|---------------|
| credit.invoice | status, value, dueDate, closeDate, consumerId, isFirstInvoice |
| credit.closed_invoice | status, receivedPayments, creditLimit |
| card_account_authorization.card_main | type, origin_type, variant, block_code, issuer, consumer_id, nfc |
| card_account_authorization.account_main | status, block_code, block_code_1, block_code_2, issuer, in_debit_repository |

---

## CATEGORIA 1: Interpretação de Linguagem Natural (30 cenários)

### 1.1 Cartões por Tipo de Bloqueio

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.1.1 | "cartoes bloqueados por roubo" | block_code = 'R' | card_main | >= 0.7 |
| 1.1.2 | "cartoes perdidos" | block_code = 'P' | card_main | >= 0.7 |
| 1.1.3 | "cartoes com fraude" | block_code IN ('F', 'N', 'O') | card_main | >= 0.7 |
| 1.1.4 | "cartoes bloqueados preventivamente" | block_code = 'O' | card_main | >= 0.7 |
| 1.1.5 | "cartoes em transporte" | block_code = 'T' | card_main | >= 0.7 |
| 1.1.6 | "cartoes cancelados pelo cliente" | block_code = 'U' | card_main | >= 0.7 |
| 1.1.7 | "cartoes com falecimento" | block_code = 'M' | card_main | >= 0.7 |
| 1.1.8 | "cartoes extraviados" | block_code = 'E' | card_main | >= 0.7 |

**Validação para TODOS os testes desta categoria:**

```python
def validate_interpretation_test(response, expected):
    assert response.status_code == 200
    data = response.json()
    
    # Estrutura básica
    assert data["status"] == "ready"
    assert data["confidence"] >= expected["min_confidence"]
    assert data["query"]["is_valid"] == True
    
    # Entidades
    table_names = [e["table_name"] for e in data["entities"]]
    assert expected["table"] in " ".join(table_names)
    
    # Filtros - verificar que contém o campo esperado
    filter_fields = [f["field"] for f in data["filters"]]
    assert expected["filter_field"] in filter_fields
    
    # Valor do filtro
    for f in data["filters"]:
        if f["field"] == expected["filter_field"]:
            if isinstance(expected["filter_value"], list):
                assert f["value"] in expected["filter_value"] or f["operator"] == "IN"
            else:
                assert f["value"] == expected["filter_value"]
```

### 1.2 Contas por Status FIS

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.2.1 | "contas ativas" | status = 'A' | account_main | >= 0.7 |
| 1.2.2 | "contas novas" | status = 'N' | account_main | >= 0.7 |
| 1.2.3 | "contas dormentes" | status = 'D' | account_main | >= 0.7 |
| 1.2.4 | "contas inativas" | status = 'I' | account_main | >= 0.7 |
| 1.2.5 | "contas encerradas" | status = '8' | account_main | >= 0.7 |
| 1.2.6 | "contas em charge-off" | status = 'Z' | account_main | >= 0.7 |

### 1.3 Contas por Tipo de Bloqueio

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.3.1 | "contas com atraso leve" | block_code = 'A' | account_main | >= 0.7 |
| 1.3.2 | "contas bloqueadas por SPC" | block_code = 'I' | account_main | >= 0.7 |
| 1.3.3 | "contas em CRELI" | block_code = 'J' | account_main | >= 0.7 |
| 1.3.4 | "contas com acordo" | block_code IN ('H', 'Y') | account_main | >= 0.6 |
| 1.3.5 | "contas sem credito" | block_code IN ('S', 'L') | account_main | >= 0.6 |
| 1.3.6 | "contas com limite zerado" | block_code = 'L' | account_main | >= 0.7 |

### 1.4 Cartões por Tipo e Variante

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.4.1 | "cartoes virtuais" | type = 'VIRTUAL' | card_main | >= 0.8 |
| 1.4.2 | "cartoes fisicos" | type = 'PHYSICAL' | card_main | >= 0.8 |
| 1.4.3 | "cartoes platinum" | variant = 'PLATINUM' | card_main | >= 0.8 |
| 1.4.4 | "cartoes black" | variant = 'BLACK' | card_main | >= 0.8 |
| 1.4.5 | "cartoes de credito" | origin_type = 'CREDIT' | card_main | >= 0.8 |
| 1.4.6 | "cartoes de debito" | origin_type = 'DEBIT' | card_main | >= 0.8 |

### 1.5 Faturas por Status

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.5.1 | "faturas vencidas" | status = 'DELAYED' | invoice | >= 0.8 |
| 1.5.2 | "faturas abertas" | status = 'OPEN' | invoice | >= 0.8 |
| 1.5.3 | "faturas fechadas" | status = 'CLOSED' | invoice | >= 0.8 |
| 1.5.4 | "faturas com pagamento antecipado" | status = 'ADVANCE_PAYMENT' | invoice | >= 0.7 |

### 1.6 Combinações Complexas

| ID | Prompt | Filtros Esperados | Tabela | Confidence |
|----|--------|-------------------|--------|------------|
| 1.6.1 | "cartoes virtuais platinum ativos" | type='VIRTUAL' + variant='PLATINUM' + block_code='' | card_main | >= 0.7 |
| 1.6.2 | "contas ativas do PicPay" | status='A' + issuer='PICPAY' | account_main | >= 0.7 |
| 1.6.3 | "cartoes fisicos bloqueados por fraude" | type='PHYSICAL' + block_code IN ('F','N') | card_main | >= 0.7 |
| 1.6.4 | "contas em CRELI com charge-off" | status='Z' + block_code='J' | account_main | >= 0.8 |

---

## CATEGORIA 2: Testes de Ambiguidade (19 cenários)

### 2.1 Prompts Sem Entidade Identificável (ERRO ESPERADO)

| ID | Prompt | Erro Esperado | Código HTTP |
|----|--------|---------------|-------------|
| 2.1.1 | "dados" | AMBIGUOUS_PROMPT | 400 |
| 2.1.2 | "tudo" | AMBIGUOUS_PROMPT | 400 |
| 2.1.3 | "me mostra" | AMBIGUOUS_PROMPT | 400 |
| 2.1.4 | "buscar" | AMBIGUOUS_PROMPT | 400 |

**Validação:**

```python
def validate_ambiguous_no_entity(response):
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "AMBIGUOUS_PROMPT"
    assert len(data["suggestions"]) > 0
```

### 2.2 Prompts Com Entidade Mas Sem Filtro (ERRO ESPERADO)

| ID | Prompt | Erro Esperado | Código HTTP |
|----|--------|---------------|-------------|
| 2.2.1 | "usuarios" | AMBIGUOUS_PROMPT ou UNRECOGNIZED_TABLES | 400 |
| 2.2.2 | "cartoes" | AMBIGUOUS_PROMPT | 400 |
| 2.2.3 | "faturas" | AMBIGUOUS_PROMPT | 400 |
| 2.2.4 | "contas" | AMBIGUOUS_PROMPT | 400 |

**Nota:** "usuarios" pode retornar UNRECOGNIZED_TABLES pois não existe tabela "usuarios" no catálogo.

### 2.3 Prompts Com Filtro Mas Sem Entidade (ERRO ESPERADO)

| ID | Prompt | Erro Esperado | Código HTTP |
|----|--------|---------------|-------------|
| 2.3.1 | "ativos" | AMBIGUOUS_PROMPT | 400 |
| 2.3.2 | "bloqueados" | AMBIGUOUS_PROMPT | 400 |
| 2.3.3 | "vencidos" | AMBIGUOUS_PROMPT | 400 |

### 2.4 Contradições Lógicas (ERRO ESPERADO)

| ID | Prompt | Contradição | Erro Esperado |
|----|--------|-------------|---------------|
| 2.4.1 | "cartoes ativos bloqueados" | ativo = block_code='', bloqueado = block_code!='' | AMBIGUOUS_PROMPT com indicação de contradição |
| 2.4.2 | "contas ativas encerradas" | ativo = status='A', encerrado = status='8' | AMBIGUOUS_PROMPT |
| 2.4.3 | "faturas abertas fechadas" | status='OPEN' vs status='CLOSED' | AMBIGUOUS_PROMPT |

**Validação:**

```python
def validate_contradiction(response):
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "AMBIGUOUS_PROMPT"
    # A mensagem deve indicar a contradição
    assert "contradição" in data["message"].lower() or "conflito" in data["message"].lower()
```

### 2.5 Tabelas/Colunas Inexistentes

| ID | Prompt | Problema | Erro Esperado |
|----|--------|----------|---------------|
| 2.5.1 | "usuarios do sistema de pagamento" | Tabela inexistente | UNRECOGNIZED_TABLES |
| 2.5.2 | "cartoes com campo xyz" | Coluna "xyz" inexistente | UNRECOGNIZED_COLUMNS |
| 2.5.3 | "faturas com CPF" | Coluna CPF não existe em invoice | UNRECOGNIZED_COLUMNS |

### 2.6 Sinônimos e Variações (SUCESSO ESPERADO)

| ID | Prompt A | Prompt B | Devem Gerar Mesmo Filtro |
|----|----------|----------|--------------------------|
| 2.6.1 | "cartao roubado" | "cartao com roubo" | block_code = 'R' |
| 2.6.2 | "negativado" | "SPC" | block_code = 'I' |
| 2.6.3 | "inadimplente grave" | "CRELI" | block_code = 'J' |
| 2.6.4 | "conta fechada" | "conta encerrada" | status = '8' |

**Validação:**

```python
def validate_synonyms(response_a, response_b):
    data_a = response_a.json()
    data_b = response_b.json()
    
    # Ambos devem ser sucesso
    assert data_a["status"] == "ready"
    assert data_b["status"] == "ready"
    
    # Filtros devem ser equivalentes
    filters_a = {f["field"]: f["value"] for f in data_a["filters"]}
    filters_b = {f["field"]: f["value"] for f in data_b["filters"]}
    assert filters_a == filters_b
```

---

## CATEGORIA 3: Validação de Resposta/Schema (14 cenários)

### 3.1 Estrutura da Resposta (9 cenários)

Para QUALQUER resposta de sucesso (200), validar:

| ID | Campo | Critério de Validação |
|----|-------|----------------------|
| 3.1.1 | id | UUID v4 válido (regex: ^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$) |
| 3.1.2 | status | Um de: pending, interpreting, validating, refining, ready, blocked, error |
| 3.1.3 | summary | String não vazia, mínimo 10 caracteres |
| 3.1.4 | confidence | Float no range 0.0 <= x <= 1.0 |
| 3.1.5 | entities | Array (pode ser vazio) |
| 3.1.6 | filters | Array (pode ser vazio) |
| 3.1.7 | query | Objeto presente |
| 3.1.8 | query.id | UUID v4 válido |
| 3.1.9 | query.sql | String contendo "SELECT" |

### 3.2 Validação de Entidades Contra Catálogo (2 cenários)

| ID | Validação | Como Testar |
|----|-----------|-------------|
| 3.2.1 | entities[].table_name existe no catálogo | Para cada entity, verificar se table_name está em lista de tabelas válidas |
| 3.2.2 | Entidades inventadas são rejeitadas | Verificar que NUNCA aparece tabela que não está no catálogo |

**Lista de tabelas válidas:**

```python
VALID_TABLES = [
    "credit.invoice",
    "credit.closed_invoice", 
    "card_account_authorization.card_main",
    "card_account_authorization.account_main"
]
```

### 3.3 Validação de Filtros Contra Catálogo (3 cenários - CRÍTICO)

| ID | Validação | Como Testar |
|----|-----------|-------------|
| 3.3.1 | filters[].field existe nas tabelas referenciadas | Checar contra YAML do catálogo |
| 3.3.2 | Colunas inventadas são rejeitadas | Ex: se aparecer "card_status" em vez de "block_code", FALHAR |
| 3.3.3 | filters[].operator é válido | Um de: =, !=, >, >=, <, <=, LIKE, IN, BETWEEN, IS NULL, IS NOT NULL |

**Mapeamento de colunas por tabela:**

```python
VALID_COLUMNS = {
    "card_account_authorization.card_main": [
        "type", "origin_type", "variant", "block_code", "issuer", 
        "consumer_id", "nfc", "expiry_date", "blocked_at", "bin"
    ],
    "card_account_authorization.account_main": [
        "status", "block_code", "block_code_1", "block_code_2", 
        "issuer", "in_debit_repository", "consumer_id", "document_number"
    ],
    "credit.invoice": [
        "status", "value", "dueDate", "closeDate", "consumerId", 
        "isFirstInvoice", "debits", "minValue"
    ],
    "credit.closed_invoice": [
        "status", "receivedPayments", "creditLimit", "taxes"
    ]
}
```

---

## CATEGORIA 4: Performance (3 cenários REST)

| ID | Prompt | Complexidade | Warning | Failure |
|----|--------|--------------|---------|---------|
| 4.1 | "faturas vencidas" | Simples | > 10s | > 30s |
| 4.2 | "cartoes virtuais platinum ativos do picpay" | Média | > 15s | > 45s |
| 4.3 | "contas bloqueadas em creli com charge-off" | Alta | > 20s | > 60s |

---

## CATEGORIA 5: WebSocket (12 cenários)

> **Contexto**: O CLI Chat (`qa chat`) consome a API via WebSocket para feedback em tempo real.
> Estes testes garantem a qualidade do canal de streaming usado pelo cliente principal.

### 5.1 Conexão e Handshake (3 cenários)

| ID | Cenário | Critério de Sucesso | Timeout |
|----|---------|---------------------|---------|
| 5.1.1 | Conexão bem-sucedida | WebSocket aceito, status 101 | 5s |
| 5.1.2 | Conexão com URL inválida | Erro 404 ou rejeição de upgrade | 5s |
| 5.1.3 | Reconexão após disconnect | Segunda conexão bem-sucedida | 10s |

**Validação:**

```python
async def validate_ws_connection(url: str) -> None:
    async with websockets.connect(url) as ws:
        assert ws.open
        # Enviar ping para confirmar conexão ativa
        pong = await ws.ping()
        await asyncio.wait_for(pong, timeout=5)
```

### 5.2 Streaming de Mensagens (5 cenários)

| ID | Cenário | Mensagens Esperadas | Ordem |
|----|---------|---------------------|-------|
| 5.2.1 | Prompt simples | status → chunks → interpretation → query | Sequencial |
| 5.2.2 | Prompt ambíguo | status → error (AMBIGUOUS_PROMPT) | Sequencial |
| 5.2.3 | Múltiplas fases | status (interpreting) → status (validating) → status (ready) | Sequencial |
| 5.2.4 | Chunks de progresso | Pelo menos 2 chunks entre status inicial e final | Parcial |
| 5.2.5 | Mensagem final completa | Última mensagem contém interpretation + query | - |

**Validação:**

```python
async def validate_ws_streaming(ws, prompt: str, expected_phases: list[str]) -> None:
    await ws.send(json.dumps({"prompt": prompt}))
    
    received_phases = []
    async for message in ws:
        data = json.loads(message)
        if "status" in data:
            received_phases.append(data["status"])
        if data.get("status") == "ready" or data.get("status") == "error":
            break
    
    # Verificar que todas as fases esperadas foram recebidas em ordem
    for expected in expected_phases:
        assert expected in received_phases, f"Fase '{expected}' não recebida"
```

### 5.3 Tratamento de Erros WebSocket (4 cenários)

| ID | Cenário | Comportamento Esperado | Código |
|----|---------|------------------------|--------|
| 5.3.1 | Timeout de inatividade (60s) | Conexão fechada pelo servidor | 1000 |
| 5.3.2 | Prompt inválido (JSON malformado) | Mensagem de erro + conexão mantida | - |
| 5.3.3 | Desconexão durante processamento | Cleanup gracioso no servidor | - |
| 5.3.4 | Rate limiting (se aplicável) | Erro 429 ou mensagem de throttle | - |

**Validação:**

```python
async def validate_ws_error_handling(ws) -> None:
    # Enviar JSON inválido
    await ws.send("not-a-json")
    
    response = await ws.recv()
    data = json.loads(response)
    
    assert data.get("type") == "error"
    assert "JSON" in data.get("message", "").upper() or "parse" in data.get("message", "").lower()
    
    # Conexão deve permanecer aberta
    assert ws.open
```

### 5.4 Validação de Schema WebSocket

| ID | Campo | Critério |
|----|-------|----------|
| 5.4.1 | type | Um de: status, chunk, interpretation, query, error |
| 5.4.2 | timestamp | ISO 8601 válido em todas as mensagens |
| 5.4.3 | session_id | UUID consistente durante toda a sessão |

---

## 📊 Resumo Final

| Categoria | Cenários |
|-----------|----------|
| 1. Interpretação NL | 30 |
| 2. Ambiguidade | 19 |
| 3. Validação Schema | 14 |
| 4. Performance REST | 3 |
| 5. WebSocket | 12 |
| **TOTAL** | **78** |

---

## 🛠️ Estrutura do Script de Automação

```
tests/qa/
├── __init__.py
├── config.py              # Configurações (BASE_URL, thresholds, tabelas válidas)
├── test_cases.py          # Definição de todos os 78 casos de teste
├── validators.py          # Funções de validação (schema, catálogo, filtros)
├── executor.py            # Executor async com httpx (REST)
├── ws_executor.py         # Executor async com websockets (WebSocket)
├── reporter.py            # Geração de relatórios MD + JSON
└── run_qa.py              # Entry point CLI
```

**Comando de execução:**

```bash
# Todos os testes (REST + WebSocket)
uv run python -m tests.qa.run_qa --base-url http://localhost:8000 --output-dir ./reports

# Apenas testes REST
uv run python -m tests.qa.run_qa --base-url http://localhost:8000 --protocol rest

# Apenas testes WebSocket
uv run python -m tests.qa.run_qa --base-url ws://localhost:8000 --protocol websocket
```

---

## 📝 Notas de Implementação

### Priorização

1. **P0 (Crítico)**: Categorias 3.3 (Validação de Filtros), 1 (Interpretação NL básica), 5.1-5.2 (WebSocket conexão/streaming)
2. **P1 (Alto)**: Categorias 2 (Ambiguidade), 3.1/3.2 (Schema), 5.3-5.4 (WebSocket erros/schema)
3. **P2 (Médio)**: Categoria 4 (Performance REST)

### Dependências

- Python 3.11+
- httpx (async HTTP client para REST)
- websockets (async WebSocket client)
- pytest (test runner)
- pyyaml (para validação contra catálogo YAML)
- jsonschema (para validação de schema)

### Execução Recomendada

```bash
# Rodar apenas testes de interpretação básica
uv run pytest tests/qa/ -k "test_interpretation"

# Rodar testes de ambiguidade
uv run pytest tests/qa/ -k "test_ambiguity"

# Rodar testes WebSocket
uv run pytest tests/qa/ -k "test_websocket"

# Rodar todos os testes com relatório
uv run python -m tests.qa.run_qa --base-url http://localhost:8000 --output-dir ./reports --verbose

# Rodar apenas testes críticos (P0)
uv run pytest tests/qa/ -m critical
```

### Critérios de Sucesso

- ✅ 100% dos testes de interpretação NL (categoria 1) devem passar
- ✅ 100% dos testes de ambiguidade (categoria 2) devem retornar erro esperado
- ✅ 100% dos testes de validação de schema (categoria 3) devem passar
- ✅ 100% dos testes de WebSocket (categoria 5) devem passar
- ⚠️ 90% dos testes de performance (categoria 4) devem estar dentro dos limites de warning
- ❌ 0% dos testes de performance podem exceder os limites de failure

> **Nota**: Os testes das categorias 1 e 2.6 requerem que o enriquecimento semântico do catálogo
> esteja completo. Veja [02P-catalog-ai-enrichment.md](./02P-catalog-ai-enrichment.md).

---

**Versão**: 1.0.0  
**Última Atualização**: 2026-02-04  
**Responsável**: Equipe QA
