#!/bin/bash
# 
# YouTube Subscription Playlist Sync - Dry Run
# 
# Run the playlist sync in dry-run mode to see what would be added
# without making any actual changes.

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

echo "Running yt-sub-playlist in DRY RUN mode..."
echo "This will show what videos would be added without making changes."
echo ""

# Run in dry-run mode with verbose output
python -m yt_sub_playlist --dry-run --verbose "$@"