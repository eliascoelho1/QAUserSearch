#!/usr/bin/env bash
# Run unit tests
# Called by Copilot hooks at session end
# Input: JSON from stdin with timestamp, cwd, reason

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Debug log file
DEBUG_LOG="/tmp/copilot-hooks-debug.log"

# Read JSON input from stdin
INPUT=$(cat)

# Log hook invocation for debugging
echo "[$(date '+%Y-%m-%d %H:%M:%S')] sessionEnd hook triggered" >> "${DEBUG_LOG}"
echo "Input: ${INPUT}" >> "${DEBUG_LOG}"

# Extract session end reason
REASON=$(echo "$INPUT" | jq -r '.reason // "unknown"')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

log_info "Session ended with reason: ${REASON}"

# Change to project directory
cd "${CWD}"

log_info "Running unit tests..."

# Run only unit tests for quick feedback
if ! uv run pytest tests/unit/ -v --tb=short; then
    log_error "Unit tests failed"
    exit 1
fi

log_success "All unit tests passed"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tests completed successfully" >> "${DEBUG_LOG}"
