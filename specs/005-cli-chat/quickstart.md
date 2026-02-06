# Quickstart: CLI Chat Interativo

**Feature**: 005-cli-chat  
**Date**: 2026-02-05

---

## Pré-requisitos

- Python 3.11+
- uv (package manager)
- Terminal com 60+ colunas

## Setup

```bash
# Instalar dependências (se ainda não instaladas)
uv sync --all-extras

# Verificar que websockets está instalado
uv run python -c "import websockets; print(websockets.__version__)"
```

---

## Desenvolvimento

### Executar em Modo Mock (Sem Backend)

```bash
# Modo mock - funciona 100% offline
uv run qa chat --mock

# Ou usando o módulo diretamente (antes de criar entry point)
uv run python -m src.cli.chat --mock
```

### Executar com Backend Real

```bash
# 1. Iniciar o backend (em outro terminal)
docker compose -f docker/docker-compose.yml up -d db
uv run uvicorn src.main:app --reload

# 2. Executar o chat
uv run qa chat

# Ou especificar servidor diferente
uv run qa chat --server ws://outro-host:8000/ws/query/interpret
```

---

## Comandos do Chat

| Comando | Descrição |
|---------|-----------|
| `/help` | Exibe ajuda com comandos disponíveis |
| `/exit` ou `/quit` | Encerra a sessão |
| `/clear` | Limpa a tela |
| `/history` | Lista as 10 últimas queries |
| `/execute` | Simula execução da última query |
| `/mock` | Alterna modo mock on/off |

---

## Testes

### Executar Todos os Testes do Chat

```bash
uv run pytest tests/unit/cli/chat/ -v
```

### Executar Teste Específico

```bash
# Testes de sessão
uv run pytest tests/unit/cli/chat/test_session.py -v

# Testes de comandos
uv run pytest tests/unit/cli/chat/test_commands.py -v

# Testes do cliente mock
uv run pytest tests/unit/cli/chat/test_mock_client.py -v
```

### Cobertura

```bash
uv run pytest tests/unit/cli/chat/ --cov=src/cli/chat --cov-report=term-missing
```

---

## Estrutura de Arquivos

```
src/cli/
├── main.py           # Entry point: `qa`
├── chat.py           # Subcomando: `qa chat`
└── chat/
    ├── __init__.py
    ├── client.py     # WSChatClient
    ├── mock_client.py# MockChatClient
    ├── session.py    # ChatSession
    ├── commands.py   # Comandos especiais
    ├── renderer.py   # Renderização de painéis
    └── handlers/
        ├── message_handler.py
        └── suggestion_handler.py

tests/unit/cli/chat/
├── conftest.py       # Fixtures compartilhadas
├── test_session.py
├── test_commands.py
├── test_client.py
├── test_mock_client.py
├── test_handlers.py
└── test_renderer.py
```

---

## Cenários de Teste Manual

### 1. Fluxo Básico (Mock)

```bash
uv run qa chat --mock
```

1. Digitar: `usuários com cartão de crédito ativo`
2. Verificar: PhaseSpinner aparece com fases
3. Verificar: Painel de interpretação com resumo e confiança
4. Verificar: Painel de SQL com syntax highlighting
5. Digitar: `/exit`
6. Verificar: Sessão encerra graciosamente

### 2. Comandos Especiais

```bash
uv run qa chat --mock
```

1. `/help` → Painel com lista de comandos
2. `/clear` → Tela limpa, welcome reexibida
3. `usuários ativos` → Gera resultado
4. `/history` → Lista com 1 query
5. `/execute` → Mensagem "Query seria executada..."
6. `/mock` → Toggle modo mock (já está on)
7. `/exit` → Encerra

### 3. Cenário de Erro (Mock)

```bash
uv run qa chat --mock
```

1. Digitar: `query com erro simulado`
2. Verificar: Painel de erro com sugestões

### 4. Cenário de Ambiguidade (Mock)

```bash
uv run qa chat --mock
```

1. Digitar: `usuários com ambiguidade`
2. Verificar: Painel de ambiguidade aparece
3. Verificar: Opções selecionáveis via setas

### 5. Ctrl+C Handling

```bash
uv run qa chat --mock
```

1. Pressionar Ctrl+C no prompt → Mensagem "Encerrando..."
2. Reiniciar e enviar query
3. Pressionar Ctrl+C durante processamento → Volta ao prompt

### 6. NO_COLOR Mode

```bash
NO_COLOR=1 uv run qa chat --mock
```

1. Verificar: Output legível sem cores
2. Verificar: Ícones ASCII em vez de emoji

---

## Debugging

### Logs Verbose

```bash
# Habilitar logs de debug
LOG_LEVEL=DEBUG uv run qa chat --mock
```

### Verificar Conexão WebSocket

```bash
# Testar conectividade com wscat (npm install -g wscat)
wscat -c ws://localhost:8000/ws/query/interpret

# Enviar mensagem de teste
{"type": "interpret", "prompt": "teste"}
```

---

## Lint e Type Check

```bash
# Lint
uv run ruff check src/cli/chat/ tests/unit/cli/chat/

# Type check
uv run mypy src/cli/chat/ tests/unit/cli/chat/

# Format
uv run black src/cli/chat/ tests/unit/cli/chat/
```

---

## Troubleshooting

### "Connection refused" ao conectar

1. Verificar se backend está rodando: `curl http://localhost:8000/health`
2. Verificar URL do WebSocket: deve ser `ws://` (não `http://`)
3. Usar `--mock` para desenvolvimento offline

### Terminal muito estreito

1. Aumentar largura do terminal para 60+ colunas
2. Painéis se adaptam automaticamente

### Emoji não aparecem

1. Usar terminal moderno (iTerm2, Windows Terminal, VS Code)
2. Ou rodar com `NO_COLOR=1` para fallback ASCII

### Timeout em queries

1. Backend pode estar sobrecarregado
2. Verificar logs do backend
3. Usar modo mock para testes

---

## Próximos Passos

1. **Implementar módulos** na ordem definida no plan.md
2. **TDD**: Escrever testes antes de cada módulo
3. **Verificar**: `uv run pytest` e `uv run mypy` a cada mudança
4. **Testar manualmente** os cenários acima

---

**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)
