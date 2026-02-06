# Feature Specification: CLI Chat Interativo para QAUserSearch

**Feature Branch**: `005-cli-chat`  
**Created**: 2026-02-05  
**Status**: Clarified  
**Clarified**: 2026-02-05  
**Input**: User description: "CLI Chat Interativo para QAUserSearch - Um CLI chat moderno e intuitivo que permite aos usuários fazer queries em linguagem natural via WebSocket, com sugestões inteligentes e feedback visual em tempo real."
**Plan Reference**: `docs/plans/03P-cli-chat.md`
**Depends on**: [`003-cli-shared-ui`](../003-cli-shared-ui/spec.md) (infraestrutura compartilhada de UI)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sessão de Chat Básica (Priority: P1)

Como usuário de QA, quero iniciar uma sessão de chat interativa onde posso digitar queries em linguagem natural e receber resultados interpretados com SQL gerado, para encontrar massas de teste de forma conversacional e intuitiva.

**Why this priority**: Este é o fluxo core do CLI chat. Sem ele, não há produto viável. É a funcionalidade mínima que entrega valor ao usuário - a capacidade de fazer perguntas em linguagem natural e obter queries SQL.

**Independent Test**: Pode ser testado executando `qa chat --mock` e digitando "usuários com cartão ativo", verificando que a interpretação e SQL são exibidos corretamente.

**Acceptance Scenarios**:

1. **Given** o CLI está em modo mock, **When** o usuário executa `qa chat --mock`, **Then** a welcome screen é exibida com banner ASCII, instruções e exemplos de queries
2. **Given** o CLI está no prompt de input, **When** o usuário digita "usuários com cartão de crédito ativo" e pressiona Enter, **Then** um spinner animado aparece durante processamento e painéis de interpretação e SQL são exibidos
3. **Given** a interpretação foi recebida, **When** os dados são exibidos, **Then** o painel mostra: resumo, barra de confiança colorida, tabela de entidades e tabela de filtros
4. **Given** a query SQL foi gerada, **When** os dados são exibidos, **Then** o painel mostra SQL com syntax highlighting (palavras-chave em azul, strings em verde, números em amarelo)

---

### User Story 2 - Feedback Visual em Tempo Real (Priority: P1)

Como usuário de QA, quero ver feedback visual durante o processamento da minha query (spinners, fases, status), para saber que o sistema está trabalhando e em qual etapa está.

**Why this priority**: Operações de IA podem demorar segundos. Sem feedback, usuários pensam que o sistema travou. É crítico para UX e diferencia uma ferramenta profissional de um script básico.

**Independent Test**: Pode ser testado observando a sequência de spinners e mensagens de status durante uma query no modo mock com delays simulados.

**Acceptance Scenarios**:

1. **Given** uma query foi enviada, **When** o processamento inicia, **Then** um PhaseSpinner é exibido com fases: "Analisando prompt", "Identificando entidades", "Gerando query"
2. **Given** o PhaseSpinner está ativo, **When** cada fase completa, **Then** o indicador visual muda de "em andamento" (roxo animado) para "completo" (verde com check)
3. **Given** mensagens de status chegam via WebSocket, **When** uma mensagem de status é recebida, **Then** o texto do status atual é atualizado em tempo real
4. **Given** chunks de streaming chegam, **When** há conteúdo parcial da IA, **Then** o conteúdo é exibido progressivamente (typewriter effect opcional)

---

### User Story 3 - Comandos Especiais do Chat (Priority: P1)

Como usuário de QA, quero ter comandos especiais (/exit, /help, /clear, /history) para controlar a sessão de chat sem sair do contexto conversacional.

**Why this priority**: Comandos especiais são essenciais para navegação básica. Sem /exit, o usuário ficaria preso. /help é necessário para descoberta. São pré-requisitos para usabilidade mínima.

**Independent Test**: Pode ser testado executando cada comando especial e verificando o comportamento esperado.

**Acceptance Scenarios**:

1. **Given** o CLI está no prompt de input, **When** o usuário digita `/exit` ou `/quit`, **Then** a sessão é encerrada graciosamente com mensagem de despedida
2. **Given** o CLI está no prompt de input, **When** o usuário digita `/help`, **Then** um painel é exibido listando todos os comandos disponíveis com descrições
3. **Given** o CLI tem conteúdo na tela, **When** o usuário digita `/clear`, **Then** a tela é limpa e a welcome screen é reexibida
4. **Given** queries foram feitas na sessão, **When** o usuário digita `/history`, **Then** uma lista das últimas 10 queries é exibida com timestamps
5. **Given** uma query SQL válida foi gerada, **When** o usuário digita `/execute`, **Then** uma mensagem informativa é exibida: "Query seria executada com limit=100" (simulação na v1)
6. **Given** o CLI está em modo real, **When** o usuário digita `/mock`, **Then** o modo mock é ativado/desativado com feedback visual

