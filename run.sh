#!/bin/bash
source venv/bin/activate
python main.py --limit 50 >> logs/playlist-sync.log 2>&1