# Feature Specification: Infraestrutura Compartilhada de CLI UI

**Feature Branch**: `01-cli-shared-ui`  
**Created**: 2026-02-04  
**Status**: Clarified  
**Clarified**: 2026-02-04  
**Input**: User description: "Infraestrutura Compartilhada de CLI UI - Estabelecer uma infraestrutura compartilhada de UI para todos os CLIs do QAUserSearch, garantindo consistência visual, reutilização de código e manutenibilidade."
**Plan Reference**: `docs/plans/01-cli-shared-ui.md`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Painéis de Feedback Visual Consistentes (Priority: P1)

Como desenvolvedor do QAUserSearch, quero ter painéis de feedback visual padronizados (info, success, warning, error) para que todos os CLIs do projeto apresentem mensagens ao usuário de forma consistente e profissional.

**Why this priority**: Painéis são o componente mais básico e amplamente utilizado em qualquer CLI. São pré-requisito para todos os outros componentes e fornecem a base visual do sistema. Sem eles, não há consistência visual entre CLIs.

**Independent Test**: Pode ser testado criando um script que importa os painéis e renderiza cada tipo no terminal. O usuário vê imediatamente se as cores, ícones e formatação estão corretos.

**Acceptance Scenarios**:

1. **Given** um CLI precisa exibir uma mensagem de sucesso, **When** o desenvolvedor usa `success_panel("Operação concluída!", "Extração")`, **Then** um painel verde com ícone de check e borda estilizada é renderizado no terminal
2. **Given** um CLI precisa exibir um erro, **When** o desenvolvedor usa `error_panel("Conexão falhou", "Erro de Rede")`, **Then** um painel vermelho com ícone de X é renderizado sem expor stack trace ao usuário
3. **Given** um terminal sem suporte a cores (NO_COLOR=1), **When** qualquer painel é renderizado, **Then** o conteúdo é exibido sem códigos ANSI, mantendo legibilidade
4. **Given** um terminal com largura reduzida (60 colunas), **When** um painel é renderizado, **Then** o texto faz wrap corretamente dentro das bordas

---

### User Story 2 - Spinners e Progress Bars (Priority: P1)

Como desenvolvedor do QAUserSearch, quero ter spinners e barras de progresso padronizadas para indicar operações em andamento, permitindo que usuários saibam que o sistema está processando.

**Why this priority**: Operações de extração de catálogo e chamadas de IA podem demorar segundos ou minutos. Sem feedback de progresso, usuários pensam que o sistema travou. É fundamental para UX e já usado no CLI existente.

**Independent Test**: Pode ser testado executando uma operação assíncrona dentro de um context manager `spinner()` e verificando que o spinner aparece/desaparece corretamente.

**Acceptance Scenarios**:

1. **Given** uma operação assíncrona de duração indeterminada, **When** o desenvolvedor usa `with spinner("Conectando ao banco...")`, **Then** um spinner animado aparece durante a execução e desaparece ao completar
2. **Given** uma operação com progresso conhecido (10 itens), **When** o desenvolvedor usa `create_bar_progress()` e atualiza o progresso, **Then** uma barra de progresso mostra porcentagem, tempo decorrido e ETA
3. **Given** um processo com múltiplas fases (conectar, extrair, salvar), **When** o desenvolvedor usa `PhaseSpinner`, **Then** cada fase é exibida com indicador visual de completo/em andamento/pendente
4. **Given** uma operação é interrompida com Ctrl+C, **When** o spinner está ativo, **Then** o terminal retorna ao estado normal sem artefatos visuais

---

### User Story 3 - Prompts Interativos Padronizados (Priority: P1)

Como desenvolvedor do QAUserSearch, quero ter prompts interativos padronizados (text, confirm, select, checkbox) com tema visual consistente para coletar input do usuário de forma elegante.

**Why this priority**: Workflows de aprovação (catalog-ai-enrichment) e chat interativo (cli-chat) dependem fortemente de prompts. A consistência visual e de comportamento é crítica para usabilidade.

**Independent Test**: Pode ser testado chamando cada tipo de prompt e verificando que navegação por setas, seleção e submissão funcionam com o estilo visual do tema.

**Acceptance Scenarios**:

