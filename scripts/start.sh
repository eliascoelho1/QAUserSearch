#!/usr/bin/env bash
# Script to start QAUserSearch application

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-false}"
WORKERS="${WORKERS:-1}"

show_help() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Start the QAUserSearch application"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -d, --dev           Run in development mode with auto-reload"
    echo "  -p, --port PORT     Port to listen on (default: 8000)"
    echo "  -H, --host HOST     Host to bind to (default: 0.0.0.0)"
    echo "  -w, --workers NUM   Number of workers (default: 1, ignored in dev mode)"
    echo ""
    echo "Environment variables:"
    echo "  HOST      Host to bind to"
    echo "  PORT      Port to listen on"
    echo "  RELOAD    Enable auto-reload (true/false)"
    echo "  WORKERS   Number of workers"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            RELOAD="true"
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

main() {
    cd "${PROJECT_ROOT}"

    # Check if .env exists
    if [[ ! -f ".env" ]]; then
        log_warn ".env file not found. Creating from .env.example..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warn "Please review .env and update values as needed"
        else
            log_error ".env.example not found. Please create a .env file."
            exit 1
        fi
    fi

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install it first: https://docs.astral.sh/uv/"
        exit 1
    fi

    log_info "Starting QAUserSearch application..."
    log_info "Host: ${HOST}"
    log_info "Port: ${PORT}"

    if [[ "${RELOAD}" == "true" ]]; then
        log_info "Mode: Development (auto-reload enabled)"
        exec uv run uvicorn src.main:app \
            --host "${HOST}" \
            --port "${PORT}" \
            --reload
    else
        log_info "Mode: Production"
        log_info "Workers: ${WORKERS}"
        exec uv run uvicorn src.main:app \
            --host "${HOST}" \
            --port "${PORT}" \
            --workers "${WORKERS}"
    fi
}

main "$@"