---

### User Story 4 - Modo Mock para Desenvolvimento (Priority: P2)

Como desenvolvedor do QAUserSearch, quero poder executar o CLI chat em modo mock (sem servidor WebSocket) com respostas simuladas realistas, para desenvolver e testar o frontend independentemente do backend.

**Why this priority**: Permite desenvolvimento paralelo frontend/backend. Essencial para testes automatizados e CI. Reduz dependências durante desenvolvimento.

**Independent Test**: Pode ser testado executando `qa chat --mock` sem servidor rodando e verificando que todas as funcionalidades UI funcionam com dados simulados.

**Acceptance Scenarios**:

1. **Given** nenhum servidor WebSocket está rodando, **When** o usuário executa `qa chat --mock`, **Then** o CLI inicia normalmente usando o MockChatClient
2. **Given** o modo mock está ativo, **When** uma query é enviada, **Then** o mock retorna interpretação realista com delay simulado (500-2000ms)
3. **Given** o modo mock está ativo, **When** uma query com "erro" é enviada, **Then** o mock retorna cenário de erro apropriado
4. **Given** o modo mock está ativo, **When** uma query com "ambiguidade" é enviada, **Then** o mock retorna interpretação com ambiguidades críticas simuladas

---

### User Story 5 - Sugestões Interativas para Ambiguidades (Priority: P2)

Como usuário de QA, quando minha query tem ambiguidades (ex: "ativo" pode significar status da conta ou do cartão), quero ver opções interativas para esclarecer, para refinar minha busca sem precisar reformular toda a query.

**Why this priority**: Ambiguidades são comuns em linguagem natural. Sem mecanismo de refinamento, usuários teriam que adivinhar a reformulação correta. Melhora significativamente a experiência.

**Independent Test**: Pode ser testado enviando query ambígua no mock e verificando que opções aparecem e seleção refina a query.

**Acceptance Scenarios**:

1. **Given** a interpretação retornou ambiguidades críticas, **When** os dados são processados, **Then** um painel de "Ambiguidade Detectada" é exibido com contexto
2. **Given** o painel de ambiguidade está ativo, **When** opções são apresentadas, **Then** um prompt Questionary select aparece com as opções possíveis
3. **Given** o usuário está navegando as opções, **When** usa setas ↑↓, **Then** a seleção é atualizada visualmente
4. **Given** o usuário selecionou uma opção, **When** pressiona Enter, **Then** a query é refinada automaticamente com a clarificação
5. **Given** nenhuma opção satisfaz o usuário, **When** seleciona "Escrever própria resposta", **Then** um prompt de texto livre aparece

---

### User Story 6 - Conexão WebSocket Real (Priority: P2)

Como usuário de QA em produção, quero que o CLI conecte ao backend real via WebSocket para receber interpretações e queries SQL em tempo real, para usar o sistema em ambiente de trabalho.

**Why this priority**: É o modo de operação real. Sem isso, o CLI seria apenas uma demo. Permite integração com o backend de IA já implementado.

**Independent Test**: Pode ser testado executando `qa chat --server ws://localhost:8000/ws/query/interpret` com backend rodando.

**Acceptance Scenarios**:

