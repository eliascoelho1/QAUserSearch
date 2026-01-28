#!/usr/bin/env bash
# Run unit tests
# Called by Copilot hooks at session end

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

log_info "Running unit tests..."

# Run only unit tests for quick feedback
if ! uv run pytest tests/unit/ -v --tb=short; then
    log_error "Unit tests failed"
    exit 1
fi

log_success "All unit tests passed"
