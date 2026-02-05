# Plan: CLI Chat Interativo para QAUserSearch

**Data**: 2026-02-04  
**Status**: Draft  
**Autor**: Claude (AI Assistant)

## Objetivo

Criar um CLI chat moderno, visualmente impactante e intuitivo que permita aos usuários fazer queries em linguagem natural via WebSocket, com sugestões inteligentes e feedback visual em tempo real.

---

## Stack Tecnológica

| Componente | Tecnologia | Versão | Justificativa |
|------------|------------|--------|---------------|
| **Output Visual** | Rich | ^13.9.0 | Formatação terminal avançada (panels, tables, spinners, markdown) |
| **Input Interativo** | Questionary | ^2.0.0 | Prompts elegantes com seleção por setas |
| **WebSocket Client** | websockets | >=12.0 | Já instalado no projeto |
| **CLI Framework** | Typer | >=0.15.0 | Já instalado, integração nativa com Rich |
| **Async** | asyncio | stdlib | Necessário para WebSocket |

---

## Arquitetura

### Estrutura de Arquivos

```
src/cli/
├── __init__.py
├── catalog.py              # CLI existente (mantido)
├── chat.py                 # Entry point do CLI chat ← NOVO
├── chat/                   # Módulo do chat ← NOVO
│   ├── __init__.py
│   ├── client.py           # WebSocket client async
│   ├── mock_client.py      # Mock client para desenvolvimento
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py        # Tema de cores e estilos
│   │   ├── components.py   # Componentes visuais reutilizáveis
│   │   ├── renderer.py     # Renderiza mensagens do WebSocket
│   │   └── prompts.py      # Prompts interativos (questionary)
│   └── handlers/
│       ├── __init__.py
│       ├── message_handler.py   # Processa mensagens WS
│       └── suggestion_handler.py # Processa e exibe sugestões
```

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Chat (chat.py)                          │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   Welcome    │───▶│  User Input  │───▶│   Process    │         │
│  │   Screen     │    │   (prompt)   │    │   Command    │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│                             │                    │                  │
│                             │                    ▼                  │
│                             │           ┌──────────────┐           │
│                             │           │  /exit ?     │           │
│                             │           └──────────────┘           │
│                             │                    │                  │
│                             ▼                    ▼ No               │
│                      ┌──────────────────────────────────┐          │
│                      │       WebSocket Client           │          │
│                      │   (ou Mock Client em dev)        │          │
│                      └──────────────────────────────────┘          │
│                                      │                              │
│         ┌────────────────────────────┼─────────────────────┐       │
│         ▼                            ▼                     ▼       │
│  ┌──────────────┐         ┌──────────────┐       ┌──────────────┐ │
│  │    Status    │         │    Chunk     │       │    Result    │ │
│  │   Message    │         │   Message    │       │   Message    │ │
│  └──────────────┘         └──────────────┘       └──────────────┘ │
│         │                        │                      │          │
│         ▼                        ▼                      ▼          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                     UI Renderer                               │ │
│  │  • Spinners animados durante processamento                   │ │
│  │  • Panels coloridos para interpretação                       │ │
│  │  • Tabelas para filtros/entidades                           │ │
│  │  • Syntax highlighting para SQL                             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                      │                              │
│                                      ▼                              │
│                      ┌──────────────────────────┐                  │
│                      │  Sugestões Interativas?  │                  │
│                      └──────────────────────────┘                  │
│                           │ Sim              │ Não                 │
│                           ▼                  ▼                     │
│                    ┌────────────┐     ┌────────────┐              │
│                    │ Questionary│     │  Próximo   │              │
│                    │   Select   │     │   Prompt   │              │
│                    └────────────┘     └────────────┘              │
│                           │                  │                     │
│                           └────────┬─────────┘                    │
│                                    │                               │
│                                    ▼                               │
│                         ┌──────────────────┐                      │
│                         │   Loop (while)   │                      │
│                         └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Design Visual (UX)

### Paleta de Cores (Tema "Vibrant Modern")

