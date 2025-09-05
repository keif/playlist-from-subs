#!/bin/bash
# 
# YouTube Subscription Playlist Sync - Quota Usage Simulator
# 
# Run the quota simulator to estimate API usage and costs.

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

echo "Running YouTube API quota usage simulator..."
echo "This estimates quota costs based on typical usage patterns."
echo ""

# Run the quota simulator from the scripts directory
python yt_sub_playlist/scripts/quota_simulator.py