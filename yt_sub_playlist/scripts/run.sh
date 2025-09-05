#!/bin/bash
# 
# YouTube Subscription Playlist Sync - Main Runner
# 
# Run the playlist sync with production settings.
# Designed for cron job automation.

set -euo pipefail

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set up logging
LOG_DIR="yt_sub_playlist/data/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting yt-sub-playlist sync" >> "$LOG_FILE"

# Run the main application
if python -m yt_sub_playlist "$@" >> "$LOG_FILE" 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Sync completed successfully" >> "$LOG_FILE"
    exit 0
else
    exit_code=$?
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Sync failed with exit code $exit_code" >> "$LOG_FILE"
    exit $exit_code
fi