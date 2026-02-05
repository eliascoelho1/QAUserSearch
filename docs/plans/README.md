# Plans - Ordem de Implementação

Este diretório contém os planos de implementação do QAUserSearch, ordenados por dependência e possibilidade de paralelização.

## Ordem de Implementação

### 1. Plan 01 - CLI Shared UI (Base)
**Arquivo**: `01-cli-shared-ui.md`  
**Status**: Infraestrutura base  
**Pré-requisitos**: Nenhum  
**Pré-requisito para**: Todos os planos CLI subsequentes

Estabelece infraestrutura compartilhada de UI para todos os CLIs do projeto (Rich, Questionary, tema de cores, componentes).

---

### 2. Plans Paralelizáveis [P] - Camada de Features

Estes planos podem ser implementados em paralelo após o Plan 01 estar completo.

#### Plan 02P - Catalog AI Enrichment
**Arquivo**: `02P-catalog-ai-enrichment.md`  
**Status**: Feature paralelizável  
**Pré-requisitos**: `01-cli-shared-ui.md`  
**Paralelizável com**: `03P-cli-chat.md`, `05P-fast-spec.md`

Enriquecimento semântico do catálogo de metadados com IA (OpenAI GPT-4).

#### Plan 03P - CLI Chat
**Arquivo**: `03P-cli-chat.md`  
**Status**: Feature paralelizável  
**Pré-requisitos**: `01-cli-shared-ui.md`  
**Paralelizável com**: `02P-catalog-ai-enrichment.md`, `05P-fast-spec.md`

CLI chat interativo para queries em linguagem natural via WebSocket.

#### Plan 05P - Fast Spec Skill
**Arquivo**: `05P-fast-spec.md`  
**Status**: Feature paralelizável  
**Pré-requisitos**: Nenhum (independente)  
**Paralelizável com**: `02P-catalog-ai-enrichment.md`, `03P-cli-chat.md`

Skill OpenCode para execução automatizada do fluxo completo de especificação.

---

### 3. Plan 04 - QA Plan Interpret Endpoint
**Arquivo**: `04-qa-plan-interpret-endpoint.md`  
**Status**: Plano de QA/Testes  
**Pré-requisitos**: `02P-catalog-ai-enrichment.md` (para testes de interpretação NL)  
**Depende de**: Enriquecimento semântico do catálogo completo

Plano de QA com 78 cenários de teste para o endpoint `/api/v1/query/interpret`.

---

## Legenda

- **[P]**: Indica planos paralelizáveis
- **Pré-requisito**: Deve ser concluído antes
- **Pré-requisito para**: Necessário para outros planos
- **Paralelizável com**: Pode ser desenvolvido simultaneamente

## Status de Implementação

| Plan | Status | Inicio | Conclusão |
|------|--------|--------|-----------|
| 01-cli-shared-ui | ⏳ Pendente | - | - |
| 02P-catalog-ai-enrichment | ⏳ Pendente | - | - |
| 03P-cli-chat | ⏳ Pendente | - | - |
| 04-qa-plan-interpret-endpoint | ⏳ Pendente | - | - |
| 05P-fast-spec | ⏳ Pendente | - | - |

## Estratégia de Implementação Recomendada

### Fase 1: Base (Sequencial)
1. Implementar `01-cli-shared-ui.md`
2. Validar componentes com testes unitários

### Fase 2: Features (Paralelo)
Três times trabalhando simultaneamente:
- **Time 1**: `02P-catalog-ai-enrichment.md`
- **Time 2**: `03P-cli-chat.md`
- **Time 3**: `05P-fast-spec.md` (se disponível)

### Fase 3: QA (Sequencial)
1. Aguardar conclusão do enriquecimento semântico (`02P`)
2. Executar `04-qa-plan-interpret-endpoint.md`
3. Validar todos os 78 cenários de teste

## Tempo Estimado Total

| Fase | Duração (sequencial) | Duração (paralelo) |
|------|---------------------|-------------------|
| Fase 1: Base | 4-7h | 4-7h |
| Fase 2: Features | 35-40h | 21-26h |
| Fase 3: QA | 8-12h | 8-12h |
| **Total** | **47-59h** | **33-45h** |

> Com 3 desenvolvedores trabalhando em paralelo: **~2 semanas** (considerando 8h/dia)

---

**Última Atualização**: 2026-02-04
