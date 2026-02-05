---
name: fast-spec
description: "Run full specification pipeline (specify -> clarify -> plan -> tasks -> analyze) orchestrating speckit commands with clean context isolation. Use when: need complete feature spec, fast specification, quick spec, full pipeline, specify and plan, end-to-end spec."
source: QAUserSearch (proprietary)
---

# Fast Spec - Full Specification Pipeline

**Role**: Specification Pipeline Orchestrator

You orchestrate the complete feature specification workflow by launching each step as a **subtask with clean context**. Each subtask invokes its corresponding speckit command, ensuring no context pollution between phases.

## Capabilities

- Execute full spec pipeline in one command
- **Clean context isolation between steps** (each runs as independent subtask)
- Delegate each phase to specialized speckit commands
- Progress tracking with phase indicators
- Final consolidated summary with all artifacts
- Fail-fast on critical errors
- Consistent behavior with standalone speckit commands

## Requirements

- Existing speckit commands (`/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze`)
- `.specify/` directory structure with templates and scripts
- Git repository for branch management

## Workflow Overview

```
/fast-spec <feature description>
     |
     v
[1/5] SUBTASK: /speckit.specify --> Creates branch + spec.md (clean context)
     |
     v
[2/5] SUBTASK: /speckit.clarify --> Resolves ambiguities (clean context)
     |
     v
[3/5] SUBTASK: /speckit.plan --> Generates design artifacts (clean context)
     |
     v
[4/5] SUBTASK: /speckit.tasks --> Generates tasks.md (clean context)
     |
     v
[5/5] SUBTASK: /speckit.analyze --> Validates consistency (clean context)
     |
     v
[SUMMARY] Consolidated report with all artifacts and issues
```

## Context Isolation Strategy

**CRITICAL**: Each step MUST run as an independent subtask to ensure clean context.

### Why Clean Context Matters

1. **Prevents token bloat**: Each phase generates significant content; accumulated context would exceed limits
2. **Avoids hallucination**: Previous phase artifacts in context can cause the agent to "remember" outdated states
3. **Ensures consistency**: Each command reads fresh state from disk, not stale in-memory representations
4. **Matches standalone behavior**: Running `/speckit.plan` standalone should behave identically to running it within `/fast-spec`

### How to Execute Each Step

Use the **Task tool** to launch each step as a subtask:

```
Task(
  description="[Step N/5] speckit.{command}",
  prompt="/speckit.{command} {arguments if any}",
  subagent_type="general"
)
```

**IMPORTANT**: 
- Wait for each subtask to complete before launching the next
- Parse the subtask result to check for success/failure
- Only proceed to next step if current step succeeded
- Collect key outputs (paths, metrics) from each subtask for final summary

## Usage

### Basic Usage

```
/fast-spec Add user authentication with OAuth2
```

### With Context

```
/fast-spec Create a dashboard for analytics that shows user metrics and trends
```

## Execution Steps

When `/fast-spec <feature description>` is invoked, you MUST execute these steps in order, **each as an independent subtask**:

### Step 1: Specify [1/5]

**Execution**: Launch subtask with clean context

```
Task(
  description="[1/5] speckit.specify",
  prompt="/speckit.specify <feature description>",
  subagent_type="general"
)
```

**What the subtask does**:
- Creates feature branch (numbered)
- Generates initial `spec.md` from template
- Runs specification quality validation
- Handles clarification questions if needed (max 3)

**Success criteria**: 
- Branch created and checked out
- `spec.md` created in `specs/{number}-{short-name}/`
- All quality checklist items pass
- No more than 3 `[NEEDS CLARIFICATION]` markers remain

**Collect from result**: Branch name, spec file path

**On failure**: Stop pipeline, report error, suggest fix

### Step 2: Clarify [2/5]

**Execution**: Launch subtask with clean context

```
Task(
  description="[2/5] speckit.clarify",
  prompt="/speckit.clarify",
  subagent_type="general"
)
```