1. **Given** o CLI precisa de confirmação do usuário, **When** o desenvolvedor usa `ask_confirm("Deseja continuar?")`, **Then** um prompt sim/não estilizado aparece com cores do tema
2. **Given** o CLI precisa que o usuário selecione uma opção de uma lista, **When** o desenvolvedor usa `ask_select("Escolha o formato:", ["JSON", "YAML", "CSV"])`, **Then** uma lista navegável por setas aparece com highlighting no item selecionado
3. **Given** o CLI precisa de seleção múltipla, **When** o desenvolvedor usa `ask_checkbox("Selecione campos:", campos)`, **Then** checkboxes interativos aparecem permitindo toggle com Espaço e confirmação com Enter
4. **Given** o usuário pressiona Ctrl+C durante um prompt, **When** a interrupção ocorre, **Then** o prompt retorna `None` sem crash e o CLI pode tratar graciosamente

---

### User Story 4 - Prompt de Aprovação Reutilizável (Priority: P2)

Como desenvolvedor do workflow de enriquecimento de catálogo, quero ter um prompt de aprovação padronizado que ofereça opções de Aprovar/Editar/Rejeitar/Pular para usar em workflows de revisão humana.

**Why this priority**: O plano `02P-catalog-ai-enrichment` requer um fluxo de aprovação para cada campo enriquecido pela IA. Um prompt especializado evita duplicação e garante experiência consistente.

**Independent Test**: Pode ser testado chamando `ask_approval("block_code")` e verificando que todas as opções aparecem e retornam os valores corretos.

**Acceptance Scenarios**:

1. **Given** um campo precisa de revisão humana, **When** o desenvolvedor usa `ask_approval("block_code")`, **Then** um menu com opções Aprovar/Editar/Rejeitar/Pular/Cancelar aparece
2. **Given** edição não é aplicável ao contexto, **When** o desenvolvedor usa `ask_approval("item", allow_edit=False)`, **Then** a opção "Editar" não aparece no menu
3. **Given** skip não é permitido no workflow, **When** o desenvolvedor usa `ask_approval("item", allow_skip=False)`, **Then** a opção "Pular" não aparece no menu
4. **Given** o usuário seleciona "Aprovar", **When** a seleção é confirmada, **Then** a função retorna a string `"approve"` para tratamento programático

---

### User Story 5 - Sistema de Tema Unificado (Priority: P2)

Como desenvolvedor do QAUserSearch, quero ter um sistema de tema centralizado com paleta de cores e estilos para Rich e Questionary, garantindo que todos os componentes usem as mesmas cores.

**Why this priority**: A consistência visual depende de uma única fonte de verdade para cores e estilos. Sem um tema centralizado, cada componente pode usar cores diferentes, criando inconsistência.

**Independent Test**: Pode ser testado importando `COLORS` e `get_rich_theme()` e verificando que os valores correspondem à paleta definida.

**Acceptance Scenarios**:

1. **Given** um desenvolvedor precisa da cor de sucesso, **When** ele acessa `COLORS.SUCCESS`, **Then** recebe o código hex `#10B981` (verde esmeralda)
2. **Given** um painel Rich precisa do tema, **When** o desenvolvedor usa `Console(theme=get_rich_theme())`, **Then** todos os estilos nomeados (primary, success, error, etc.) estão disponíveis
3. **Given** um prompt Questionary precisa do estilo, **When** o desenvolvedor usa `get_questionary_style()`, **Then** o estilo retornado tem cores alinhadas com a paleta do tema Rich
4. **Given** a paleta precisa ser atualizada, **When** um desenvolvedor altera `COLORS.PRIMARY`, **Then** todos os componentes que referenciam essa cor são automaticamente atualizados

---

### User Story 6 - Utilitários de Terminal (Priority: P3)

Como desenvolvedor do QAUserSearch, quero ter utilitários para detectar capacidades do terminal (cores, unicode, tamanho) para que os componentes façam fallback gracioso em ambientes limitados.

**Why this priority**: Embora a maioria dos terminais modernos suporte cores e unicode, pipelines CI e alguns ambientes não suportam. O fallback garante que CLIs não quebrem nesses cenários.