1. **Given** o backend está rodando, **When** o usuário executa `qa chat`, **Then** o CLI conecta ao WebSocket default (ws://localhost:8000/ws/query/interpret)
2. **Given** o CLI está conectado, **When** uma query é enviada, **Then** mensagens streaming (status, chunk, interpretation, query) são recebidas e processadas
3. **Given** a conexão WebSocket cai, **When** o usuário envia próxima query, **Then** o CLI tenta reconectar automaticamente até 3 vezes com backoff exponencial
4. **Given** reconexão falhou, **When** todas as tentativas se esgotaram, **Then** uma mensagem de erro clara é exibida com sugestão de verificar o servidor
5. **Given** o usuário quer usar servidor diferente, **When** executa `qa chat --server ws://outro:8000/ws/query/interpret`, **Then** conecta ao servidor especificado

---

### User Story 7 - Entry Point Unificado (Priority: P3)

Como usuário do QAUserSearch, quero um comando único `qa` com subcomandos claros (`qa chat`, `qa catalog`), para ter experiência CLI consistente e organizada.

**Why this priority**: Organização do CLI. Melhora DX mas não é bloqueante para funcionalidade core. Pode ser implementado após funcionalidades principais.

**Independent Test**: Pode ser testado executando `qa --help` e verificando que subcomandos são listados corretamente.

**Acceptance Scenarios**:

1. **Given** o CLI está instalado, **When** o usuário executa `qa --help`, **Then** os subcomandos disponíveis são listados: `chat`, `catalog`
2. **Given** o CLI está instalado, **When** o usuário executa `qa chat --help`, **Then** a ajuda específica do chat é exibida com flags disponíveis
3. **Given** o CLI está instalado, **When** o usuário executa `qa catalog --help`, **Then** a ajuda do catálogo é exibida (já existente)

---

### Edge Cases

- **WebSocket desconectado durante query**: Exibir erro amigável e oferecer retry
- **Query muito longa (>2000 chars)**: Rejeitar no input com mensagem clara de limite
- **Terminal muito estreito (<60 cols)**: Painéis usam largura total sem bordas decorativas
- **Ctrl+C durante input**: Sair graciosamente sem stack trace
- **Ctrl+C durante processamento**: Cancelar operação e voltar ao prompt
- **Servidor retorna erro 500**: Exibir mensagem genérica sem expor detalhes técnicos
- **Timeout de resposta (>30s)**: Cancelar e exibir mensagem de timeout
- **Terminal sem TTY (pipe)**: Modo não-interativo com output simplificado
- **Caracteres especiais na query**: Escape apropriado para não quebrar parsing

---

## Requirements *(mandatory)*

### Functional Requirements

#### Core
- **FR-001**: Sistema DEVE fornecer entry point `qa chat` para iniciar sessão de chat interativa
- **FR-002**: Sistema DEVE exibir welcome screen com banner ASCII, instruções e exemplos ao iniciar
- **FR-003**: Sistema DEVE aceitar input em linguagem natural via prompt interativo
- **FR-004**: Sistema DEVE processar queries via WebSocket client assíncrono

#### Feedback Visual
- **FR-005**: Sistema DEVE exibir spinner animado durante processamento de queries
- **FR-006**: Sistema DEVE exibir PhaseSpinner com fases distintas: análise, identificação, geração
- **FR-007**: Sistema DEVE renderizar interpretação em painel estilizado com: resumo, confiança, entidades, filtros
- **FR-008**: Sistema DEVE renderizar SQL gerada com syntax highlighting (SQL keywords coloridos)
- **FR-009**: Sistema DEVE exibir barra de confiança visual colorida (verde alto, âmbar médio, vermelho baixo)

#### Comandos Especiais
- **FR-010**: Sistema DEVE processar comando `/exit` ou `/quit` para encerrar sessão
- **FR-011**: Sistema DEVE processar comando `/help` para exibir ajuda
- **FR-012**: Sistema DEVE processar comando `/clear` para limpar tela
- **FR-013**: Sistema DEVE processar comando `/history` para listar as 10 últimas queries
- **FR-014**: Sistema DEVE processar comando `/execute` para simular execução da última query (v1: exibe mensagem informativa)
- **FR-015**: Sistema DEVE processar comando `/mock` para alternar modo mock on/off

#### Sugestões
- **FR-016**: Sistema DEVE detectar ambiguidades críticas na interpretação
- **FR-017**: Sistema DEVE exibir prompt interativo Questionary quando ambiguidades existem
- **FR-018**: Sistema DEVE permitir seleção via setas ↑↓ e Enter
- **FR-019**: Sistema DEVE enviar refinamento ao servidor após seleção de sugestão

#### Mock
- **FR-020**: Sistema DEVE fornecer flag `--mock` para iniciar em modo simulado
- **FR-021**: Sistema DEVE ter MockChatClient com mesma interface do WSChatClient
- **FR-022**: Sistema DEVE simular delays realistas (500-2000ms) em modo mock
- **FR-023**: Sistema DEVE suportar cenários de erro simulados em modo mock

#### Conexão
- **FR-024**: Sistema DEVE fornecer flag `--server` para especificar URL WebSocket
- **FR-025**: Sistema DEVE implementar reconnection automática com backoff exponencial
- **FR-026**: Sistema DEVE exibir erro claro quando conexão falha permanentemente

### Non-Functional Requirements

- **NFR-001**: Feedback visual DEVE aparecer em <100ms após input do usuário
- **NFR-002**: Prompts DEVEM responder a navegação em <50ms
- **NFR-003**: CLI DEVE funcionar em terminais de 60+ colunas
- **NFR-004**: CLI DEVE funcionar com `NO_COLOR=1` (output legível sem cores)
- **NFR-005**: Código DEVE ter 0 erros mypy/ruff/black
- **NFR-006**: Cobertura de testes unitários DEVE ser >80% para lógica de negócio
- **NFR-007**: CLI DEVE gracefully handle Ctrl+C em qualquer momento

### Key Entities

- **WSChatClient**: Cliente WebSocket assíncrono para comunicação com backend. Gerencia conexão, envio de prompts e recebimento de mensagens streaming.
- **MockChatClient**: Cliente mock com mesma interface para desenvolvimento offline. Simula delays e retorna dados realistas.
- **ChatSession**: Gerencia estado da sessão: histórico de queries, última interpretação, última query SQL.
- **MessageHandler**: Processa mensagens WebSocket por tipo (status, chunk, interpretation, query, error).
- **InterpretationPanel**: Painel Rich que renderiza interpretação com resumo, confiança, entidades e filtros.
- **QueryPanel**: Painel Rich que renderiza SQL com syntax highlighting.
- **SuggestionHandler**: Detecta ambiguidades e orquestra prompts Questionary para refinamento.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário consegue completar fluxo básico: iniciar chat → digitar query → ver interpretação → ver SQL em <10 segundos (modo mock)
- **SC-002**: Todos os 6 comandos especiais (/exit, /help, /clear, /history, /execute, /mock) funcionam conforme especificado
- **SC-003**: Modo mock funciona 100% offline sem servidor WebSocket
- **SC-004**: Reconexão automática funciona em caso de queda de conexão (testado com kill do servidor)
- **SC-005**: Zero erros de mypy/ruff/black no módulo `src/cli/chat/`
- **SC-006**: Cobertura de testes unitários >80% para `src/cli/chat/`
- **SC-007**: CLI responde a Ctrl+C em qualquer estado sem stack trace
- **SC-008**: Output é legível em terminal com `NO_COLOR=1`
- **SC-009**: Sugestões interativas funcionam para queries com ambiguidades (modo mock)
- **SC-010**: Entry point `qa` funciona com subcomandos `chat` e `catalog`

---

## Technical Context

### Stack Confirmada

| Componente | Tecnologia | Versão | Status |
|------------|------------|--------|--------|
| **UI Compartilhada** | `src/cli/shared/` | - | Depende do [spec 003-cli-shared-ui](../003-cli-shared-ui/spec.md) |
| **WebSocket Client** | websockets | >=12.0 | Já instalado |
| **CLI Framework** | Typer | >=0.15.0 | Já instalado |
| **Async** | asyncio | stdlib | Python 3.11+ |
| **Output Visual** | Rich | ^13.9.0 | Via shared UI |
| **Input Interativo** | Questionary | ^2.0.0 | Via shared UI |

### Estrutura de Arquivos

```
src/cli/
├── __init__.py
├── main.py                     # Entry point unificado (qa)
├── catalog.py                  # Subcomando existente (qa catalog)
├── chat.py                     # Subcomando novo (qa chat)
├── shared/                     # Do [spec 003-cli-shared-ui](../003-cli-shared-ui/spec.md)
│   ├── ui/
│   │   ├── theme.py
│   │   ├── panels.py
│   │   ├── progress.py
│   │   └── prompts.py
│   └── utils/
│       └── terminal.py
└── chat/                       # Módulo específico do chat
    ├── __init__.py
    ├── client.py               # WSChatClient async
    ├── mock_client.py          # MockChatClient
    ├── session.py              # ChatSession state management
    ├── renderer.py             # WelcomePanel, InterpretationPanel, QueryPanel
    └── handlers/
        ├── __init__.py
        ├── message_handler.py  # Processa mensagens WS por tipo
        └── suggestion_handler.py # Gerencia prompts de sugestão

tests/unit/cli/chat/
├── __init__.py
├── conftest.py                 # Fixtures: mock_ws, mock_session
├── test_client.py              # Testes WSChatClient
├── test_mock_client.py         # Testes MockChatClient
├── test_session.py             # Testes ChatSession
├── test_handlers.py            # Testes MessageHandler, SuggestionHandler
└── test_renderer.py            # Testes de renderização (lógica, não visual)
```

### Dependências entre Módulos

```
src/cli/shared/ui/ ─────────────────────────────────────────────┐
                                                                 │
src/cli/chat/                                                    │
    │                                                            │
    ├── client.py ──────────────────────────────────────────────┤
    │       └── websockets (async ws client)                    │
    │                                                            │
    ├── mock_client.py ─────────────────────────────────────────┤
    │       └── asyncio (delays simulados)                      │
    │                                                            │
    ├── session.py                                               │
    │       └── (sem deps externas)                             │
    │                                                            │
    ├── renderer.py ────────────────────────────────────────────┤
    │       └── rich (panels, syntax, tables)                   │
    │       └── shared/ui (create_panel, COLORS)                │
    │                                                            │
    └── handlers/                                                │
            ├── message_handler.py ─────────────────────────────┤
            │       └── renderer.py                             │
            │       └── shared/ui/progress (PhaseSpinner)       │
            │                                                    │
            └── suggestion_handler.py ──────────────────────────┘
                    └── shared/ui/prompts (ask_select)
```

### Protocolo WebSocket

O CLI consome mensagens do WebSocket já implementado em `src/api/v1/websocket/interpreter_ws.py`:

```python
# Tipos de mensagem recebidos (definidos em src/schemas/websocket.py)
WSStatusMessage:    {"type": "status", "data": {"status": str, "message": str}}
WSChunkMessage:     {"type": "chunk", "data": {"content": str, "agent": str}}
WSInterpretationMessage: {"type": "interpretation", "data": InterpretationResponse}
WSQueryMessage:     {"type": "query", "data": QueryResponse}
WSErrorMessage:     {"type": "error", "data": ErrorResponse}
```

---

## Out of Scope

- Execução real de queries no banco de dados QA (apenas estrutura de `/execute`)
- Persistência de histórico de chat entre sessões
- Autenticação/autorização de usuários
- Métricas e telemetria de uso
- Internacionalização (i18n) - mensagens em português fixo
- Modo offline com cache de interpretações anteriores
- Autocompletion de queries baseado em histórico

---

## Clarifications (Resolved 2026-02-05)

### CL-001: Limite do Histórico

**Pergunta**: Quantas queries devem ser mantidas no histórico acessível via `/history`?

**Decisão**: **10 últimas queries**

**Rationale**: Suficiente para maioria dos casos de uso em sessões normais, sem consumo excessivo de memória. Usuários que precisam de mais histórico podem usar logs externos.

### CL-002: Comportamento do /execute

**Pergunta**: O que o comando `/execute` deve fazer na implementação inicial?

**Decisão**: **Simular execução com mensagem**

**Rationale**: Na v1, o comando `/execute` exibirá mensagem informativa: "Query seria executada com limit=100". Execução real será adicionada em spec futuro após validação do fluxo de segurança. Isso é seguro para lançamento inicial.

### CL-003: Confirmação antes de /execute

**Pergunta**: O comando `/execute` deve pedir confirmação antes de executar (quando implementação real for adicionada)?

**Decisão**: **Não, executar diretamente**

**Rationale**: Mais fluido para power users. O comando `/execute` é explícito o suficiente. Se execução acidental for problema, usuário pode usar Ctrl+C. A simulação na v1 é segura de qualquer forma.

---

## Dependencies

### Hard Dependencies (bloqueantes)

1. **[003-cli-shared-ui](../003-cli-shared-ui/spec.md)** - Infraestrutura compartilhada de UI
   - Painéis estilizados (info_panel, error_panel, etc.)
   - PhaseSpinner para feedback de fases
   - Prompts Questionary (ask_select, ask_confirm)
   - Sistema de tema (COLORS, get_rich_theme)
   - Utilitários de terminal (supports_color, is_interactive)

### Soft Dependencies (recomendadas)

1. **001-llm-query-interpreter** - WebSocket backend (para modo real)
   - Endpoint `ws://localhost:8000/ws/query/interpret`
   - Schemas de mensagem WebSocket

---

## Quality Checklist

- [x] User Stories têm prioridades definidas (P1/P2/P3)
- [x] Cada User Story é independentemente testável
- [x] Acceptance Scenarios seguem formato Given/When/Then
- [x] Requirements são específicos e mensuráveis (MUST/SHOULD)
- [x] Key Entities estão identificadas com responsabilidades
- [x] Success Criteria são quantificáveis
- [x] Edge Cases estão documentados
- [x] Dependências estão identificadas e priorizadas
- [x] Technical Context inclui stack e estrutura
- [x] Out of Scope delimita claramente limites da feature
