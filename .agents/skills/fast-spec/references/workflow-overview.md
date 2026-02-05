# Fast-Spec Workflow Overview

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│            /fast-spec <feature description>                      │
│                      (Orchestrator)                              │
│                                                                  │
│  Responsibilities:                                               │
│  - Parse feature description from $ARGUMENTS                     │
│  - Launch each step as subtask via Task tool                     │
│  - Delegate to /speckit.* commands (not replicate behavior)      │
│  - Collect summary data from subtask results                     │
│  - Present final consolidated summary                            │
└─────────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────────────┐
    │                         │                                  │
    ▼                         ▼                                  ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│    SUBTASK    │       │    SUBTASK    │       │    SUBTASK    │
│ /speckit.     │result │ /speckit.     │result │ /speckit.     │ ...
│   specify     │──────▶│   clarify     │──────▶│    plan       │
│(clean context)│       │(clean context)│       │(clean context)│
└───────────────┘       └───────────────┘       └───────────────┘
```

## Execution Flow

```
User: /fast-spec Add user authentication with OAuth2

┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (fast-spec skill)                                   │
│ - Runs in main context (not a subtask)                          │
│ - Launches each step as subtask via Task tool                   │
│ - Delegates to /speckit.* commands                              │
│ - Collects minimal summary data between steps                   │
│ - Waits for each subtask to complete before next                │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 1. Task(prompt="/speckit.specify <description>")
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ /speckit.specify (subtask) - Clean Context                      │
│ - Creates branch + spec.md                                       │
│ - Runs quality validation checklist                              │
│ - Handles initial clarifications (max 3)                         │
│ - Returns: branch_name, spec_path                                │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 2. Task(prompt="/speckit.clarify")
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ /speckit.clarify (subtask) - Clean Context                      │
│ - Loads spec fresh from disk                                     │
│ - Scans for ambiguities (taxonomy-based)                        │
│ - Asks up to 5 sequential questions (may pause for user)        │
│ - Updates spec with clarifications                               │
│ - Returns: clarification_count, coverage_status                  │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 3. Task(prompt="/speckit.plan")
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ /speckit.plan (subtask) - Clean Context                         │
│ - Loads spec.md and constitution.md fresh from disk             │
│ - Runs Constitution Check                                        │
│ - Generates research.md, data-model.md, contracts/, plan.md     │
│ - Updates agent context (AGENTS.md)                              │
│ - Returns: artifacts_created[], plan_path                        │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 4. Task(prompt="/speckit.tasks")
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ /speckit.tasks (subtask) - Clean Context                        │
│ - Loads plan.md, spec.md fresh from disk                        │
│ - Maps user stories to tasks                                     │
│ - Generates tasks.md with dependency ordering                    │
│ - Returns: tasks_count, phase_count, tasks_path                  │
└─────────────────────────────────────────────────────────────────┘
        │
        │ 5. Task(prompt="/speckit.analyze")
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ /speckit.analyze (subtask) - Clean Context                      │
│ - Loads all artifacts fresh from disk (READ-ONLY)               │
│ - Validates consistency across spec/plan/tasks                   │
│ - Checks constitution alignment                                  │
│ - Returns: coverage_percent, issues_by_severity, critical_list   │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ SUMMARY (orchestrator context)                                   │
│ - Consolidates results from all subtasks                        │
│ - Lists all generated artifacts                                  │
│ - Shows analysis metrics and issues                              │
│ - Recommends next steps based on critical issues                │
└─────────────────────────────────────────────────────────────────┘
```

## Subtask Execution Pattern

Each step uses the Task tool to launch a clean-context subtask:

```
Task(
  description="[N/5] speckit.{command}",
  prompt="/speckit.{command} {arguments}",
  subagent_type="general"
)
```

**Key points**:
- `subagent_type="general"` ensures full capability
- Each subtask reads artifacts fresh from disk
- Subtask results contain only summary data (not full artifacts)
- Orchestrator waits for completion before next step

## Step Returns

| Step | Command | Returns |
|------|---------|---------|
| 1 | `/speckit.specify` | `branch_name`, `spec_path` |
| 2 | `/speckit.clarify` | `clarification_count`, `coverage_status` |
| 3 | `/speckit.plan` | `artifacts[]`, `plan_path` |
| 4 | `/speckit.tasks` | `tasks_count`, `phase_count`, `tasks_path` |
| 5 | `/speckit.analyze` | `coverage_percent`, `issues_by_severity`, `critical_list` |

## Context Isolation

### Why Clean Context Matters

```
WITHOUT subtasks (bad):
┌────────────────────────────────────────────────────────┐
│ Single Context                                          │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ specify  │+│ clarify  │+│   plan   │+│  tasks   │   │
│ │ output   │ │ output   │ │ output   │ │ output   │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│         CONTEXT GROWS → TOKEN OVERFLOW                 │
└────────────────────────────────────────────────────────┘