**Independent Test**: Pode ser testado em ambiente com `NO_COLOR=1` ou `TERM=dumb` e verificando que a detecção funciona corretamente.

**Acceptance Scenarios**:

1. **Given** o terminal suporta cores, **When** `supports_color()` é chamado, **Then** retorna `True`
2. **Given** a variável `NO_COLOR=1` está definida, **When** `supports_color()` é chamado, **Then** retorna `False`
3. **Given** o terminal está em Windows sem Windows Terminal, **When** `supports_unicode()` é chamado, **Then** retorna `False` para evitar caracteres quebrados
4. **Given** o terminal tem 80x24, **When** `get_terminal_size()` é chamado, **Then** retorna `(80, 24)`

---

### User Story 7 - Console Pré-configurado (Priority: P3)

Como desenvolvedor do QAUserSearch, quero ter uma função factory para criar Console Rich pré-configurado com tema e detecção automática de capacidades para simplificar uso.

**Why this priority**: Reduz boilerplate em cada CLI que precisa criar um Console. Centraliza configuração e garante consistência.

**Independent Test**: Pode ser testado chamando `create_console()` e verificando que o Console retornado tem tema aplicado e respeita capacidades do terminal.

**Acceptance Scenarios**:

1. **Given** um desenvolvedor precisa de um Console, **When** ele chama `create_console()`, **Then** recebe um Console Rich com tema aplicado e detecção de cores/unicode
2. **Given** o terminal não suporta cores, **When** `create_console()` é chamado, **Then** o Console retornado tem `no_color=True`
3. **Given** o terminal não suporta unicode, **When** `create_console()` é chamado, **Then** o Console retornado tem `emoji=False`

---

### Edge Cases

- **Terminal sem TTY (pipe/redirect)**: Spinners imprimem mensagem única estática (sem animação). Prompts retornam `None` imediatamente sem bloquear.
- **Largura de terminal <60 colunas**: Painéis usam largura total disponível sem bordas decorativas.
- **Interrupção durante prompt (Ctrl+C)**: Deve retornar `None` sem exceção não tratada
- **Texto com caracteres especiais/unicode**: Painéis e prompts devem renderizar corretamente sem corrupção
- **Ambiente CI (GitHub Actions)**: Deve funcionar com output não-interativo, sem cores se apropriado
- **Progress bar com total=0**: Não deve causar divisão por zero ou comportamento estranho
- **Terminal sem suporte a Unicode**: Ícones usam fallback ASCII: `[OK]` `[X]` `[!]` `[i]`

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE fornecer painéis estilizados para os tipos: info, success, warning, error
- **FR-002**: Sistema DEVE fornecer spinner com animação para operações de duração indeterminada
- **FR-003**: Sistema DEVE fornecer progress bar com porcentagem, tempo decorrido e ETA para operações com progresso conhecido
- **FR-004**: Sistema DEVE fornecer PhaseSpinner para operações com múltiplas fases sequenciais, usando dataclass `Phase(key, label, icon)`
- **FR-005**: Sistema DEVE fornecer prompts interativos: text, confirm, select, checkbox
- **FR-006**: Sistema DEVE fornecer prompt de aprovação especializado retornando `ApprovalResult` enum (APPROVE/EDIT/REJECT/SKIP/CANCEL)
- **FR-007**: Sistema DEVE fornecer namespace de cores centralizado (`COLORS`) com constantes semânticas
- **FR-008**: Sistema DEVE fornecer tema Rich (`get_rich_theme()`) alinhado com a paleta
- **FR-009**: Sistema DEVE fornecer estilo Questionary (`get_questionary_style()`) alinhado com a paleta
- **FR-010**: Sistema DEVE fornecer utilitários para detectar suporte a cores e unicode no terminal
- **FR-011**: Sistema DEVE fornecer factory function para criar Console Rich pré-configurado
- **FR-012**: Sistema DEVE fazer fallback gracioso em terminais sem suporte a cores/unicode
- **FR-013**: Sistema DEVE tratar interrupção (Ctrl+C) em prompts retornando `None` sem exceção
- **FR-014**: Sistema DEVE exportar todos os componentes públicos via `from src.cli.shared.ui import *`

### Non-Functional Requirements

