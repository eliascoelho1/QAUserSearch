---
description: Create feature branch and initial specification (Step 1 of fast-spec pipeline)
subtask: true
---

## User Input

```text
$ARGUMENTS
```

## Overview

You are executing **Step 1 (SPECIFY)** of the fast-spec pipeline as a subtask with clean context.

Your job is to delegate to `/speckit.specify` and return structured results for the orchestrator.

## Execution

### 1. Validate Input

```text
IF $ARGUMENTS is empty or "$ARGUMENTS":
  RETURN ERROR: "No feature description provided"
```

### 2. Execute speckit.specify

Run the full `/speckit.specify $ARGUMENTS` workflow:

1. Generate concise short name for branch
2. Check for existing branches and calculate next number
3. Create branch using `.specify/scripts/bash/create-new-feature.sh`
4. Load spec template and fill with feature details
5. Write specification to SPEC_FILE
6. Run specification quality validation
7. Collect any [NEEDS CLARIFICATION] markers

### 3. Collect Clarifications

After spec is created, scan for `[NEEDS CLARIFICATION: ...]` markers.

For each marker found, extract:
- Question context
- Specific question
- Suggested options (if applicable)

**LIMIT**: Maximum 3 clarification markers (as per speckit.specify rules)

### 4. Return Results to Orchestrator

Return a structured result in this format:

```markdown
## SPECIFY Results

**Status**: SUCCESS | ERROR

### Branch Info
- **Branch Name**: {branch_name}
- **Feature Directory**: {feature_dir}

### Specification
- **Spec Path**: {spec_path}
- **Checklist Path**: {checklist_path}

### Clarifications Needed

{IF clarifications exist}:

**Count**: {N} clarification(s) found

{For each clarification}:

#### Q{N}: {Topic}

**Context**: {Quote from spec}

**Question**: {Specific question}

**Options**:
| Option | Answer | Implications |
|--------|--------|--------------|
| A | {answer} | {implication} |
| B | {answer} | {implication} |
| C | {answer} | {implication} |

---

{ELSE}:

**Count**: 0 - No clarifications needed

### Errors (if any)

{List any non-critical warnings or issues encountered}
```

## Error Handling

If any step fails:

```markdown
## SPECIFY Results

**Status**: ERROR

### Error Details
- **Step**: {which step failed}
- **Message**: {error message}
- **Suggestion**: {how to fix}

### Partial Results (if any)
{Include any successfully created artifacts}
```

## Behavior Rules

1. **Full Delegation**: Execute complete `/speckit.specify` workflow
2. **Clean Extraction**: Extract clarifications in structured format
3. **No User Interaction**: Do NOT prompt user for clarifications - return them for orchestrator
4. **Structured Output**: Always return results in the specified format
5. **Error Capture**: Capture and report errors, don't hide them
