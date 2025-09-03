#!/bin/bash
source venv/bin/activate

: > logs/playlist-sync.log

# Ensure logs directory exists
mkdir -p logs
python main.py --limit 50 >> logs/playlist-sync.log 2>&1