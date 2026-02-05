---
description: Run full specification pipeline (specify -> clarify -> plan -> tasks -> analyze) with context clearing between steps
---

## User Input

```text
$ARGUMENTS
```

## Overview

You are the **fast-spec orchestrator**. Your job is to execute the complete feature specification pipeline, invoking each step as a subtask with clean context.

**CRITICAL**: This command orchestrates the flow. Each step runs as a subtask to ensure clean context isolation.

## Execution Flow

### Step 1: Validate Input

```text
IF $ARGUMENTS is empty or "$ARGUMENTS":
  ERROR "No feature description provided. Usage: /fast-spec <feature description>"
  STOP
```

### Step 2: Execute SPECIFY (Subtask)

Display progress indicator:

```
[1/5] SPECIFY - Creating feature branch and initial specification...
```

Invoke the specify subtask by running `/fast-spec.specify $ARGUMENTS`.

Wait for completion and capture:
- `branch_name`: The created branch name
- `spec_path`: Path to spec.md
- `clarifications[]`: List of [NEEDS CLARIFICATION] questions (if any)

If SPECIFY fails, report error and STOP.

### Step 3: Handle Clarifications (Single Pause)

```text
IF clarifications[] is not empty:
  Display: "[PAUSE] Clarification needed before continuing..."
  
  Present ALL clarification questions in batch format:
  
  ## Clarifications Needed
  
  The specification has questions that need your input before proceeding:
  
  [For each clarification, present as numbered question with options]
  
  **Please answer all questions** (e.g., "Q1: A, Q2: B, Q3: custom answer")
  
  WAIT for user response
  
  Store answers as: clarification_answers
ELSE:
  Display: "No clarifications needed, proceeding..."
  clarification_answers = null
```

### Step 4: Execute CLARIFY (Subtask)

```text
IF clarification_answers is not null:
  Display: "[2/5] CLARIFY - Applying clarifications to specification..."
  
  Invoke /fast-spec.clarify with the user's answers
  
  Wait for completion and capture:
  - spec_updated: boolean
  - remaining_issues: any unresolved items
  
  IF CLARIFY fails, report error and STOP
ELSE:
  Display: "[2/5] CLARIFY - Skipped (no clarifications needed)"
```

### Step 5: Execute PLAN (Subtask)

Display progress indicator:

```
[3/5] PLAN - Generating technical design artifacts...
```

Invoke `/fast-spec.plan`.

Wait for completion and capture:
- `artifacts[]`: List of created files (research.md, data-model.md, contracts/, plan.md)
- `plan_path`: Path to plan.md

If PLAN fails, report error and STOP.

### Step 6: Execute TASKS (Subtask)

Display progress indicator:

```
[4/5] TASKS - Generating actionable task list...
```

Invoke `/fast-spec.tasks`.

Wait for completion and capture:
- `tasks_count`: Number of tasks generated
- `tasks_path`: Path to tasks.md

If TASKS fails, report error and STOP.

### Step 7: Execute ANALYZE (Subtask)

Display progress indicator:

```
[5/5] ANALYZE - Validating cross-artifact consistency...
```

Invoke `/fast-spec.analyze`.

Wait for completion and capture:
- `analysis_report`: Summary of findings
- `issues_by_severity`: Categorized issues (CRITICAL, HIGH, MEDIUM, LOW)

If ANALYZE fails, report warning (non-blocking) and continue to summary.

### Step 8: Present Final Summary

```markdown
## Fast-Spec Complete

### Feature
**Branch**: {branch_name}
**Description**: {$ARGUMENTS}

### Artifacts Created

| Artifact | Path | Status |
|----------|------|--------|
| Specification | {spec_path} | Created |
| Plan | {plan_path} | Created |
| Tasks | {tasks_path} | {tasks_count} tasks |
| Research | {feature_dir}/research.md | Created (if applicable) |
| Data Model | {feature_dir}/data-model.md | Created (if applicable) |
| Contracts | {feature_dir}/contracts/ | Created (if applicable) |

### Analysis Summary

**Issues Found**:
- CRITICAL: {count}
- HIGH: {count}
- MEDIUM: {count}
- LOW: {count}

{If CRITICAL > 0}:
**Action Required**: Address CRITICAL issues before proceeding to implementation.

### Suggested Next Steps

1. {If CRITICAL issues}: Run `/speckit.clarify` or manually fix issues, then `/fast-spec.analyze`
2. {If no CRITICAL}: Ready for implementation with `/speckit.implement`
3. Review tasks at: {tasks_path}
4. Start with Phase 1 tasks (Setup)
```

## Error Handling

- **SPECIFY fails**: "Failed to create specification. Check feature description and try again."
- **CLARIFY fails**: "Failed to apply clarifications. Run `/speckit.clarify` manually."
- **PLAN fails**: "Failed to generate plan. Run `/speckit.plan` manually."
- **TASKS fails**: "Failed to generate tasks. Run `/speckit.tasks` manually."
- **ANALYZE fails**: "Analysis incomplete. Run `/speckit.analyze` manually after reviewing artifacts."

## Behavior Rules

1. **Progress Visibility**: Always show current step indicator [N/5]
2. **Single Pause**: Only interrupt user flow for clarifications (after SPECIFY)
3. **Clean Context**: Each step invoked as subtask for isolation
4. **Fail-Fast**: Stop on critical errors, report clearly
5. **Summary Always**: Even on partial completion, show what was created
6. **No Duplication**: Do not re-run successful steps
