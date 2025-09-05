#!/bin/bash
#
# DEPRECATED: Use ./yt_sub_playlist/scripts/dryrun.sh instead
#
echo "⚠️  This script is deprecated. Please use:"
echo "   ./yt_sub_playlist/scripts/dryrun.sh"
echo ""
echo "Running with new package structure..."

source venv/bin/activate
python -m yt_sub_playlist --dry-run --limit 50