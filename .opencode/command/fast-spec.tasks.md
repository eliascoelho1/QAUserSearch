---
description: Generate actionable task list with dependencies (Step 4 of fast-spec pipeline)
subtask: true
---

## User Input

```text
$ARGUMENTS
```

## Overview

You are executing **Step 4 (TASKS)** of the fast-spec pipeline as a subtask with clean context.

Your job is to delegate to `/speckit.tasks` and return structured results for the orchestrator.

## Execution

### 1. Initialize Context

Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root.

Parse JSON for:
- `FEATURE_DIR`
- `AVAILABLE_DOCS` list

If parsing fails, RETURN ERROR with instruction to verify feature branch.

### 2. Execute speckit.tasks

Run the full `/speckit.tasks` workflow:

1. Load design documents from FEATURE_DIR:
   - **Required**: plan.md, spec.md
   - **Optional**: data-model.md, contracts/, research.md, quickstart.md

2. Execute task generation:
   - Extract tech stack and libraries from plan.md
   - Extract user stories with priorities from spec.md
   - Map entities from data-model.md (if exists)
   - Map endpoints from contracts/ (if exists)
   - Extract decisions from research.md (if exists)

3. Generate tasks.md:
   - Phase 1: Setup tasks
   - Phase 2: Foundational tasks
   - Phase 3+: User story phases (in priority order)
   - Final Phase: Polish & cross-cutting concerns

4. Validate tasks:
   - All tasks follow checklist format
   - Dependencies are clear
   - Each user story is independently testable

### 3. Collect Task Metrics

After generation, collect:
- Total task count
- Tasks per phase
- Tasks per user story
- Parallel opportunities
- MVP scope suggestion

### 4. Return Results to Orchestrator

```markdown
## TASKS Results

**Status**: SUCCESS | ERROR

### Tasks File
- **Path**: {tasks_path}

### Task Summary

| Metric | Value |
|--------|-------|
| Total Tasks | {count} |
| Setup Phase | {count} tasks |
| Foundational Phase | {count} tasks |
| User Story Phases | {count} phases |
| Polish Phase | {count} tasks |
| Parallel Opportunities | {count} |

### Phase Breakdown

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | {count} |
| Phase 2 | Foundational | {count} |
| Phase 3 | {US1 name} | {count} |
| Phase 4 | {US2 name} | {count} |
| ... | ... | ... |
| Final | Polish | {count} |

### User Story Coverage

| Story | Priority | Tasks | Independent |
|-------|----------|-------|-------------|
| US1 | P1 | {count} | Yes/No |
| US2 | P2 | {count} | Yes/No |
| ... | ... | ... | ... |

### MVP Recommendation
- **Suggested MVP**: {Phase 1 + Phase 2 + Phase 3 (US1)}
- **Tasks for MVP**: {count}

### Validation
- **Format Compliance**: {pass | fail}
- **Dependencies Clear**: {yes | issues}
- **Independent Stories**: {yes | issues}

### Errors (if any)

{List any warnings or issues encountered}
```

## Error Handling

If any step fails:

```markdown
## TASKS Results

**Status**: ERROR

### Error Details
- **Step**: {which step failed}
- **Message**: {error message}
- **Missing Documents**: {list if applicable}
- **Suggestion**: {how to fix}

### Partial Results

{If tasks.md was partially created, note what's included}
```

## Behavior Rules

1. **Full Delegation**: Execute complete `/speckit.tasks` workflow
2. **Document Flexibility**: Work with available documents (not all may exist)
3. **Format Strict**: Ensure all tasks follow the checklist format
4. **Story Independence**: Prioritize independent user story phases
5. **MVP Focus**: Clearly identify MVP scope
6. **Metrics Capture**: Collect all metrics for summary
