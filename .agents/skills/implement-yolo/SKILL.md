---
name: implement-yolo
description: "Execute automated implementation of Speckit specifications in yolo mode. Implements tasks until each checkpoint, commits automatically, and loops until all tasks complete. Use when: need yolo implementation, auto implement spec, autonomous spec implementation, implement all tasks automatically, yolo mode, implement loop."
source: QAUserSearch (proprietary)
---

# Implement Yolo - Autonomous Implementation Loop

**Role**: Implementation Loop Orchestrator

You orchestrate automated implementation of Speckit specifications by running `/speckit.implement` in a loop. Each iteration implements tasks until a checkpoint, commits the work, and continues until all tasks are complete.

## Capabilities

- Execute implementation in autonomous loop mode
- **Clean context isolation** per iteration (each runs as independent subtask)
- Detect and stop at checkpoints (marked with `**Checkpoint**`)
- Auto-commit at each checkpoint with descriptive messages
- Retry recoverable errors (lint/type/test) up to 3 times
- Fail-fast on non-recoverable errors
- Progress tracking with iteration count and task completion status

## Requirements

- Active feature branch with `tasks.md` in spec directory
- Speckit command available (`/speckit.implement`)
- Git repository with clean working tree (or staged changes only)
- `.specify/` directory structure

## Workflow Overview

```
/implement-yolo
     |
     v
[INIT] Validate prerequisites
     |  - tasks.md exists
     |  - Has pending tasks (- [ ])
     |  - On feature branch (not main/master)
     |
     v
[SCAN] Parse tasks.md
     |  - Identify pending tasks
     |  - Find next checkpoint
     |  - Determine current phase
     |
     +---> [LOOP] while (has_pending_tasks):
              |
              |---> [IMPLEMENT] Subtask: /speckit.implement
              |        - Implement until next checkpoint
              |        - Mark tasks as [x] when complete
              |        - STOP at checkpoint line
              |
              |---> [VERIFY] Check result:
              |        - lint/type/test error -> retry (up to 3x)
              |        - other error -> STOP + report
              |        - success -> continue
              |
              |---> [COMMIT] Create checkpoint commit
              |        - Message: feat({phase}): {checkpoint}
              |
              |---> [NEXT] Re-scan tasks.md
              |        - Find next pending tasks
              |        - Find next checkpoint
              |        - Loop or exit
              |
     v
[COMPLETE] All tasks done - Final summary
```

## Usage

### Basic Usage

```
/implement-yolo
```

Starts autonomous implementation from current tasks.md state.

### Resume After Error

```
/implement-yolo
```

Re-run after fixing issues manually. The skill resumes from first pending task.

## Execution Steps

### Step 1: Initialize [INIT]

**Validate prerequisites** before starting the loop:

1. **Find spec directory**: Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks` to get FEATURE_DIR
2. **Check branch**: Verify not on `main` or `master`
3. **Check tasks.md**: Verify file exists and has at least one pending task (`- [ ]`)
4. **Check working tree**: Verify no uncommitted changes (warn if dirty)

**On validation failure**: Stop immediately with clear error message.

**Output**:
```
Implement Yolo - Starting

Feature: {branch_name}
Spec Dir: specs/{feature}/
Tasks Found: {total_tasks} total, {pending_tasks} pending
Checkpoints: {checkpoint_count} remaining

Ready to implement autonomously.
```

### Step 2: Scan Tasks [SCAN]

Parse `tasks.md` to identify:

1. **Pending tasks**: Lines matching `- [ ]` pattern
2. **Next checkpoint**: First line containing `**Checkpoint**` after pending tasks
3. **Current phase**: Phase header (e.g., "Phase 3: User Story 1")
4. **Tasks until checkpoint**: All `- [ ]` tasks between current position and checkpoint

**Checkpoint detection logic**:

```python
# Pseudocode for checkpoint detection
pending_tasks = []
next_checkpoint = None
current_phase = None

