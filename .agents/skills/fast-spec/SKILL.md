---
name: fast-spec
description: "Run full specification pipeline (specify -> clarify -> plan -> tasks -> analyze) with context clearing between steps. Use when: need complete feature spec, fast specification, quick spec, full pipeline, specify and plan, end-to-end spec."
source: QAUserSearch (proprietary)
---

# Fast Spec - Full Specification Pipeline

**Role**: Specification Pipeline Orchestrator

You orchestrate the complete feature specification workflow, delegating each step to specialized subtasks that run with clean context. This ensures high-quality outputs without context pollution between phases.

## Capabilities

- Execute full spec pipeline in one command
- Clean context isolation between steps (subtasks)
- Batch clarification questions (single user interruption)
- Progress tracking with phase indicators
- Final consolidated summary with all artifacts
- Fail-fast on critical errors

## Requirements

- Existing speckit commands (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`)
- `.specify/` directory structure with templates and scripts
- Git repository for branch management

## Workflow Overview

```
/fast-spec <feature description>
     |
     v
[1/5] SPECIFY (subtask) --> Creates branch + spec.md
     |
     v
[PAUSE] Batch clarifications (if any)
     |
     v
[2/5] CLARIFY (subtask) --> Applies answers to spec.md
     |
     v
[3/5] PLAN (subtask) --> Generates research.md, data-model.md, contracts/, plan.md
     |
     v
[4/5] TASKS (subtask) --> Generates tasks.md with dependency ordering
     |
     v
[5/5] ANALYZE (subtask) --> Validates consistency (READ-ONLY)
     |
     v
[SUMMARY] Consolidated report with all artifacts and issues
```

## Usage

### Basic Usage

```
/fast-spec Add user authentication with OAuth2
```

### With Context

```
/fast-spec Create a dashboard for analytics that shows user metrics and trends
```

## Patterns

### Full Pipeline Execution

The orchestrator invokes each step as a subtask:

1. **SPECIFY**: Creates feature branch and initial spec
2. **CLARIFY**: Resolves ambiguities (single batch pause for user)
3. **PLAN**: Generates technical design artifacts
4. **TASKS**: Creates actionable task list
5. **ANALYZE**: Validates cross-artifact consistency

### Clarification Handling

- Clarifications are collected during SPECIFY
- Presented as batch questions (single interruption)
- User answers all at once
- CLARIFY applies answers to spec

### Error Handling

- Each step runs in isolation (subtask)
- Failures in one step don't corrupt others
- Clear error messages with suggested fixes
- Can resume from specific step if needed

## Anti-Patterns

### Running Steps Manually

**Why bad**: Context pollution between steps, higher error risk, tedious process

**Instead**: Use `/fast-spec` for full pipeline, or individual `/speckit.*` commands only for debugging

### Skipping Clarify

**Why bad**: Downstream rework, ambiguous specs

**Instead**: Always complete clarify step unless explicitly doing exploratory spike

### Ignoring Analyze Issues

**Why bad**: Inconsistent artifacts, implementation problems

**Instead**: Address CRITICAL issues before proceeding to implementation

## Related Commands

- `/fast-spec.specify` - Step 1: Create spec (subtask)
- `/fast-spec.clarify` - Step 2: Apply clarifications (subtask)
- `/fast-spec.plan` - Step 3: Generate plan (subtask)
- `/fast-spec.tasks` - Step 4: Generate tasks (subtask)
- `/fast-spec.analyze` - Step 5: Validate consistency (subtask)

## References

- [Workflow Overview](references/workflow-overview.md) - Detailed flow diagram and troubleshooting
- [OpenCode Agents Documentation](https://opencode.ai/docs/agents/)
- [OpenCode Commands Documentation](https://opencode.ai/docs/commands/)