**What the subtask does**:
- Loads current spec from active branch (fresh from disk)
- Scans for ambiguities across taxonomy categories
- Asks up to 5 targeted clarification questions (sequential)
- Updates spec with answers in `## Clarifications` section
- Integrates clarifications into relevant spec sections

**Success criteria**:
- All critical ambiguities resolved
- Coverage summary shows acceptable status
- Spec updated with clarifications

**User interaction**: May pause for answers (respects user "done" signal)

**On failure**: Report coverage gaps, suggest proceeding if only low-impact items remain

### Step 3: Plan [3/5]

**Execution**: Launch subtask with clean context

```
Task(
  description="[3/5] speckit.plan",
  prompt="/speckit.plan",
  subagent_type="general"
)
```

**What the subtask does**:
- Loads spec.md and constitution.md (fresh from disk)
- Runs Constitution Check against quality gates
- Phase 0: Generates `research.md` (resolves tech unknowns)
- Phase 1: Generates `data-model.md`, `contracts/`, `quickstart.md`
- Updates agent context (AGENTS.md)

**Success criteria**:
- `plan.md` complete with Technical Context filled
- Constitution Check passes or violations justified
- All design artifacts generated
- No unresolved `NEEDS CLARIFICATION` in technical sections

**Collect from result**: List of generated artifacts

**On failure**: Report gate violations or missing clarifications

### Step 4: Tasks [4/5]

**Execution**: Launch subtask with clean context

```
Task(
  description="[4/5] speckit.tasks",
  prompt="/speckit.tasks",
  subagent_type="general"
)
```

**What the subtask does**:
- Loads plan.md, spec.md, and optional artifacts (fresh from disk)
- Maps user stories to tasks
- Organizes tasks by phase (Setup → Foundational → User Stories → Polish)
- Generates dependency graph
- Creates parallel execution examples

**Success criteria**:
- `tasks.md` generated with all user stories covered
- Each task follows checklist format: `- [ ] [TaskID] [P?] [Story?] Description`
- All requirements have ≥1 task
- Dependencies clearly defined

**Collect from result**: Task count, phase count

**On failure**: Report missing coverage or format violations

### Step 5: Analyze [5/5]

**Execution**: Launch subtask with clean context

```
Task(
  description="[5/5] speckit.analyze",
  prompt="/speckit.analyze",
  subagent_type="general"
)
```

**What the subtask does**:
- Loads spec.md, plan.md, tasks.md (fresh from disk, read-only)
- Detects duplications, ambiguities, underspecifications
- Validates constitution alignment
- Checks coverage (requirements → tasks mapping)
- Identifies inconsistencies

**Success criteria**:
- Analysis report generated
- Coverage metrics calculated
- Issues categorized by severity (CRITICAL/HIGH/MEDIUM/LOW)

**Collect from result**: Coverage %, issue counts by severity, critical issues list

**Output**: Structured Markdown report with findings table

**On failure**: N/A (read-only, always succeeds)

### Step 6: Summary (Orchestrator Context)

**Execution**: This step runs in the orchestrator context (NOT a subtask)

**Action**: Generate consolidated pipeline report using collected data from subtasks

**Content**:
```markdown
## Fast Spec Pipeline - COMPLETE

**Feature**: {branch name}
**Status**: ✅ All phases completed

### Generated Artifacts

- Branch: `{number}-{short-name}`
- Spec: `specs/{number}-{short-name}/spec.md`
- Plan: `specs/{number}-{short-name}/plan.md`
- Tasks: `specs/{number}-{short-name}/tasks.md`
- Research: `specs/{number}-{short-name}/research.md` (if exists)
- Data Model: `specs/{number}-{short-name}/data-model.md` (if exists)
- Contracts: `specs/{number}-{short-name}/contracts/` (if exists)

### Analysis Summary

- Total Requirements: {count}
- Total Tasks: {count}
- Coverage: {percentage}%
- Issues: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW

### Next Steps

{If CRITICAL issues}: ⚠️ Resolve CRITICAL issues before `/speckit.implement`
{If no CRITICAL}: ✅ Ready for implementation - run `/speckit.implement`

### Critical Issues (if any)

{List of CRITICAL findings from analyze}
```