```python
THEME = {
    # Cores primárias
    "primary": "#7C3AED",      # Roxo vibrante (brand)
    "secondary": "#06B6D4",    # Cyan (destaques)
    "accent": "#F59E0B",       # Âmbar (warnings/ênfase)
    
    # Status
    "success": "#10B981",      # Verde esmeralda
    "error": "#EF4444",        # Vermelho coral
    "warning": "#F59E0B",      # Âmbar
    "info": "#3B82F6",         # Azul
    
    # Confiança
    "confidence_high": "#10B981",    # Verde (>70%)
    "confidence_medium": "#F59E0B",  # Âmbar (50-70%)
    "confidence_low": "#EF4444",     # Vermelho (<50%)
    
    # Neutros
    "text": "#F9FAFB",         # Branco suave
    "text_dim": "#9CA3AF",     # Cinza para texto secundário
    "background": "#111827",   # Fundo escuro
    "border": "#374151",       # Bordas sutis
}
```

### Componentes Visuais

#### 1. Welcome Screen
```
╭─────────────────────────────────────────────────────────────────────╮
│                                                                     │
│    ██████╗  █████╗ ██╗   ██╗███████╗███████╗██████╗                │
│   ██╔═══██╗██╔══██╗██║   ██║██╔════╝██╔════╝██╔══██╗               │
│   ██║   ██║███████║██║   ██║███████╗█████╗  ██████╔╝               │
│   ██║▄▄ ██║██╔══██║██║   ██║╚════██║██╔══╝  ██╔══██╗               │
│   ╚██████╔╝██║  ██║╚██████╔╝███████║███████╗██║  ██║               │
│    ╚══▀▀═╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝               │
│                                                                     │
│                    🔍 QA User Search CLI                            │
│                                                                     │
│   Encontre massas de teste usando linguagem natural                │
│                                                                     │
│   Exemplos:                                                         │
│   • "usuários com cartão de crédito ativo"                         │
│   • "faturas vencidas do último mês"                               │
│   • "contas bloqueadas por fraude"                                 │
│                                                                     │
│   Comandos: /help /exit /clear /history                            │
│                                                                     │
╰─────────────────────────────────────────────────────────────────────╯
```

#### 2. Prompt de Input
```
┌ 🔍 QA Search ───────────────────────────────────────────────────────┐
│                                                                      │
│  Digite sua busca em linguagem natural:                             │
│  ▸ _                                                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### 3. Status de Processamento (Spinner + Fases)
```
⠋ Analisando prompt...
  ├─ ✓ Identificando entidades
  ├─ ⠙ Mapeando para catálogo...
  └─ ○ Gerando query
```

#### 4. Resultado da Interpretação
```
╭─ 📊 Interpretação ──────────────────────────────────────────────────╮
│                                                                      │
│  Resumo: Buscando usuários que possuem cartão de crédito com        │
│          status ativo na base de dados de cartões.                  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Confiança: ████████████████████░░░░░ 85% (alta)                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  📦 Entidades:                                                       │
│  ┌──────────────┬──────────────────────────┐                        │
│  │ Nome         │ Tabela                   │                        │
│  ├──────────────┼──────────────────────────┤                        │
│  │ card_main    │ card_account.card_main   │                        │
│  │ account_main │ card_account.account_main│                        │
│  └──────────────┴──────────────────────────┘                        │
│                                                                      │
│  🔍 Filtros:                                                         │
│  ┌──────────────┬──────────┬───────────────┐                        │
│  │ Campo        │ Operador │ Valor         │                        │
│  ├──────────────┼──────────┼───────────────┤                        │
│  │ card_type    │ =        │ credit        │                        │
│  │ status       │ =        │ active        │                        │
│  └──────────────┴──────────┴───────────────┘                        │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

#### 5. Query SQL Gerada
```
╭─ 💻 Query SQL ──────────────────────────────────────────────────────╮
│                                                                      │
│  SELECT c.*, a.*                                                    │
│  FROM card_account.card_main c                                      │
│  INNER JOIN card_account.account_main a ON c.account_id = a.id     │
│  WHERE c.card_type = 'credit'                                       │
│    AND c.status = 'active'                                          │
│  LIMIT 100;                                                         │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

#### 6. Sugestões Interativas (Questionary)
```
╭─ ⚠️ Ambiguidade Detectada ──────────────────────────────────────────╮
│                                                                      │
│  O termo "ativo" pode se referir a diferentes campos.               │
│  Selecione o significado desejado:                                  │
│                                                                      │
│    ❯ 1. Status da conta (account_status = 'ACTIVE')                 │
│      2. Status do cartão (card_status = 'ACTIVE')                   │
│      3. Último acesso recente (last_access > 30 dias)               │
│      4. Escrever minha própria resposta                             │
│                                                                      │
│  Use ↑↓ para navegar, Enter para selecionar                         │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

