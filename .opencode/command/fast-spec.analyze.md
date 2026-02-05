---
description: Validate cross-artifact consistency (Step 5 of fast-spec pipeline)
subtask: true
---

## User Input

```text
$ARGUMENTS
```

## Overview

You are executing **Step 5 (ANALYZE)** of the fast-spec pipeline as a subtask with clean context.

Your job is to delegate to `/speckit.analyze` and return structured results for the orchestrator.

**CRITICAL**: This is a READ-ONLY operation. Do NOT modify any files.

## Execution

### 1. Initialize Context

Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root.

Parse JSON for:
- `FEATURE_DIR`
- `AVAILABLE_DOCS`

Derive paths:
- SPEC = `{FEATURE_DIR}/spec.md`
- PLAN = `{FEATURE_DIR}/plan.md`
- TASKS = `{FEATURE_DIR}/tasks.md`

If any required file is missing, RETURN ERROR with instruction to run missing prerequisite command.

### 2. Execute speckit.analyze

Run the full `/speckit.analyze` workflow:

1. Load artifacts (progressive disclosure)
2. Build semantic models:
   - Requirements inventory
   - User story/action inventory
   - Task coverage mapping
   - Constitution rule set

3. Detection passes:
   - **A**: Duplication Detection
   - **B**: Ambiguity Detection
   - **C**: Underspecification
   - **D**: Constitution Alignment
   - **E**: Coverage Gaps
   - **F**: Inconsistency

4. Severity assignment (CRITICAL, HIGH, MEDIUM, LOW)

5. Generate analysis report

### 3. Collect Analysis Results

Capture:
- Issues by severity
- Coverage metrics
- Constitution compliance
- Unmapped tasks
- Next action recommendations

### 4. Return Results to Orchestrator

```markdown
## ANALYZE Results

**Status**: SUCCESS | ERROR

### Analysis Summary

| Severity | Count |
|----------|-------|
| CRITICAL | {count} |
| HIGH | {count} |
| MEDIUM | {count} |
| LOW | {count} |

### Issues Found

{If any CRITICAL or HIGH issues}:

#### CRITICAL Issues

| ID | Category | Location | Summary |
|----|----------|----------|---------|
| {id} | {category} | {location} | {summary} |

#### HIGH Issues

| ID | Category | Location | Summary |
|----|----------|----------|---------|
| {id} | {category} | {location} | {summary} |

{Summarize MEDIUM/LOW counts without full details}

### Coverage Metrics

| Metric | Value |
|--------|-------|
| Total Requirements | {count} |
| Total Tasks | {count} |
| Coverage % | {percentage} |
| Unmapped Tasks | {count} |

### Constitution Compliance

- **Status**: {Compliant | Violations Found}
- **Violations**: {none | list}

### Recommendations

{Based on analysis}:

1. {If CRITICAL issues exist}:
   **BLOCKING**: Address CRITICAL issues before implementation
   - {specific recommendation}

2. {If only HIGH/MEDIUM/LOW}:
   **PROCEED WITH CAUTION**: Review HIGH issues, consider addressing before implementation
   - {specific recommendation}

3. {If no significant issues}:
   **READY**: Artifacts are consistent, proceed to implementation
   - Run `/speckit.implement` to begin

### Next Steps

- {Prioritized list of recommended actions}
```

## Error Handling

If analysis fails:

```markdown
## ANALYZE Results

**Status**: ERROR

### Error Details
- **Step**: {which step failed}
- **Message**: {error message}
- **Missing Files**: {list if applicable}
- **Suggestion**: {how to fix}

### Partial Results

{If any analysis was completed, include those results}
```

## Behavior Rules

1. **READ-ONLY**: Do NOT modify any files
2. **Full Analysis**: Run all detection passes
3. **Severity Accuracy**: Apply severity heuristics correctly
4. **Constitution Priority**: Constitution violations are always CRITICAL
5. **Actionable Output**: Provide clear recommendations
6. **Metrics Capture**: Collect all metrics for summary
7. **Non-Blocking**: Analysis errors should not stop the pipeline (warn only)
