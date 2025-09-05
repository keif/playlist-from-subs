#!/bin/bash
# 
# YouTube Subscription Playlist Sync - Reset Authentication
# 
# Reset stored authentication tokens to force a fresh OAuth flow.
# Useful when switching Google accounts or troubleshooting auth issues.

set -euo pipefail

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to project directory
cd "$PROJECT_DIR"

echo "Resetting YouTube API authentication..."

# Remove stored token file
if [ -f "token.json" ]; then
    rm -f "token.json"
    echo "✅ Removed stored authentication token (token.json)"
else
    echo "ℹ️  No stored token found (token.json)"
fi

# Test authentication to trigger OAuth flow
echo ""
echo "Testing authentication (this will open your browser)..."

python -c "
from yt_sub_playlist.auth.oauth import test_authentication
import sys
success = test_authentication()
if success:
    print('✅ Authentication reset and re-established successfully!')
else:
    print('❌ Authentication failed')
    sys.exit(1)
"