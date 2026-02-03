#!/bin/bash
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$HOME/.local/bin:$PATH"
cd ~/joey-ai-agent
source .env
export CLAUDE_CODE_OAUTH_TOKEN

echo "Starting with OAuth Token: ${CLAUDE_CODE_OAUTH_TOKEN:0:25}..."
echo "Time: $(date)"

TASK_CONTENT=$(cat tasks/web-frontend-task.md)
claude -p "$TASK_CONTENT" --print --dangerously-skip-permissions
