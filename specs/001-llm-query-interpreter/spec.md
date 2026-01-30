<!--
╔════════════════════════════════════════════════════════════════════════════╗
║ 🇧🇷 IDIOMA: Este template deve ser preenchido em PORTUGUÊS BRASILEIRO.     ║
╚════════════════════════════════════════════════════════════════════════════╝
-->

# Feature Specification: Interpretador LLM para Geração de Queries

**Feature Branch**: `001-llm-query-interpreter`  
**Created**: 2026-01-30  
**Status**: Draft  
**Input**: User description: "Interpretador que utiliza LLM para interpretar um prompt e gerar uma query para obter os dados"

## Clarifications

### Session 2026-01-30

- Q: Qual provider LLM será utilizado e qual comportamento quando falhar? → A: OpenAI GPT-4 com retry simples (3 tentativas)
- Q: Todos os testadores QA podem acessar todos os dados, ou há controle por perfil/equipe? → A: Acesso irrestrito - todos os QAs veem todos os dados de teste
- Q: Qual o timeout máximo para a interpretação LLM? → A: 15 segundos
- Q: Há limite de requisições por usuário? → A: Sem limite (confiar no bom uso)
- Q: Como tratar prompts muito genéricos que retornariam milhões de registros? → A: Retornar primeiros 100, alertar sobre resultado parcial e sugerir refinamento
- Q: Qual estratégia de prevenção de injeção SQL será utilizada? → A: Blacklist de comandos proibidos (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER bloqueados)
- Q: Qual comportamento quando uma query é bloqueada por conter comandos proibidos? → A: Retornar erro detalhado ao usuário (qual comando foi bloqueado) + registrar em log de auditoria
- Q: Quais informações registrar no log de auditoria? → A: Query + timestamp + prompt original + resultado - somente para queries bloqueadas (sem identificação do usuário)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Busca por Cenário em Linguagem Natural (Priority: P1)

Como testador de QA, quero descrever em linguagem natural o tipo de massa de usuários que preciso (ex: "usuários com cartão de crédito ativo e fatura vencida há mais de 30 dias") e o sistema deve interpretar minha descrição e gerar automaticamente uma query que retorne os dados correspondentes.

**Why this priority**: Esta é a funcionalidade core da feature - sem ela, não existe valor entregue. Permite que testadores encontrem massas de dados sem conhecimento técnico de SQL ou da estrutura do banco.

**Independent Test**: Pode ser testado fornecendo um prompt em linguagem natural e verificando se o sistema retorna dados relevantes que correspondem à descrição.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado no sistema, **When** ele digita "usuários com cartão de crédito ativo", **Then** o sistema gera uma query válida e retorna uma lista de usuários que possuem cartão de crédito com status ativo.
2. **Given** um usuário autenticado no sistema, **When** ele digita "clientes com empréstimo aprovado nos últimos 7 dias", **Then** o sistema interpreta a condição temporal e retorna usuários com empréstimos aprovados dentro do período especificado.
3. **Given** um usuário autenticado no sistema, **When** ele digita um prompt ambíguo como "usuários novos", **Then** o sistema solicita esclarecimento ou aplica uma interpretação padrão razoável (ex: cadastrados nos últimos 30 dias).

---

### User Story 2 - Feedback de Interpretação (Priority: P2)

Como testador de QA, quero visualizar como o sistema interpretou meu prompt antes de executar a query, para que eu possa confirmar que a interpretação está correta ou ajustar minha descrição.

**Why this priority**: Garante transparência e confiança no sistema. Permite que o usuário entenda o que será buscado antes da execução.

**Independent Test**: Pode ser testado verificando se o sistema exibe um resumo da interpretação antes de executar a busca.

**Acceptance Scenarios**:

1. **Given** um usuário que digitou um prompt de busca, **When** o sistema processa o prompt, **Then** exibe um resumo em linguagem natural dos critérios que serão aplicados (ex: "Buscarei usuários onde: cartão de crédito = ativo E fatura = vencida E dias de atraso > 30").
2. **Given** um usuário visualizando a interpretação, **When** ele identifica que a interpretação está incorreta, **Then** pode modificar seu prompt e resubmeter sem perder o contexto anterior.

---

### User Story 3 - Tratamento de Erros e Sugestões (Priority: P3)

Como testador de QA, quando meu prompt não puder ser interpretado ou não encontrar resultados, quero receber mensagens claras explicando o problema e sugestões de como reformular minha busca.

