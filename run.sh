#!/bin/bash
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# Clear previous log
: > logs/playlist-sync.log

python main.py --limit 50 >> logs/playlist-sync.log 2>&1