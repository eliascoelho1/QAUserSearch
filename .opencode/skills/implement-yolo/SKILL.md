---
name: implement-yolo
description: "Execute automated implementation of Speckit specifications in yolo mode. Implements tasks until each checkpoint, commits automatically, and loops until all tasks complete. Use when: need yolo implementation, auto implement spec, autonomous spec implementation, implement all tasks automatically, yolo mode, implement loop, continuous implementation."
---

# Implement Yolo - Autonomous Specification Implementation

**Role**: Implementation Loop Orchestrator

Orchestrate the complete implementation of a Speckit specification by executing `/speckit.implement` in automated cycles, committing at each checkpoint, and looping until all tasks are complete.

## Capabilities

- Execute implementation in autonomous loop (yolo mode)
- Detect checkpoints in tasks.md by `**Checkpoint**` marker
- Auto-commit at each checkpoint with descriptive message
- Retry lint/type-check/test errors up to 3 times
- Progress tracking with iteration and task counts
- Clean context isolation between iterations

## Requirements

- Plugin `@openspoon/subtask2` installed for loop orchestration
- `tasks.md` must exist with checkpoints defined
- Active feature branch (numbered branch from Speckit)
- `/speckit.implement` command available

## Workflow Overview

```
/implement-yolo
     │
     ├──► [INIT] Validate prerequisites
     │
     ├──► [SCAN] Parse tasks.md
     │         - Count pending tasks (- [ ])
     │         - Identify next checkpoint
     │         - Determine current phase
     │
     └──► [LOOP] while has_pending_tasks:
               │
               ├──► SUBTASK: /speckit.implement
               │    (implement until next checkpoint)
               │
               ├──► [VERIFY] Check result
               │    - lint/type/test error → retry (max 3x)
               │    - other error → STOP
               │    - success → continue
               │
               ├──► [COMMIT] Auto-commit checkpoint
               │
               └──► [NEXT] Re-scan and continue
```

## Execution Steps

### Step 0: Prerequisites Check

Run the prerequisites script to get FEATURE_DIR:

```bash
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

Parse the JSON output for `FEATURE_DIR` and verify:
- tasks.md exists
- At least one task is pending (- [ ])
- Currently on a feature branch

**On failure**: Stop and report missing prerequisites.

### Step 1: Parse tasks.md

Read `{FEATURE_DIR}/tasks.md` and extract:

1. **Total tasks**: Count all lines matching `- [ ]` or `- [x]` or `- [X]`
2. **Pending tasks**: Count lines matching `- [ ]`
3. **Completed tasks**: Count lines matching `- [x]` or `- [X]`
4. **Next checkpoint**: Find first `**Checkpoint**` line after any pending task
5. **Current phase**: Extract phase name from nearest `## Phase` header

**Checkpoint format in tasks.md**:
```markdown
**Checkpoint**: Description of what should be achieved ✅
```

### Step 2: Execute Implementation Loop

For each iteration while pending tasks exist:

#### 2.1 Launch Implementation Subtask

Use the Task tool to launch `/speckit.implement` with specific instructions:

```
Task(
  description="[Iteration N] speckit.implement until checkpoint",
  prompt="/speckit.implement Implement all tasks until the next checkpoint: '{checkpoint_description}'. Mark each completed task as [x] in tasks.md. STOP when you reach the checkpoint. Do NOT proceed past the checkpoint.",
  subagent_type="general"
)
```

**CRITICAL**: Each iteration runs as an independent subtask for clean context isolation.

#### 2.2 Verify Result

After subtask completes, check for errors:

**Recoverable errors** (retry up to 3 times):
- Lint errors: output contains "ruff" or "lint" failures
- Type errors: output contains "mypy" or "type" failures
- Test errors: output contains "pytest" or "test" failures

**Retry action**:
```
Task(
  description="[Iteration N] Retry - fix errors",
  prompt="/speckit.implement Fix the lint/type/test errors reported and continue implementation. Current retry: {retry_count}/3",
  subagent_type="general"
)
```

**Non-recoverable errors** (stop immediately):
- tasks.md not found or corrupted
- Branch protection errors
- 3 retries exhausted without success
- Unexpected errors

#### 2.3 Verify Checkpoint Reached

Re-read tasks.md and verify:
- All tasks before the target checkpoint are marked `[x]`
- If not all marked, the subtask may have stopped prematurely - retry

#### 2.4 Create Commit

Use the git-commit skill or create commit directly:

**Commit message format**:
```
feat({phase-slug}): {checkpoint_description}

Tasks completed in this checkpoint:
- {task_id} {task_description}
- {task_id} {task_description}
...

Checkpoint: {checkpoint_text}
```

