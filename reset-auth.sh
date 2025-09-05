#!/bin/bash
#
# DEPRECATED: Use ./yt_sub_playlist/scripts/reset-auth.sh instead
#
echo "⚠️  This script is deprecated. Please use:"
echo "   ./yt_sub_playlist/scripts/reset-auth.sh"
echo ""
echo "Running with new package structure..."

echo "⚠️ Removing OAuth token..."
rm -f token.json

echo "🔐 Starting auth flow..."
source venv/bin/activate
python -m yt_sub_playlist.auth.oauth