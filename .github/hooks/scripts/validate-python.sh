#!/usr/bin/env bash
# Validate Python files with Ruff and mypy
# Called by Copilot hooks after editing Python files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Get the modified file from hook arguments
FILE="${1:-}"

if [[ -z "${FILE}" ]]; then
    log_error "No file specified"
    exit 1
fi

if [[ ! -f "${FILE}" ]]; then
    log_error "File not found: ${FILE}"
    exit 1
fi

# Only process Python files
if [[ "${FILE}" != *.py ]]; then
    exit 0
fi

log_info "Validating ${FILE}..."

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