#### 7. Mensagem de Erro
```
╭─ ❌ Erro ────────────────────────────────────────────────────────────╮
│                                                                      │
│  Código: SQL_COMMAND_BLOCKED                                        │
│                                                                      │
│  Mensagem: Comando DELETE não é permitido. Apenas consultas         │
│            SELECT são aceitas.                                      │
│                                                                      │
│  💡 Sugestões:                                                       │
│  • Reformule seu pedido para buscar dados em vez de modificá-los    │
│  • Use termos como 'buscar', 'encontrar', 'listar'                  │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

---

## Fluxo de Interação

### 1. Inicialização
```bash
# Iniciar o chat (modo padrão - WebSocket)
qa-chat

# Iniciar em modo mock (desenvolvimento)
qa-chat --mock

# Especificar URL do servidor
qa-chat --server ws://localhost:8000/ws/query/interpret
```

### 2. Loop Principal
```
1. Exibir welcome screen
2. Loop:
   a. Mostrar prompt de input
   b. Receber entrada do usuário
   c. Se comando especial (/exit, /help, etc): processar
   d. Senão:
      i.   Conectar WebSocket (se não conectado)
      ii.  Enviar prompt
      iii. Processar mensagens streaming:
           - status → atualizar spinner
           - chunk → exibir progresso
           - interpretation → renderizar painel
           - query → renderizar SQL com syntax highlight
           - error → renderizar erro com sugestões
      iv.  Se há ambiguidades críticas:
           - Exibir questionary com opções
           - Enviar resposta refinada
      v.   Voltar ao prompt
