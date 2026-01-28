#!/usr/bin/env bash
# Setup script for QAUserSearch development environment

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

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        return 1
    fi
    log_info "$1 is installed: $(command -v "$1")"
}

main() {
    cd "${PROJECT_ROOT}"
    
    log_info "Setting up QAUserSearch development environment..."
    echo
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    check_command "python3"
    check_command "uv"
    check_command "docker"
    check_command "docker-compose" || check_command "docker"
    echo
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_info "Python version: ${PYTHON_VERSION}"
    if [[ "$(echo "${PYTHON_VERSION} < 3.11" | bc -l)" == "1" ]]; then
        log_error "Python 3.11 or higher is required"
        exit 1
    fi
    echo
    
    # Create .env if not exists
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_warn "Please review .env and update values as needed"
    else
        log_info ".env already exists"
    fi
    echo
    
    # Install dependencies
    log_info "Installing dependencies with uv..."
    uv sync --all-extras
    echo
    
    # Start database
    log_info "Starting PostgreSQL database..."
    docker compose -f docker/docker-compose.yml up -d db
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    for i in {1..30}; do
        if docker compose -f docker/docker-compose.yml exec -T db pg_isready -U postgres &>/dev/null; then
            log_info "Database is ready!"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Database failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
    echo
    
    # Run linting
    log_info "Running linting checks..."
    uv run ruff check src/ tests/ || true
    echo
    
    # Run type checking
    log_info "Running type checks..."
    uv run mypy src/ || true
    echo
    
    log_info "Setup complete! You can now:"
    echo "  - Run the application: uv run uvicorn src.main:app --reload"
    echo "  - Run tests: uv run pytest"
    echo "  - Access API docs: http://localhost:8000/docs"
    echo
}

main "$@"