for line in tasks_md:
    if line.startswith("## Phase"):
        current_phase = extract_phase_name(line)
    elif "- [ ]" in line:
        pending_tasks.append(parse_task(line))
    elif "**Checkpoint**" in line and pending_tasks:
        next_checkpoint = line
        break  # Stop at first checkpoint after pending tasks
```

**Output**:
```
Iteration {n}: Scanning tasks.md

Phase: {current_phase}
Tasks to implement: {count}
Next checkpoint: {checkpoint_description}

Tasks in this batch:
- T067 Description
- T068 Description
...
```

### Step 3: Implement [LOOP - IMPLEMENT]

**Launch subtask** with specific instructions:

```
Task(
  description="[Iteration {n}] speckit.implement until checkpoint",
  prompt="/speckit.implement

IMPORTANT: Implement tasks until you reach the next checkpoint.

Current phase: {current_phase}
Tasks to complete: {task_list}
Stop condition: When you see '**Checkpoint**:' in tasks.md

After completing each task:
1. Mark it as [x] in tasks.md
2. Continue to next task

When you reach '**Checkpoint**', STOP and report completion.",
  subagent_type="general"
)
```

**Subtask execution**:
- Implements tasks following TDD approach
- Marks each completed task as `[x]` in tasks.md
- Stops when reaching `**Checkpoint**` line

**Collect from result**: List of completed tasks, any errors encountered

### Step 4: Verify [LOOP - VERIFY]

After subtask completes, verify the result:

1. **Run validation**:
   ```bash
   uv run ruff check src/ tests/
   uv run mypy src/
   uv run pytest tests/unit/ -x
   ```

2. **Evaluate result**:
   - **Success**: All checks pass -> proceed to commit
   - **Recoverable error**: Lint/type/test failure -> retry
   - **Non-recoverable error**: Other errors -> stop

**Retry logic** (for recoverable errors):

```
retry_count = 0
MAX_RETRIES = 3

while retry_count < MAX_RETRIES:
    result = run_validation()
    if result.success:
        break
    retry_count += 1
    
    # Launch fix subtask
    Task(
      description="[Retry {retry_count}/{MAX_RETRIES}] Fix errors",
      prompt="/speckit.implement

Fix the following errors:
{error_output}

After fixing, run validation again.",
      subagent_type="general"
    )

if retry_count >= MAX_RETRIES:
    STOP("Max retries exceeded. Manual intervention required.")
```

**Output on retry**:
```
Verification failed. Retrying ({retry_count}/{MAX_RETRIES})

Errors:
{error_output}

Launching fix subtask...
```

### Step 5: Commit [LOOP - COMMIT]

Create a checkpoint commit:

**Commit message format**:
```
feat({phase_slug}): {checkpoint_description}

Tasks completed:
- T067 Description
- T068 Description

Checkpoint: {full_checkpoint_text}
```

**Example**:
```
feat(polish): Update environment and bootstrap files

Tasks completed:
- T067 Atualizar .env.example com novas variaveis
- T068 Criar arquivo catalog/catalog.yaml inicial

Checkpoint: Environment and bootstrap files ready
```

**Execution**:
```bash
git add -A
git commit -m "{commit_message}"
```

**Output**:
```
Checkpoint commit created

Commit: {short_sha}
Message: feat({phase}): {checkpoint}
Tasks: {count} completed
```

### Step 6: Next Iteration [LOOP - NEXT]

Re-scan tasks.md and decide:

1. **More pending tasks**: Loop back to Step 2 (SCAN)
2. **No pending tasks**: Proceed to completion (Step 7)

**Output**:
```
Checkpoint complete. Scanning for next iteration...

Remaining: {pending_count} tasks, {checkpoint_count} checkpoints
```

### Step 7: Complete [COMPLETE]

When all tasks are done:

**Output**:
```
Implement Yolo - COMPLETE

Feature: {branch_name}
Total Iterations: {iteration_count}
Total Tasks Completed: {task_count}
Total Commits: {commit_count}