```

### 3. Comandos Especiais
| Comando | Descrição |
|---------|-----------|
| `/exit` ou `/quit` | Sair do chat |
| `/help` | Mostrar ajuda |
| `/clear` | Limpar tela |
| `/history` | Ver últimas queries |
| `/execute` | Executar última query |
| `/mock` | Alternar modo mock on/off |

---

## Implementação

### Fase 1: Infraestrutura Base
**Estimativa**: 2-3 horas

1. **Adicionar dependências** ao `pyproject.toml`:
   ```toml
   "rich>=13.9.0",
   "questionary>=2.0.0",
   ```

2. **Criar estrutura de diretórios**:
   ```
   src/cli/chat/
   src/cli/chat/ui/
   src/cli/chat/handlers/
   ```

3. **Implementar tema** (`ui/theme.py`):
   - Definir paleta de cores
   - Criar estilos Rich reutilizáveis
   - Criar estilo Questionary customizado

4. **Adicionar entry point** no `pyproject.toml`:
   ```toml
   [project.scripts]
   qa-chat = "src.cli.chat:app"
   ```

### Fase 2: WebSocket Client
**Estimativa**: 2-3 horas

1. **Implementar `client.py`**:
   - Classe `WSChatClient` async
   - Métodos: `connect()`, `disconnect()`, `send_prompt()`, `receive_messages()`
   - Callback pattern para processar mensagens
   - Reconnection logic

2. **Implementar `mock_client.py`**:
   - Classe `MockChatClient` com mesma interface
   - Simula delays realistas
   - Retorna dados mock para cada fase
   - Suporta cenários de erro para testes

### Fase 3: UI Components
**Estimativa**: 3-4 horas

1. **Implementar `components.py`**:
   - `WelcomePanel`: Banner ASCII + instruções
   - `InterpretationPanel`: Resumo + confiança + entidades + filtros
   - `QueryPanel`: SQL com syntax highlighting
   - `ErrorPanel`: Erro + sugestões
   - `ConfidenceBar`: Barra de progresso colorida
   - `StatusSpinner`: Spinner com fases

2. **Implementar `renderer.py`**:
   - `MessageRenderer` class
   - Métodos para cada tipo de mensagem WS
   - Live display com Rich

3. **Implementar `prompts.py`**:
   - `get_user_input()`: Prompt principal
   - `show_suggestions()`: Questionary select
   - `confirm_action()`: Confirmações

### Fase 4: Handlers
**Estimativa**: 2-3 horas

1. **Implementar `message_handler.py`**:
   - Processar cada tipo de mensagem WS
   - Orquestrar atualizações de UI
   - Manter estado da sessão

2. **Implementar `suggestion_handler.py`**:
   - Detectar quando mostrar sugestões
   - Formatar opções para questionary
   - Processar resposta do usuário

### Fase 5: Entry Point e Integração
**Estimativa**: 2-3 horas

1. **Implementar `chat.py`**:
   - Typer CLI app
   - Flags: `--mock`, `--server`, `--verbose`
   - Comandos especiais (`/exit`, `/help`, etc.)
   - Loop principal assíncrono

2. **Testes**:
   - Testes unitários para componentes UI
   - Testes de integração com mock client
   - Testes E2E com servidor local (se disponível)

---

## Tarefas (Checklist)

### Fase 1: Infraestrutura Base
- [ ] Adicionar `rich>=13.9.0` ao pyproject.toml
- [ ] Adicionar `questionary>=2.0.0` ao pyproject.toml
- [ ] Criar diretório `src/cli/chat/`
- [ ] Criar diretório `src/cli/chat/ui/`
- [ ] Criar diretório `src/cli/chat/handlers/`
- [ ] Criar `src/cli/chat/__init__.py`
- [ ] Criar `src/cli/chat/ui/__init__.py`
- [ ] Criar `src/cli/chat/handlers/__init__.py`
- [ ] Implementar `src/cli/chat/ui/theme.py` com paleta de cores
- [ ] Adicionar entry point `qa-chat` no pyproject.toml

### Fase 2: WebSocket Client
- [ ] Implementar `src/cli/chat/client.py` (WSChatClient)
- [ ] Implementar `src/cli/chat/mock_client.py` (MockChatClient)
- [ ] Criar protocolo/interface comum para ambos os clients
- [ ] Implementar reconnection logic no WSChatClient

### Fase 3: UI Components
- [ ] Implementar `WelcomePanel` em components.py
- [ ] Implementar `InterpretationPanel` em components.py
- [ ] Implementar `QueryPanel` com syntax highlighting
- [ ] Implementar `ErrorPanel` em components.py
- [ ] Implementar `ConfidenceBar` em components.py
- [ ] Implementar `StatusSpinner` em components.py
- [ ] Implementar `MessageRenderer` em renderer.py
- [ ] Implementar prompts em prompts.py

### Fase 4: Handlers
- [ ] Implementar `MessageHandler` em message_handler.py
- [ ] Implementar `SuggestionHandler` em suggestion_handler.py
- [ ] Integrar handlers com UI components

### Fase 5: Entry Point e Integração
- [ ] Implementar `src/cli/chat.py` com Typer
- [ ] Implementar comandos especiais (/exit, /help, /clear, /history)
- [ ] Implementar loop principal assíncrono
- [ ] Criar testes unitários para componentes
- [ ] Criar testes de integração com mock client
- [ ] Documentar uso no README

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Conflito Rich/Questionary async | Média | Alto | Testar integração cedo; usar `asyncio.to_thread` se necessário |
| Performance em terminals lentos | Baixa | Médio | Modo `--simple` sem animações |
| WebSocket disconnects | Média | Médio | Implementar reconnection automático |
| Compatibilidade Windows | Média | Médio | Testar em Windows; fallback para ASCII |

---

## Critérios de Aceite

1. **Funcional**:
   - [ ] CLI inicia sem erros
   - [ ] Conecta ao WebSocket e envia prompts
   - [ ] Exibe feedback em tempo real (spinners, status)
   - [ ] Renderiza interpretação com entidades e filtros
   - [ ] Exibe SQL com syntax highlighting
   - [ ] Mostra sugestões interativas quando há ambiguidade
   - [ ] Modo mock funciona sem servidor

2. **Visual**:
   - [ ] Cores vibrantes e consistentes
   - [ ] Painéis bem formatados
   - [ ] Barra de confiança animada
   - [ ] Spinners suaves durante processamento

3. **UX**:
   - [ ] Tempo de resposta perceptível < 100ms para UI
   - [ ] Mensagens de erro claras e acionáveis
   - [ ] Navegação intuitiva com setas
   - [ ] Comandos de ajuda acessíveis

4. **Qualidade**:
   - [ ] Cobertura de testes > 80%
   - [ ] Zero erros de lint/mypy
   - [ ] Documentação de uso

---

## Referências

- [Rich Documentation](https://rich.readthedocs.io/)
- [Questionary Documentation](https://questionary.readthedocs.io/)
- [CLI UX Patterns](.agents/skills/cli-ux-patterns/SKILL.md)
- [WebSocket atual](src/api/v1/websocket/interpreter_ws.py)
- [Schemas WebSocket](src/schemas/websocket.py)
