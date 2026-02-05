# Plan: Skill `fast-spec`

## Overview

Skill que executa o fluxo completo de especificação (`specify → clarify → plan → tasks → analyze`) de forma contínua e otimizada, utilizando **subagents** do OpenCode para limpar contexto entre etapas.

Inspirada no conceito "ralphy" de execução autônoma em loop.

## Problem Statement

Executar manualmente a sequência `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` é tedioso e acumula contexto desnecessário na sessão, degradando a qualidade das respostas.

## Solution: Orchestrator + Subagents

A chave para "limpar contexto entre etapas" é usar **subagents** no OpenCode. Cada subagent:

1. Roda em uma sessão separada
2. Tem seu próprio contexto limpo
3. Retorna apenas o resultado final

A opção `subtask: true` força o comando a rodar como subagent, evitando poluição do contexto principal.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│            /fast-spec <feature description>                      │
│                      (Orchestrator)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────────────┐
    │                         │                                  │
    ▼                         ▼                                  ▼
┌─────────┐  result     ┌─────────┐  result     ┌─────────┐  ...
│ SPECIFY │ ─────────▶  │ CLARIFY │ ─────────▶  │  PLAN   │
│(subtask)│             │(subtask)│             │(subtask)│
└─────────┘             └─────────┘             └─────────┘
  Clean                   Clean                   Clean
  Context                 Context                 Context
```

## Execution Flow

```
User: /fast-spec Add user authentication with OAuth2

┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (fast-spec.md)                                      │
│ - NOT a subtask (maintains context for orchestration)            │
│ - Invokes each step as subtask                                   │
│ - Collects results between steps                                 │
│ - Single pause for clarifications (batch)                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 1. Invoke @fast-spec.specify with feature description
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ SPECIFY (subtask: true) - Clean Context                         │
│ - Creates branch + spec.md                                       │
│ - Collects [NEEDS CLARIFICATION] markers                        │
│ - Returns: branch_name, spec_path, clarifications[]             │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 2. If clarifications[] not empty:
        │    PAUSE - Present batch questions to user
        │    (Only interruption in the flow)
        │
        │ 3. Invoke @fast-spec.clarify with answers
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLARIFY (subtask: true) - Clean Context                         │
│ - Applies answers to spec.md                                     │
│ - Returns: spec_updated, remaining_issues                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 4. Invoke @fast-spec.plan
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ PLAN (subtask: true) - Clean Context                            │
│ - Generates research.md, data-model.md, contracts/, plan.md     │
│ - Returns: artifacts_created[], plan_path                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 5. Invoke @fast-spec.tasks
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ TASKS (subtask: true) - Clean Context                           │
│ - Generates tasks.md with dependency ordering                    │
│ - Returns: tasks_count, tasks_path                               │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 6. Invoke @fast-spec.analyze
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ ANALYZE (subtask: true) - Clean Context                         │
│ - Validates consistency (READ-ONLY)                              │
│ - Returns: analysis_report, issues_by_severity                   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ SUMMARY (orchestrator)                                           │
│ - Presents consolidated summary                                  │
│ - Links to all artifacts                                         │
│ - Issues found by analyze                                        │
│ - Suggested next steps                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Files to Create

### Skill Structure

```
.agents/skills/fast-spec/
├── SKILL.md                           # Main skill file
└── references/
    └── workflow-overview.md           # Flow overview for troubleshooting
```

### Commands

```
.opencode/command/
├── fast-spec.md              # Main orchestrator
├── fast-spec.specify.md      # Step 1: subtask
├── fast-spec.clarify.md      # Step 2: subtask (batch clarifications)
├── fast-spec.plan.md         # Step 3: subtask
├── fast-spec.tasks.md        # Step 4: subtask
└── fast-spec.analyze.md      # Step 5: subtask
```

## Command Specifications

### Orchestrator (fast-spec.md)

```yaml
---
description: Run full specification pipeline (specify → clarify → plan → tasks → analyze) with context clearing between steps
agent: build
---
```

**Responsibilities:**
- Parse feature description from $ARGUMENTS
- Invoke each step as subtask using @mention
- Handle clarification batch (single pause)
- Collect and present final summary

### Step Commands (subtask: true)

Each step command:
- Has `subtask: true` in frontmatter
- Delegates to corresponding `/speckit.*` command
- Returns structured result for orchestrator

| Command | Delegates to | Returns |
|---------|--------------|---------|
| `fast-spec.specify` | `/speckit.specify` | branch, spec_path, clarifications |
| `fast-spec.clarify` | `/speckit.clarify` | spec_updated, remaining_issues |
| `fast-spec.plan` | `/speckit.plan` | artifacts[], plan_path |
| `fast-spec.tasks` | `/speckit.tasks` | tasks_count, tasks_path |
| `fast-spec.analyze` | `/speckit.analyze` | report, issues_by_severity |

## UX Characteristics

| Aspect | Implementation |
|--------|---------------|
| **Simple trigger** | `/fast-spec <feature description>` |
| **Visual progress** | Phase indicators (1/5, 2/5...) |
| **Batch clarifications** | Single pause for all questions |
| **Concise output** | Final summary with links and metrics |
| **Fail-fast** | Stops on critical errors with clear message |

## Advantages

| Aspect | Benefit |
|--------|---------|
| **Clean context** | Each step runs in separate subtask |
| **Isolated failure** | If one step fails, doesn't corrupt others |
| **Easy debugging** | Can run steps individually |
| **Simple UX** | Single command: `/fast-spec <feature>` |
| **Batch clarifications** | Single pause for all questions |
| **Reuse** | Reuses existing speckit commands |

## Comparison with Original Ralphy

| Aspect | Ralphy (bash) | fast-spec (OpenCode) |
|--------|---------------|----------------------|
| Execution | External bash loop | Native subagents |
| Context | New instance per loop | Subtask clears context |
| State | PRD/progress files | Orchestrator maintains state |
| Parallelism | Git worktrees | Sequential (by design) |
| Clarifications | N/A | Single batch |

## Implementation Steps

1. **Create directory structure**
2. **Implement SKILL.md** with frontmatter and description
3. **Implement orchestrator command** (fast-spec.md)
4. **Implement step commands** (5 subtask commands)
5. **Test each step** individually
6. **Test complete flow**
7. **Package skill** (if needed)

## Success Criteria

- [ ] `/fast-spec <description>` triggers full pipeline
- [ ] Each step runs with clean context (subtask)
- [ ] Clarifications presented in single batch
- [ ] Final summary shows all artifacts and issues
- [ ] Errors in one step don't corrupt others
- [ ] Can be invoked from any OpenCode session

## References

- [OpenCode Agents Documentation](https://opencode.ai/docs/agents/)
- [OpenCode Commands Documentation](https://opencode.ai/docs/commands/)
- [Ralphy GitHub Repository](https://github.com/michaelshimeles/ralphy)
- Existing speckit commands in `.opencode/command/speckit.*.md`
