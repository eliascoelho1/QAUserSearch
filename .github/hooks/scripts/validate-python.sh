#!/usr/bin/env bash
# Validate Python files with Ruff and mypy
# Called by Copilot hooks after editing Python files
# Input: JSON from stdin with toolName, toolArgs, toolResult

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Debug log file
DEBUG_LOG="/tmp/copilot-hooks-debug.log"

# Read JSON input from stdin
INPUT=$(cat)

# Log hook invocation for debugging
echo "[$(date '+%Y-%m-%d %H:%M:%S')] postToolUse hook triggered" >> "${DEBUG_LOG}"
echo "Input: ${INPUT}" >> "${DEBUG_LOG}"

# Extract tool name and file path from toolArgs
TOOL_NAME=$(echo "$INPUT" | jq -r '.toolName')
TOOL_ARGS=$(echo "$INPUT" | jq -r '.toolArgs')

# Only process edit and create tools
if [[ "${TOOL_NAME}" != "edit" && "${TOOL_NAME}" != "create" ]]; then
    exit 0
fi

# Extract file path from toolArgs JSON
FILE=$(echo "$TOOL_ARGS" | jq -r '.path // empty')

if [[ -z "${FILE}" ]]; then
    exit 0
fi

# Only process Python files
if [[ "${FILE}" != *.py ]]; then
    exit 0
fi

if [[ ! -f "${FILE}" ]]; then
    log_error "File not found: ${FILE}"
    exit 1
fi

log_info "Validating ${FILE}..."

# Run Black (formatting)
log_info "Running Black..."
if ! uv run black --check "${FILE}" 2>/dev/null; then
    log_info "Formatting ${FILE} with Black..."
    uv run black "${FILE}"
fi

# Run Ruff
log_info "Running Ruff..."
if ! uv run ruff check "${FILE}"; then
    log_error "Ruff found issues in ${FILE}"
    log_info "Attempting auto-fix..."
    uv run ruff check "${FILE}" --fix
    if ! uv run ruff check "${FILE}"; then
        log_error "Ruff issues remain after auto-fix"
        exit 1
    fi
fi

# Run mypy on the file
log_info "Running mypy..."
if ! uv run mypy "${FILE}" --no-error-summary; then
    log_error "mypy found type errors in ${FILE}"
    exit 1
fi

log_success "Validation passed for ${FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Validation completed for ${FILE}" >> "${DEBUG_LOG}"
