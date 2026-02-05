---
description: Generate technical design artifacts (Step 3 of fast-spec pipeline)
subtask: true
---

## User Input

```text
$ARGUMENTS
```

## Overview

You are executing **Step 3 (PLAN)** of the fast-spec pipeline as a subtask with clean context.

Your job is to delegate to `/speckit.plan` and return structured results for the orchestrator.

## Execution

### 1. Initialize Context

Run `.specify/scripts/bash/setup-plan.sh --json` from repo root.

Parse JSON for:
- `FEATURE_SPEC`
- `IMPL_PLAN`
- `SPECS_DIR`
- `BRANCH`

If parsing fails, RETURN ERROR with instruction to verify feature branch.

### 2. Execute speckit.plan

Run the full `/speckit.plan` workflow:

1. Load FEATURE_SPEC and constitution
2. Load IMPL_PLAN template
3. Fill Technical Context
4. Fill Constitution Check section
5. Evaluate gates (ERROR if violations unjustified)
6. **Phase 0**: Generate research.md (resolve all NEEDS CLARIFICATION)
7. **Phase 1**: Generate data-model.md, contracts/, quickstart.md
8. Update agent context
9. Re-evaluate Constitution Check post-design

### 3. Collect Artifacts

Track all artifacts created:

| Artifact | Expected Path |
|----------|---------------|
| plan.md | `{SPECS_DIR}/plan.md` |
| research.md | `{SPECS_DIR}/research.md` |
| data-model.md | `{SPECS_DIR}/data-model.md` |
| contracts/ | `{SPECS_DIR}/contracts/` |
| quickstart.md | `{SPECS_DIR}/quickstart.md` |

### 4. Return Results to Orchestrator

```markdown
## PLAN Results

**Status**: SUCCESS | ERROR

### Branch Info
- **Branch**: {branch_name}
- **Feature Directory**: {feature_dir}

### Plan Created
- **Path**: {plan_path}

### Artifacts Generated

| Artifact | Path | Status |
|----------|------|--------|
| plan.md | {path} | Created |
| research.md | {path} | Created |
| data-model.md | {path} | Created |
| contracts/ | {path} | Created |
| quickstart.md | {path} | Created |

### Technical Context

**Stack**:
- {list key technologies from plan}

**Architecture**:
- {brief architecture summary}

### Constitution Compliance
- **Gates Passed**: {yes | no}
- **Violations**: {none | list}

### Errors (if any)

{List any non-critical warnings or issues encountered}
```

## Error Handling

If any step fails:

```markdown
## PLAN Results

**Status**: ERROR

### Error Details
- **Step**: {which step failed}
- **Phase**: {0 | 1}
- **Message**: {error message}
- **Suggestion**: {how to fix}

### Partial Results

| Artifact | Status |
|----------|--------|
| plan.md | {created | missing} |
| research.md | {created | missing} |
| ... | ... |
```

## Behavior Rules

1. **Full Delegation**: Execute complete `/speckit.plan` workflow
2. **Phase Completion**: Complete both Phase 0 and Phase 1
3. **Artifact Tracking**: Track all created artifacts for summary
4. **Constitution Check**: Ensure constitution compliance is validated
5. **No Skipping**: Don't skip steps even if they seem optional
6. **Error Capture**: Capture and report errors clearly