**Example**:
```
feat(foundational): Foundation ready - user story implementation can begin

Tasks completed in this checkpoint:
- T006 Create enum EnrichmentStatus
- T007 Create schemas ColumnMetadataYaml and SourceMetadataYaml
- T010 Implement AsyncTTLCache with dual-lock pattern
- T015 Create tests for AsyncTTLCache

Checkpoint: Foundation ready - user story implementation can begin
```

#### 2.5 Report Progress

After each successful checkpoint:

```markdown
### Iteration {N} Complete

**Phase**: {current_phase}
**Checkpoint**: {checkpoint_description}
**Tasks Implemented**: {count}
**Commit**: {commit_hash_short}

Pending tasks remaining: {pending_count}
```

#### 2.6 Next Iteration

- Re-scan tasks.md for updated state
- Find next checkpoint (if any)
- Continue loop if pending tasks exist

### Step 3: Final Summary

When all tasks are complete (no more `- [ ]` in tasks.md):

```markdown
## Implement Yolo - COMPLETE

**Spec**: {feature_name}
**Total Iterations**: {iteration_count}
**Total Tasks Implemented**: {task_count}
**Commits Created**: {commit_count}

### Checkpoints Completed

1. ✅ {checkpoint_1_description}
2. ✅ {checkpoint_2_description}
...

### Next Steps

✅ All tasks implemented. Ready for:
- Code review
- PR creation with `/pr-creator`
```

## Error Handling Patterns

### Retry Pattern for Recoverable Errors

```
retry_count = 0
max_retries = 3

while retry_count < max_retries:
    result = run_speckit_implement()
    
    if is_lint_type_test_error(result):
        retry_count += 1
        log(f"Retry {retry_count}/{max_retries}: Fixing errors...")
        continue
    elif is_success(result):
        break
    else:
        # Non-recoverable error
        stop_and_report(result)
        return

if retry_count >= max_retries:
    stop_and_report("Max retries exhausted")
```

### Error Detection Heuristics

**Lint errors** - Look for:
- "ruff check" in output
- "linting" or "lint error" messages
- Exit code from ruff

**Type errors** - Look for:
- "mypy" in output
- "type error" or "type:" messages
- Missing type annotations

**Test errors** - Look for:
- "pytest" in output
- "FAILED" test markers
- "AssertionError" messages

## Usage Examples

### Basic Usage

```
/implement-yolo
```

Runs the full implementation loop from current state.

### With Status Check First

```
User: Show me the current implementation status
AI: [Scans tasks.md and reports pending tasks, current phase, next checkpoint]

User: /implement-yolo
AI: [Begins automated implementation loop]
```

## Anti-Patterns

### Running Without Subtask Isolation

**Why bad**: Context accumulates, causing token overflow and stale state

**Instead**: ALWAYS use Task tool for each `/speckit.implement` invocation

### Skipping Verification

**Why bad**: May commit incomplete checkpoints

**Instead**: Always verify all tasks before checkpoint are marked [x]

### Ignoring Retries

**Why bad**: Transient errors cause unnecessary failures

**Instead**: Retry lint/type/test errors up to 3 times

### Continuing Past Non-Recoverable Errors

**Why bad**: May corrupt state or create inconsistent code

**Instead**: Stop immediately on unexpected errors, report clearly

## Checkpoint Detection Reference

### Identifying Checkpoints in tasks.md

Checkpoints are marked with this pattern:
```markdown
**Checkpoint**: {description} [optional ✅]
```

**Examples from real tasks.md**:
```markdown
**Checkpoint**: Foundation ready - user story implementation can now begin ✅
**Checkpoint US1**: API de consulta funciona sem PostgreSQL
**Checkpoint Final**: Quality validated, ready for merge
```

### Determining Tasks Before a Checkpoint

1. Find the checkpoint line number
2. Scan backwards for all tasks (`- [ ]` or `- [x]`) until:
   - Previous checkpoint, OR
   - Phase header (`## Phase`), OR
   - Start of file

3. These are the tasks that must be `[x]` for checkpoint to be complete

## Related Commands

- `/speckit.implement` - The command being orchestrated
- `/speckit.tasks` - Regenerate task list if needed
- `/fast-spec` - Full specification pipeline
- `/git-commit` - Manual commit creation

## Configuration

### Subtask2 Integration (if using plugin)

If subtask2 is installed, the skill can leverage its loop feature:

```yaml
subtask: true
loop:
  max: 50
  until: "all tasks in tasks.md are marked [x]"
return:
  - "Checkpoint complete. Committing and continuing..."
```

### Without Subtask2

The skill works without subtask2 by using the native Task tool with manual loop control in the orchestrator context.