## Patterns

### Clean Context Execution

**CRITICAL**: Each phase MUST run as an independent subtask:

```
Orchestrator (this context)
    │
    ├──► Task [1/5] speckit.specify ──► returns: branch, spec path
    │         (clean context)
    │
    ├──► Task [2/5] speckit.clarify ──► returns: clarification count
    │         (clean context)
    │
    ├──► Task [3/5] speckit.plan ──► returns: artifact list
    │         (clean context)
    │
    ├──► Task [4/5] speckit.tasks ──► returns: task count
    │         (clean context)
    │
    ├──► Task [5/5] speckit.analyze ──► returns: metrics, issues
    │         (clean context)
    │
    └──► Summary (orchestrator generates from collected results)
```

**Why this works**:
- Each subtask starts fresh, reading artifacts from disk
- No accumulated context between phases
- Subtask results are minimal (paths, counts, issues)
- Orchestrator only holds summary data, not full artifacts

### Sequential Execution (REQUIRED)

Steps MUST run sequentially, not in parallel:

1. **specify** creates branch and spec → must complete before clarify
2. **clarify** updates spec → must complete before plan  
3. **plan** generates design → must complete before tasks
4. **tasks** needs plan → must complete before analyze
5. **analyze** validates all → runs last

**DO NOT** launch multiple subtasks in parallel - each depends on the previous.

### Full Pipeline Execution

Each phase delegates to its corresponding speckit command via subtask, ensuring:
- **Clean context isolation** (no token bloat or stale state)
- Consistent behavior with standalone commands
- Reusable components
- Maintainability (single source of truth)

### Error Handling

- Failures in one subtask stop the pipeline
- Clear error messages reference the failed command
- User can resume from specific step using standalone commands
- Preserve all artifacts up to failure point
- **Context isolation ensures partial failures don't corrupt state**

### User Interaction

- `/speckit.specify` subtask may pause for clarification questions (max 3)
- `/speckit.clarify` subtask may pause for sequential questions (max 5)
- User can signal early termination ("done", "skip clarify")
- **User interactions happen within subtask context, not orchestrator**

## Anti-Patterns

### Running Without Subtasks

**Why bad**: Context accumulates across phases, causing token overflow and stale state

**Instead**: ALWAYS use Task tool to launch each step as independent subtask

### Running Steps in Parallel

**Why bad**: Each step depends on artifacts from previous step

**Instead**: Run steps sequentially, waiting for each to complete

### Collecting Full Artifacts in Orchestrator

**Why bad**: Defeats purpose of context isolation; orchestrator context bloats

**Instead**: Collect only summary data (paths, counts, issue lists) from subtask results

### Running Steps Manually

**Why bad**: More tedious, no consolidated report

**Instead**: Use `/fast-spec` for full pipeline; use individual `/speckit.*` commands only for:
- Debugging specific phase
- Updating single artifact after implementation
- Iterative refinement of one section

### Skipping Clarify

**Why bad**: Downstream rework, ambiguous specs

**Instead**: Let pipeline run clarify unless explicitly exploratory spike

### Ignoring Analyze Issues

**Why bad**: Inconsistent artifacts, implementation problems

**Instead**: Address CRITICAL issues before proceeding to `/speckit.implement`

## Related Commands

- `/speckit.specify` - Step 1: Create spec
- `/speckit.clarify` - Step 2: Resolve ambiguities
- `/speckit.plan` - Step 3: Generate technical design
- `/speckit.tasks` - Step 4: Create task breakdown
- `/speckit.analyze` - Step 5: Validate consistency
- `/speckit.implement` - Next: Execute implementation

## References

- See individual speckit command files: `.opencode/command/speckit.*.md`
- [OpenCode Agents Documentation](https://opencode.ai/docs/agents/)
- [OpenCode Commands Documentation](https://opencode.ai/docs/commands/)
