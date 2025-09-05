#!/bin/bash
#
# DEPRECATED: Use the new package structure instead
#
echo "⚠️  This script is deprecated. Please use:"
echo "   LOOKBACK_HOURS=168 python -m yt_sub_playlist --limit 100"
echo ""
echo "Running with new package structure..."

source venv/bin/activate
LOOKBACK_HOURS=168 python -m yt_sub_playlist --limit 100