- **NFR-001**: Componentes DEVEM ser type-safe com 100% de cobertura de type hints (mypy strict)
- **NFR-002**: Componentes DEVEM ter docstrings Google-style documentando uso
- **NFR-003**: Código DEVE passar em lint (ruff) e formatação (black) sem warnings
- **NFR-004**: Testes unitários DEVEM cobrir aspectos críticos: lógica do PhaseSpinner e tratamento de Ctrl+C
- **NFR-005**: Spinners DEVEM ter refresh rate ≤100ms para animação fluida
- **NFR-006**: Prompts DEVEM responder a input em <50ms para sensação responsiva

### Key Entities

- **COLORS**: Namespace com constantes de cores (`COLORS.SUCCESS = "#10B981"`) - simples e eficiente
- **Console**: Rich Console pré-configurado com tema e detecção de capacidades
- **Panel**: Rich Panel estilizado com ícone, título, subtítulo e borda colorida por tipo
- **Progress/Spinner**: Indicadores de progresso Rich para operações sync/async
- **Phase**: Dataclass para definir fases do PhaseSpinner: `Phase(key="connect", label="Conectando", icon="🔗")`
- **PhaseSpinner**: Componente customizado para múltiplas fases de progresso, recebe `list[Phase]`
- **ApprovalResult**: Enum com valores `APPROVE`, `EDIT`, `REJECT`, `SKIP`, `CANCEL` para type-safety
- **Prompt Functions**: Funções wrapper sobre Questionary com estilo aplicado

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos componentes são importáveis via `from src.cli.shared.ui import *` sem erros
- **SC-002**: Zero erros de mypy/ruff/black em todo o código do módulo `src/cli/shared/`
- **SC-003**: Testes unitários cobrem lógica crítica (PhaseSpinner, Ctrl+C handling)
- **SC-004**: Painéis renderizam corretamente em terminais de 60+ colunas (verificado manualmente)
- **SC-005**: Spinners animam fluidamente sem flicker visível (verificado manualmente)
- **SC-006**: Prompts respondem a navegação por setas e seleção sem delay perceptível
- **SC-007**: Em terminal com `NO_COLOR=1`, output é legível sem códigos ANSI
- **SC-008**: Plano `02P-catalog-ai-enrichment` consegue usar `ask_approval()` sem duplicação de código
- **SC-009**: Plano `03P-cli-chat` consegue usar painéis e spinners sem duplicação de código

---

## Technical Context

### Stack Confirmada

| Componente | Tecnologia | Versão | Status |
|------------|------------|--------|--------|
| **Output Visual** | Rich | ^13.9.0 | Já instalado |
| **Input Interativo** | Questionary | ^2.0.0 | Já instalado |
| **CLI Framework** | Typer | >=0.15.0 | Já instalado |

### Estrutura de Arquivos Proposta

```
src/cli/
├── __init__.py
├── catalog.py                    # CLI existente (não modificar)
├── chat.py                       # CLI chat (futuro, plano 03P)
│
└── shared/                       # ← NOVO: Módulo compartilhado
    ├── __init__.py               # Exports públicos
    ├── ui/
    │   ├── __init__.py           # Re-exports de todos componentes UI
    │   ├── theme.py              # ColorPalette, get_rich_theme, get_questionary_style
    │   ├── panels.py             # create_panel, info_panel, success_panel, etc.
    │   ├── progress.py           # spinner, create_bar_progress, PhaseSpinner
    │   └── prompts.py            # ask_text, ask_confirm, ask_select, ask_checkbox, ask_approval
    └── utils/
        ├── __init__.py           # Re-exports de utilitários
        └── terminal.py           # get_terminal_size, supports_color, supports_unicode, create_console
```

### Dependências entre Componentes

```
terminal.py ─────┐
                 │
theme.py ────────┼──────► panels.py
                 │           │
                 │           ▼
                 └──────► progress.py
                            │
                            ▼
                        prompts.py (usa theme.py diretamente)
```

### Integração com CLIs Existentes

O CLI `catalog.py` existente usa `typer.echo()` básico. Após esta feature:
- Novos CLIs (chat, enrichment) usarão os componentes compartilhados
- `catalog.py` pode ser migrado incrementalmente (não no escopo deste spec)

---

## Out of Scope

