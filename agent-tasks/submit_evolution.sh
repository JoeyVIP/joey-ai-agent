#!/bin/bash
#
# Submit Evolution Task - One-click task submission script
#
# This script creates an evolution task in Notion and optionally
# triggers the agent to execute it.
#
# Usage:
#   ./submit_evolution.sh <task_file.md>           # Create task only
#   ./submit_evolution.sh <task_file.md> --execute # Create and execute
#   ./submit_evolution.sh --check-pending          # Check and run pending tasks
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Check if we're checking pending tasks
if [ "$1" == "--check-pending" ]; then
    log_info "Checking for pending evolution tasks..."
    cd "$PROJECT_DIR"
    python3 scripts/evolution_controller.py --check-pending
    exit $?
fi

# Check if task file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <task_file.md> [--execute]"
    echo "       $0 --check-pending"
    exit 1
fi

TASK_FILE="$1"
EXECUTE_FLAG="$2"

# Validate task file exists
if [ ! -f "$TASK_FILE" ]; then
    log_error "Task file not found: $TASK_FILE"
    exit 1
fi

# Create task in Notion
log_info "Creating evolution task in Notion..."
cd "$PROJECT_DIR"

TASK_ID=$(python3 scripts/create_evolution_task.py "$TASK_FILE")

if [ -z "$TASK_ID" ]; then
    log_error "Failed to create task in Notion"
    exit 1
fi

log_info "Task created: $TASK_ID"

# Execute if requested
if [ "$EXECUTE_FLAG" == "--execute" ]; then
    log_info "Executing evolution task..."
    python3 scripts/evolution_controller.py --task-id "$TASK_ID"
else
    log_info "Task created but not executed."
    log_info "To execute, run:"
    echo "  python3 scripts/evolution_controller.py --task-id $TASK_ID"
fi

echo ""
echo "Task ID: $TASK_ID"
