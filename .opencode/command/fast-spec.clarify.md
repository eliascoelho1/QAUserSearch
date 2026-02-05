---
description: Apply clarification answers to the specification (Step 2 of fast-spec pipeline)
subtask: true
---

## User Input

```text
$ARGUMENTS
```

The `$ARGUMENTS` contains the user's answers to clarification questions in format:
`Q1: A, Q2: B, Q3: custom answer` or similar.

## Overview

You are executing **Step 2 (CLARIFY)** of the fast-spec pipeline as a subtask with clean context.

Your job is to apply the user's clarification answers to the spec using a streamlined approach.

## Execution

### 1. Initialize Context

Run `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` from repo root.

Parse JSON for:
- `FEATURE_DIR`
- `FEATURE_SPEC`

If parsing fails, RETURN ERROR with instruction to verify feature branch.

### 2. Load Current Spec

Read the spec file at `FEATURE_SPEC`.

### 3. Parse User Answers

Parse `$ARGUMENTS` to extract answers:

```text
Expected formats:
- "Q1: A, Q2: B, Q3: custom answer"
- "Q1: recommended, Q2: A, Q3: my custom input"
- "A, B, custom answer" (positional)

Map each answer to its corresponding clarification marker in the spec.
```

### 4. Apply Clarifications

For each clarification answer:

1. Find the corresponding `[NEEDS CLARIFICATION: ...]` marker in the spec
2. Determine the answer value:
   - If user said "A", "B", "C", etc. - map to the corresponding option
   - If user said "recommended" or "yes" - use the recommended option
   - If user provided custom text - use that directly
3. Replace the marker with the resolved answer
4. Update related sections (functional requirements, data model, etc.) as needed

### 5. Add Clarifications Section

If not already present, add a `## Clarifications` section with today's session:

```markdown
## Clarifications

### Session YYYY-MM-DD

- Q: {question} → A: {answer}
- Q: {question} → A: {answer}
```

### 6. Write Updated Spec

Save the updated spec back to `FEATURE_SPEC`.

### 7. Validate

Check that:
- All `[NEEDS CLARIFICATION]` markers have been resolved
- No contradictory statements remain
- Markdown structure is valid

### 8. Return Results to Orchestrator

```markdown
## CLARIFY Results

**Status**: SUCCESS | ERROR

### Spec Updated
- **Path**: {spec_path}
- **Clarifications Applied**: {count}

### Changes Made

| Question | Answer Applied | Sections Updated |
|----------|----------------|------------------|
| {Q1} | {answer} | {sections} |
| {Q2} | {answer} | {sections} |

### Remaining Issues

{IF any issues remain}:
- {issue description}

{ELSE}:
- None - spec is fully clarified

### Validation
- **Markers Resolved**: {all | partial}
- **Contradictions**: {none | list}
- **Structure**: {valid | issues}
```

## Error Handling

If parsing or application fails:

```markdown
## CLARIFY Results

**Status**: ERROR

### Error Details
- **Issue**: {what went wrong}
- **User Input**: {$ARGUMENTS}
- **Suggestion**: {how to fix}

### Partial Results
{Any successfully applied clarifications}
```

## Behavior Rules

1. **Answer Parsing**: Be flexible in parsing user's answer format
2. **Marker Resolution**: Remove ALL `[NEEDS CLARIFICATION]` markers
3. **Section Updates**: Update all relevant sections, not just the marker location
4. **Atomic Writes**: Save after each clarification to minimize loss risk
5. **No Questions**: Do NOT ask additional questions - work with what's provided
6. **Graceful Handling**: If an answer doesn't map clearly, make a reasonable interpretation