- Migração do CLI `catalog.py` existente para usar os novos componentes
- Implementação de tabelas Rich (pode ser adicionado em spec futuro se necessário)
- Suporte a temas configuráveis pelo usuário (dark/light)
- Persistência de preferências de UI
- Internacionalização de labels fixas dos componentes

---

## Open Questions

1. **Q**: O ícone dos painéis deve usar emoji ou caracteres ASCII?  
   **A**: Usar emoji por padrão, com fallback para ASCII se `supports_unicode()` retornar False.

2. **Q**: O estilo Questionary deve ter instruções em português ou inglês?  
   **A**: Português, seguindo o padrão do projeto.

3. **Q**: PhaseSpinner deve usar Live display do Rich ou print estático?  
   **A**: Live display para atualização in-place, com fallback para print estático em terminais sem suporte.

---

## Clarifications (Resolved 2026-02-04)

As seguintes ambiguidades foram identificadas e resolvidas durante a fase de clarificação:

### CL-001: Comportamento em Terminal sem TTY

**Ambiguidade**: O que acontece quando CLI roda em pipe/redirect (sem TTY)?

**Decisão**: 
- **Spinner**: Imprime mensagem única estática (ex: "Conectando ao banco...") sem animação
- **Prompts**: Retornam `None` imediatamente sem bloquear esperando input

**Rationale**: Permite uso em scripts e pipelines sem travar, enquanto mantém algum feedback.

### CL-002: Fallback de Unicode para ASCII

**Ambiguidade**: Quais caracteres ASCII substituem emojis quando `supports_unicode()` retorna False?

**Decisão**: Usar formato com brackets:
- ✅ → `[OK]`
- ❌ → `[X]`
- ⚠️ → `[!]`
- ℹ️ → `[i]`

**Rationale**: Formato legível e consistente, claramente distinguível dos textos de mensagem.

### CL-003: Largura Mínima de Terminal

**Ambiguidade**: Qual a largura mínima suportada e o que acontece abaixo dela?

**Decisão**: 
- **Mínimo**: 60 colunas
- **Comportamento**: Painéis usam largura total disponível sem bordas decorativas

**Rationale**: 60 colunas é suficiente para maioria dos casos, bordas são sacrificadas para preservar conteúdo.

### CL-004: Implementação do ColorPalette

**Ambiguidade**: Como implementar para permitir acesso `COLORS.SUCCESS`?

**Decisão**: Namespace com constantes no módulo (não dataclass):
```python
class COLORS:
    SUCCESS = "#10B981"
    ERROR = "#EF4444"
    # ...
```

**Rationale**: Simples, eficiente, sem overhead de instanciação, autocomplete funciona bem.

### CL-005: API do PhaseSpinner

**Ambiguidade**: Como definir as fases de um PhaseSpinner?

**Decisão**: Usar dataclass `Phase`:
```python
@dataclass(frozen=True)
class Phase:
    key: str
    label: str
    icon: str = "🔄"

spinner = PhaseSpinner([
    Phase("connect", "Conectando", "🔗"),
    Phase("extract", "Extraindo", "📦"),
    Phase("save", "Salvando", "💾"),
])
```

**Rationale**: Type-safe, extensível, permite metadados por fase, imutável.

### CL-006: Tipo de Retorno do ask_approval()

**Ambiguidade**: Retornar string ou tipo mais restrito?

**Decisão**: Enum `ApprovalResult`:
```python
class ApprovalResult(str, Enum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    SKIP = "skip"
    CANCEL = "cancel"
```

**Rationale**: Type-safety, autocomplete, impossível errar string, compatível com JSON (herda de str).

### CL-007: Escopo de Testes Unitários

**Ambiguidade**: O que testar em componentes visuais?

**Decisão**: Testes unitários focados apenas em aspectos críticos:
1. **PhaseSpinner lógica**: Verifica se fases avançam corretamente e timeout funciona
2. **Ctrl+C handling**: Verifica se interrupção retorna None e não levanta exceção

**Não testar**: Renderização visual de painéis, cores, formatação (verificação manual).

**Rationale**: Testes de UI visual têm baixo ROI e alta manutenção. Focar em lógica crítica que pode quebrar silenciosamente.
