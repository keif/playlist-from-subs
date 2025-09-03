#!/bin/bash
echo "⚠️ Removing OAuth token..."
rm -f token.json

echo "🔐 Starting auth flow..."
source venv/bin/activate
python auth.py