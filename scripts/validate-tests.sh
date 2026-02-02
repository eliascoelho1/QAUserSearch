#!/usr/bin/env bash
# Run unit tests
# Supports multiple execution modes:
#   1. Manual: ./validate-tests.sh [OPTIONS] [directory]
#   2. Copilot hooks: Reads JSON from stdin with timestamp, cwd, reason
#
# Options:
#   --no-block    Run tests in background (non-blocking mode)
#   --block       Run tests in foreground and fail on errors (default)
#
# Examples:
#   ./validate-tests.sh                         # Run in current directory (blocking)
#   ./validate-tests.sh /path/to/project        # Run in specific directory
#   ./validate-tests.sh --no-block              # Run in background
#   echo '{"cwd": "."}' | ./validate-tests.sh   # Copilot hook mode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Debug log file
DEBUG_LOG="/tmp/copilot-hooks-debug.log"

# Default: blocking mode
BLOCKING=true

# Run tests in the given directory
run_tests() {
    local work_dir="$1"

    # Resolve to absolute path if relative
    if [[ ! "$work_dir" = /* ]]; then
        work_dir="$(cd "$work_dir" 2>/dev/null && pwd)" || {
            log_error "Directory not found: $work_dir"
            return 1
        }
    fi

    # Change to project directory
    cd "${work_dir}"

    log_info "Running unit tests in ${work_dir}..."

    # Check if tests directory exists
    if [[ ! -d "tests/unit" ]]; then
        log_warn "No tests/unit directory found, skipping tests"
        return 0
    fi

    # Run only unit tests for quick feedback
    if ! uv run pytest tests/unit/ -v --tb=short; then
        log_error "Unit tests failed"
        return 1
    fi

    log_success "All unit tests passed"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tests completed successfully" >> "${DEBUG_LOG}"
    return 0
}

# Detect execution mode and get working directory from stdin (hook mode)
get_working_directory_from_stdin() {
    local input
    input=$(cat)
    
    if [[ -n "$input" ]]; then
        # Log hook invocation for debugging
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] sessionEnd hook triggered" >> "${DEBUG_LOG}"
        echo "Input: ${input}" >> "${DEBUG_LOG}"
        
        # Extract working directory from JSON
        local cwd
        cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null || echo "")
        
        if [[ -n "$cwd" && "$cwd" != "null" ]]; then
            # Extract reason for logging (output to stderr to not pollute return value)
            local reason
            reason=$(echo "$input" | jq -r '.reason // "unknown"' 2>/dev/null || echo "unknown")
            log_info "Session ended with reason: ${reason}" >&2
            echo "$cwd"
            return
        fi
    fi

    # Default to current directory
    echo "."
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [directory]"
    echo "       echo '{\"cwd\": \".\", \"reason\": \"...\"}' | $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-block    Run tests in background (non-blocking mode)"
    echo "  --block       Run tests in foreground and fail on errors (default)"
    echo "  -h, --help    Show this help message"
}

# Main
main() {
    local work_dir=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-block)
                BLOCKING=false
                shift
                ;;
            --block)
                BLOCKING=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                work_dir="$1"
                shift
                ;;
        esac
    done

    # If no directory provided, check stdin or use current directory
    if [[ -z "$work_dir" ]]; then
        if [[ ! -t 0 ]]; then
            # Hook mode: read from stdin
            work_dir=$(get_working_directory_from_stdin)
        else
            # Default to current directory
            work_dir="."
        fi
    fi

    # Run tests based on blocking mode
    if [[ "$BLOCKING" == true ]]; then
        # Blocking: run in foreground and propagate exit code
        run_tests "$work_dir"
        exit $?
    else
        # Non-blocking: run in background
        log_info "Running tests in background..."
        (
            run_tests "$work_dir" >> "${DEBUG_LOG}" 2>&1 || true
        ) &
        disown
        exit 0
    fi
}

main "$@"