All checkpoints reached. Implementation complete.

Next steps:
- Review commits: git log --oneline -n {commit_count}
- Run full test suite: uv run pytest
- Create PR: /speckit.pr (or gh pr create)
```

## Error Handling

### Recoverable Errors (retry up to 3x)

| Error Type | Detection | Recovery |
|------------|-----------|----------|
| Lint errors | `ruff check` fails | Launch fix subtask |
| Type errors | `mypy` fails | Launch fix subtask |
| Test failures | `pytest` fails | Launch fix subtask |

### Non-Recoverable Errors (stop immediately)

| Error Type | Detection | Action |
|------------|-----------|--------|
| tasks.md not found | File doesn't exist | Stop with instructions |
| No pending tasks | No `- [ ]` lines | Stop (already complete) |
| Not on feature branch | On main/master | Stop with warning |
| 3 retries exhausted | Retry count exceeded | Stop with error summary |
| Git error | Commit/add fails | Stop with git status |

### Error Output Format

```
Implement Yolo - STOPPED

Reason: {error_type}
Details: {error_details}

Current state:
- Iteration: {current_iteration}
- Last checkpoint: {last_checkpoint}
- Pending tasks: {pending_count}

To resume:
1. Fix the issue manually
2. Run /implement-yolo again
```

## Context Isolation Strategy

**CRITICAL**: Each implementation iteration MUST run as an independent subtask.

### Why Clean Context Matters

1. **Prevents token bloat**: Implementation generates significant code; accumulated context would exceed limits
2. **Avoids stale state**: Each iteration reads fresh state from disk
3. **Enables clean retries**: Failed iterations don't pollute next attempt
4. **Matches standalone behavior**: Running `/speckit.implement` standalone behaves identically

### Execution Pattern

```
Orchestrator (this context)
    |
    +---> [Iteration 1] speckit.implement --> returns: completed tasks
    |         (clean context)
    |
    +---> [Verify] Run lint/type/test
    |
    +---> [Commit] Create checkpoint commit
    |
    +---> [Iteration 2] speckit.implement --> returns: completed tasks
    |         (clean context)
    |
    ...continues until all tasks complete...
```

## Progress Tracking

Maintain state across iterations:

```yaml
# Internal state (orchestrator context only)
state:
  iteration: 3
  total_tasks: 73
  completed_tasks: 45
  pending_tasks: 28
  checkpoints_reached: 4
  retries_used: 1
  commits:
    - sha: "abc1234"
      message: "feat(setup): Phase 1 complete"
    - sha: "def5678"
      message: "feat(foundational): Core infrastructure ready"
```

**Progress display** (after each iteration):

```
Progress: [=========>          ] 45/73 tasks (62%)
Iterations: 3 | Checkpoints: 4 | Retries: 1/3
```

## Anti-Patterns

### Running Without Subtasks

**Why bad**: Context accumulates across iterations, causing token overflow

**Instead**: ALWAYS use Task tool to launch each implementation iteration

### Ignoring Checkpoints

**Why bad**: Large commits, harder to review, no incremental validation

**Instead**: Stop at EVERY checkpoint, commit, then continue

### Skipping Verification

**Why bad**: Broken code propagates to next iteration

**Instead**: ALWAYS run lint/type/test after each implementation

### Continuing After 3 Retries

**Why bad**: Usually indicates deeper issue requiring human judgment

**Instead**: Stop and report, let user investigate

### Committing Without Verification

**Why bad**: Broken commits in history

**Instead**: ALWAYS verify before commit

## Related Commands

- `/speckit.implement` - Single implementation run (used internally)
- `/speckit.tasks` - Generate task breakdown
- `/speckit.analyze` - Validate spec consistency
- `/fast-spec` - Full specification pipeline

## Configuration

The skill respects these settings from `config.py`:

- **CATALOG_PATH**: Where to find catalog files
- **LOG_LEVEL**: Verbosity of progress output

## Examples

### Example 1: Fresh Start

```
User: /implement-yolo