**Why this priority**: Melhora a experiência do usuário e reduz frustração quando buscas falham.

**Independent Test**: Pode ser testado fornecendo prompts inválidos ou que não retornam resultados e verificando se o sistema fornece feedback útil.

**Acceptance Scenarios**:

1. **Given** um usuário que digitou um prompt que não corresponde a nenhum dado existente, **When** a query é executada, **Then** o sistema informa que nenhum resultado foi encontrado e sugere critérios alternativos ou mais amplos.
2. **Given** um usuário que digitou um prompt com termos não reconhecidos, **When** o sistema não consegue interpretar, **Then** exibe uma mensagem explicando quais termos não foram entendidos e sugere termos similares disponíveis no catálogo.

---

### Edge Cases

- O que acontece quando o prompt contém termos conflitantes (ex: "usuários ativos e inativos")?
- Quando o prompt é muito genérico e retornaria milhões de registros, o sistema retorna os primeiros 100 resultados, exibe alerta informando que o resultado é parcial, e sugere critérios de refinamento para busca mais específica
- O que acontece quando o usuário menciona entidades ou campos que não existem no banco?
- Quando o LLM (OpenAI GPT-4) está indisponível, o sistema realiza até 3 tentativas com backoff exponencial antes de retornar erro ao usuário
- Quando a query gerada contém comandos proibidos (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER), o sistema bloqueia a execução, retorna erro detalhado ao usuário informando qual comando foi bloqueado, e registra a ocorrência em log de auditoria

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE aceitar prompts em qualquer idioma
- **FR-002**: O sistema DEVE interpretar o prompt e identificar as entidades e filtros desejados
- **FR-003**: O sistema DEVE gerar uma query válida baseada na interpretação do prompt
- **FR-004**: O sistema DEVE executar a query gerada e retornar os resultados ao usuário
- **FR-005**: O sistema DEVE exibir um resumo da interpretação antes de executar a query
- **FR-006**: O sistema DEVE limitar o número de resultados retornados para evitar sobrecarga (padrão: 10 registros)
- **FR-007**: O sistema DEVE validar se a query gerada é segura antes de executá-la utilizando blacklist de comandos proibidos (INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER são bloqueados; apenas SELECT permitido)
- **FR-008**: O sistema DEVE registrar em log de auditoria todas as queries bloqueadas, contendo: query gerada, timestamp, prompt original e motivo do bloqueio (sem identificação do usuário)
- **FR-009**: O sistema DEVE informar o usuário quando não conseguir interpretar o prompt com mensagem clara
- **FR-010**: O sistema DEVE sugerir termos ou reformulações quando a busca não retornar resultados
- **FR-011**: O sistema DEVE utilizar o catálogo de metadados existente para validar entidades e campos mencionados no prompt

### Key Entities

- **Prompt**: Texto em linguagem natural fornecido pelo usuário descrevendo os dados desejados
- **Interpretação**: Representação estruturada do entendimento do sistema sobre o prompt (entidades, filtros, condições)
- **Query Gerada**: Consulta resultante da interpretação, pronta para execução no banco de dados
- **Resultado de Busca**: Conjunto de dados retornados após execução da query

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários conseguem encontrar massas de dados relevantes em menos de 2 minutos usando linguagem natural
- **SC-002**: 80% dos prompts simples (até 2 condições) são interpretados corretamente na primeira tentativa
- **SC-003**: 100% das queries geradas são validadas quanto à segurança antes da execução
- **SC-004**: Usuários compreendem a interpretação do sistema em 90% dos casos sem necessidade de ajuda adicional
- **SC-005**: Redução de 60% no tempo médio gasto por testadores para encontrar massas de dados específicas
- **SC-006**: Tempo máximo de resposta do LLM para interpretação do prompt: 15 segundos (timeout)

## Assumptions

- O sistema já possui um catálogo de metadados com informações sobre tabelas, colunas e relacionamentos
- Os usuários estão autenticados através do sistema de login existente
- Todos os testadores QA autenticados têm acesso irrestrito a todos os dados de teste (sem segregação por equipe ou projeto)
- O ambiente de QA possui dados representativos para as buscas
- Existe conectividade com as bases de dados de QA
- O provider LLM é OpenAI GPT-4, com política de retry de 3 tentativas em caso de falha transitória
- Não há rate limiting por usuário; confia-se no uso responsável pelos testadores QA