WITH subtasks (good):
┌─────────────────────────────────────────────────────────┐
│ Orchestrator (minimal context)                          │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│ │ branch  │  │ count   │  │ paths   │  │ metrics │    │
│ │ path    │  │ status  │  │ list    │  │ issues  │    │
│ └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
│     ▲            ▲            ▲            ▲           │
└─────┼────────────┼────────────┼────────────┼───────────┘
      │            │            │            │
┌─────┴────┐ ┌─────┴────┐ ┌─────┴────┐ ┌─────┴────┐
│ SUBTASK  │ │ SUBTASK  │ │ SUBTASK  │ │ SUBTASK  │
│ specify  │ │ clarify  │ │  plan    │ │  tasks   │
│(isolated)│ │(isolated)│ │(isolated)│ │(isolated)│
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Benefits

1. **Prevents token bloat**: Each subtask has fresh context
2. **Avoids stale state**: Subtasks read from disk, not memory
3. **Matches standalone**: `/speckit.plan` behaves same in pipeline or alone
4. **Isolates failures**: One step failing doesn't corrupt others

## Troubleshooting

### Step Fails to Start

1. Check if `/speckit.*` command exists in `.opencode/command/`
2. Verify `.specify/` directory structure
3. Ensure Git repository is initialized
4. Check that previous step completed successfully

### Subtask Returns Error

1. Review error message from subtask result
2. Run the failed `/speckit.*` command standalone to debug
3. Check prerequisites (spec.md exists for clarify, plan.md exists for tasks)
4. Verify constitution.md is valid if plan fails

### Context Issues

1. Ensure using Task tool (not direct invocation) for each step
2. Verify subtask results contain only summary data
3. Restart session if context seems corrupted
4. Run steps individually via `/speckit.*` commands

### Analyze Reports Critical Issues

1. Review CRITICAL issues first (blocks implementation)
2. Fix in appropriate artifact (spec.md, plan.md, or tasks.md)
3. Re-run `/speckit.analyze` standalone to verify fixes
4. Only proceed to `/speckit.implement` when no CRITICAL issues

## Manual Step Execution

For debugging or iterative refinement, run speckit commands directly:

```
/speckit.specify <description>   # Step 1: Create spec
/speckit.clarify                 # Step 2: Resolve ambiguities
/speckit.plan                    # Step 3: Generate design
/speckit.tasks                   # Step 4: Create task list
/speckit.analyze                 # Step 5: Validate consistency
```

**Note**: Running manually loses context isolation benefits but allows fine-grained control.

## Comparison: Fast-Spec vs Manual

| Aspect | Manual (`/speckit.*`) | `/fast-spec` |
|--------|----------------------|--------------|
| Context | Single (accumulates) | Clean per step (subtasks) |
| Commands | Direct invocation | Delegates to same commands |
| User pauses | At each command | Within subtasks (clarify) |
| Error isolation | Shared context | Isolated per subtask |
| Progress tracking | Manual | Automatic [N/5] indicators |
| Final summary | None | Consolidated report |
| When to use | Debugging, iteration | Full pipeline, new features |

## Related Files

- **Skill definition**: `.agents/skills/fast-spec/SKILL.md`
- **Speckit commands**: `.opencode/command/speckit.*.md`
- **Templates**: `.specify/templates/`
- **Scripts**: `.specify/scripts/bash/`
