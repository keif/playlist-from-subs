#!/bin/bash
#
# DEPRECATED: Use ./yt_sub_playlist/scripts/run.sh instead
#
echo "⚠️  This script is deprecated. Please use:"
echo "   ./yt_sub_playlist/scripts/run.sh"
echo ""
echo "Running with new package structure..."

source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# Clear previous log
: > logs/playlist-sync.log

python -m yt_sub_playlist --limit 50 >> logs/playlist-sync.log 2>&1