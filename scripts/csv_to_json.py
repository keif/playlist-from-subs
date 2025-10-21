#!/usr/bin/env python3
"""
Convert CSV report to JSON format for dashboard.
Usage: python scripts/csv_to_json.py input.csv output.json
"""

import csv
import json
import sys
from pathlib import Path

def csv_to_playlist_json(csv_path: str, json_path: str = None) -> str:
    """Convert CSV report to playlist JSON format."""
    
    if json_path is None:
        json_path = csv_path.replace('.csv', '.json')
    
    playlist = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                video = {
                    'title': row.get('title', ''),
                    'video_id': row.get('video_id', ''),
                    'channel_title': row.get('channel_title', ''),
                    'channel_id': row.get('channel_id', ''),
                    'published_at': row.get('published_at', ''),
                    'duration_seconds': int(row.get('duration_seconds', 0)) if row.get('duration_seconds') else 0,
                    'live_broadcast': row.get('live_broadcast', 'none'),
                    'added': row.get('added', '').lower() in ('true', '1', 'yes')
                }
                playlist.append(video)
        
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(playlist, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"✅ Converted {len(playlist)} videos from {csv_path} to {json_path}")
        return json_path
        
    except Exception as e:
        print(f"❌ Error converting {csv_path}: {e}")
        return None

def main():
    """Main conversion function."""
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json.py input.csv [output.json]")
        print("Example: python csv_to_json.py yt_sub_playlist/reports/latest.csv dashboard/playlist.json")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    json_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    result = csv_to_playlist_json(csv_path, json_path)
    if result:
        print(f"🎉 Conversion complete: {result}")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()