#!/usr/bin/env bash
# Common functions for hook scripts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get project root directory
get_project_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Ensure we're in the project root
ensure_project_root() {
    cd "$(get_project_root)"
}
