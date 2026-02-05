# Fast-Spec Workflow Overview

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│            /fast-spec <feature description>                      │
│                      (Orchestrator)                              │
│                                                                  │
│  Responsibilities:                                               │
│  - Parse feature description from $ARGUMENTS                     │
│  - Invoke each step as subtask                                   │
│  - Handle clarification batch (single pause)                     │
│  - Collect and present final summary                             │
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
        │ 1. Invoke /fast-spec.specify with feature description
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
        │ 3. Invoke /fast-spec.clarify with answers
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLARIFY (subtask: true) - Clean Context                         │
│ - Applies answers to spec.md                                     │
│ - Returns: spec_updated, remaining_issues                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 4. Invoke /fast-spec.plan
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ PLAN (subtask: true) - Clean Context                            │
│ - Generates research.md, data-model.md, contracts/, plan.md     │
│ - Returns: artifacts_created[], plan_path                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 5. Invoke /fast-spec.tasks
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ TASKS (subtask: true) - Clean Context                           │
│ - Generates tasks.md with dependency ordering                    │
│ - Returns: tasks_count, tasks_path                               │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 6. Invoke /fast-spec.analyze
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

## Step Returns

| Step | Returns |
|------|---------|
| SPECIFY | `branch_name`, `spec_path`, `clarifications[]` |
| CLARIFY | `spec_updated`, `remaining_issues` |
| PLAN | `artifacts[]`, `plan_path` |
| TASKS | `tasks_count`, `tasks_path` |
| ANALYZE | `analysis_report`, `issues_by_severity` |

## Troubleshooting

### Step Fails to Start

1. Check if required speckit command exists
2. Verify `.specify/` directory structure
3. Ensure Git repository is initialized

### Clarifications Not Collected

1. Check spec.md for `[NEEDS CLARIFICATION]` markers
2. Verify SPECIFY step completed successfully
3. Check for formatting issues in markers

### Context Pollution

1. Ensure subtask commands have `subtask: true` in frontmatter
2. Restart OpenCode session if issues persist
3. Run steps individually to isolate problem

### Analyze Reports Issues

1. Review CRITICAL issues first
2. Fix spec/plan/tasks as recommended
3. Re-run `/fast-spec.analyze` to verify fixes

## Manual Step Execution

For debugging, run steps individually:

```
/fast-spec.specify <description>   # Step 1
/fast-spec.clarify                 # Step 2 (after answering questions)
/fast-spec.plan                    # Step 3
/fast-spec.tasks                   # Step 4
/fast-spec.analyze                 # Step 5
```

## Comparison with Manual Execution

| Aspect | Manual (`/speckit.*`) | Fast-Spec |
|--------|----------------------|-----------|
| Context | Accumulates | Clean per step |
| User interruptions | Multiple | Single (clarify) |
| Error isolation | Shared | Isolated |
| Progress tracking | Manual | Automatic |
| Final summary | None | Consolidated |
