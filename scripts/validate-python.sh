#!/usr/bin/env bash
# Validate Python files with Black, Ruff and mypy
# Supports multiple execution modes:
#   1. Manual: ./validate-python.sh [--no-block] <file.py> [file2.py ...]
#   2. Copilot hooks: Reads JSON from stdin with toolName, toolArgs, toolResult
#
# Options:
#   --no-block    Run validation in background (non-blocking mode)
#   --block       Run validation in foreground and fail on errors (default)
#
# Examples:
#   ./validate-python.sh src/main.py                    # Blocking validation
#   ./validate-python.sh --no-block src/main.py         # Non-blocking validation
#   echo '{"toolName":"edit","toolArgs":{"filePath":"src/main.py"}}' | ./validate-python.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Debug log file
DEBUG_LOG="/tmp/copilot-hooks-debug.log"

# Default: blocking mode
BLOCKING=true

# Validate a single Python file
validate_file() {
    local file="$1"

    if [[ ! -f "${file}" ]]; then
        log_error "File not found: ${file}"
        return 1
    fi

    log_info "Validating ${file}..."

    # Run Black (formatting)
    log_info "Running Black..."
    if ! uv run black --check "${file}" 2>/dev/null; then
        log_info "Formatting ${file} with Black..."
        uv run black "${file}"
    fi

    # Run Ruff
    log_info "Running Ruff..."
    if ! uv run ruff check "${file}"; then
        log_error "Ruff found issues in ${file}"
        log_info "Attempting auto-fix..."
        uv run ruff check "${file}" --fix
        if ! uv run ruff check "${file}"; then
            log_error "Ruff issues remain after auto-fix"
            return 1
        fi
    fi

    # Run mypy on the file
    log_info "Running mypy..."
    if ! uv run mypy "${file}" --no-error-summary; then
        log_error "mypy found type errors in ${file}"
        return 1
    fi

    log_success "Validation passed for ${file}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Validation completed for ${file}" >> "${DEBUG_LOG}"
    return 0
}

# Run validation for multiple files
run_validation() {
    local files=("$@")
    local failed=0

    for file in "${files[@]}"; do
        if ! validate_file "$file"; then
            failed=1
        fi
    done

    return $failed
}

# Extract file path from hook JSON input
extract_file_from_hook() {
    local input="$1"
    
    # Log hook invocation for debugging
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] postToolUse hook triggered" >> "${DEBUG_LOG}"
    echo "Input: ${input}" >> "${DEBUG_LOG}"

    # Extract tool name
    local tool_name
    tool_name=$(echo "$input" | jq -r '.toolName // empty' 2>/dev/null || echo "")

    # Only process edit, write, and create tools
    if [[ "${tool_name}" != "edit" && "${tool_name}" != "write" && "${tool_name}" != "create" ]]; then
        return 0
    fi

    # Extract file path from toolArgs JSON
    # Copilot uses 'filePath', some tools use 'path'
    local tool_args file
    tool_args=$(echo "$input" | jq -r '.toolArgs // empty' 2>/dev/null || echo "")
    file=$(echo "$tool_args" | jq -r '.filePath // .path // empty' 2>/dev/null || echo "")

    if [[ -z "${file}" || "${file}" == "null" ]]; then
        return 0
    fi

    # Only process Python files
    if [[ "${file}" != *.py ]]; then
        return 0
    fi

    echo "$file"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] <file.py> [file2.py ...]"
    echo "       echo '{\"toolName\":\"edit\",\"toolArgs\":{\"filePath\":\"file.py\"}}' | $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --no-block    Run validation in background (non-blocking mode)"
    echo "  --block       Run validation in foreground and fail on errors (default)"
    echo "  -h, --help    Show this help message"
}

# Main
main() {
    local files=()
    local positional_args=()

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
                positional_args+=("$1")
                shift
                ;;
        esac
    done

    # Mode 1: Command line arguments
    if [[ ${#positional_args[@]} -gt 0 ]]; then
        files=("${positional_args[@]}")
    # Mode 2: Check if stdin has data (hook mode)
    elif [[ ! -t 0 ]]; then
        local input
        input=$(cat)
        
        if [[ -n "$input" ]]; then
            local file
            file=$(extract_file_from_hook "$input")
            
            if [[ -n "$file" ]]; then
                files=("$file")
            else
                # No Python file to process
                exit 0
            fi
        fi
    else
        # No input provided
        show_usage
        exit 1
    fi

    # Filter to only Python files
    local python_files=()
    for file in "${files[@]}"; do
        if [[ "${file}" == *.py ]]; then
            python_files+=("$file")
        else
            log_warn "Skipping non-Python file: ${file}"
        fi
    done

    if [[ ${#python_files[@]} -eq 0 ]]; then
        log_warn "No Python files to validate"
        exit 0
    fi

    # Run validation based on blocking mode
    if [[ "$BLOCKING" == true ]]; then
        # Blocking: run in foreground and propagate exit code
        run_validation "${python_files[@]}"
        exit $?
    else
        # Non-blocking: run in background
        log_info "Running validation in background..."
        (
            run_validation "${python_files[@]}" >> "${DEBUG_LOG}" 2>&1 || true
        ) &
        disown
        exit 0
    fi
}

main "$@"
