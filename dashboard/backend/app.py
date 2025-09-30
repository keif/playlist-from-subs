"""
YouTube Playlist Dashboard Backend

A Flask web server that provides REST API endpoints for the playlist dashboard.
Integrates with the existing yt_sub_playlist CLI tool for data generation.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Add the parent directory to Python path to import yt_sub_playlist
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from yt_sub_playlist.core.playlist_manager import PlaylistManager
    from yt_sub_playlist.config.env_loader import load_config
    CLI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import yt_sub_playlist modules: {e}")
    print("API will work with static data only")
    CLI_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend development

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DASHBOARD_DIR = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent.parent.parent / "yt_sub_playlist" / "data"
REPORTS_DIR = Path(__file__).parent.parent.parent / "yt_sub_playlist" / "reports"

class PlaylistAPI:
    """API controller for playlist operations."""
    
    def __init__(self):
        self.last_refresh = None
        self.cache_duration_minutes = 30
    
    def get_playlist_data(self) -> List[Dict[str, Any]]:
        """
        Get playlist data from multiple sources in priority order:
        1. Recent CSV report (most complete data)
        2. Generated dashboard JSON
        3. Static sample data
        """
        # Try CSV report first (most recent from CLI runs)
        csv_data = self._load_from_csv_report()
        if csv_data:
            logger.info("Loaded playlist from CSV report")
            return csv_data
        
        # Try dashboard JSON data
        json_data = self._load_from_json()
        if json_data:
            logger.info("Loaded playlist from JSON data")
            return json_data
            
        # Fallback to sample data
        logger.info("Using sample data - no real playlist data found")
        return self._load_sample_data()
    
    def _load_from_csv_report(self) -> Optional[List[Dict[str, Any]]]:
        """Load data from the most recent CSV report."""
        try:
            csv_files = list(REPORTS_DIR.glob("*.csv"))
            if not csv_files:
                return None
                
            # Get the most recent CSV file
            latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
            
            # Check if file is recent (within last 24 hours)
            file_age_hours = (datetime.now().timestamp() - latest_csv.stat().st_mtime) / 3600
            if file_age_hours > 24:
                logger.info(f"CSV report is {file_age_hours:.1f} hours old, skipping")
                return None
            
            return self._parse_csv_to_playlist(latest_csv)
            
        except Exception as e:
            logger.error(f"Error loading CSV report: {e}")
            return None
    
    def _parse_csv_to_playlist(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Parse CSV report into playlist format."""
        import csv
        
        playlist = []
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
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
        
        return playlist
    
    def _load_from_json(self) -> Optional[List[Dict[str, Any]]]:
        """Load data from processed videos or cache files."""
        # Try the processed videos file
        processed_file = DATA_DIR / "processed_videos.json"
        if processed_file.exists():
            try:
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                    # This might be in a different format, adapt as needed
                    if isinstance(data, dict) and 'videos' in data:
                        return data['videos']
                    elif isinstance(data, list):
                        return data
            except Exception as e:
                logger.error(f"Error loading processed videos: {e}")
        
        return None
    
    def _load_sample_data(self) -> List[Dict[str, Any]]:
        """Load sample data as fallback."""
        sample_file = DASHBOARD_DIR / "playlist.json"
        try:
            with open(sample_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            return []
    
    def refresh_playlist(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Generate fresh playlist data using the CLI tool.
        
        Args:
            dry_run: If True, run CLI in dry-run mode
            
        Returns:
            Dict with refresh status and metadata
        """
        if not CLI_AVAILABLE:
            return {
                'success': False,
                'error': 'CLI tool not available - yt_sub_playlist modules not found',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Run the CLI tool with report generation
            cmd = [
                sys.executable, '-m', 'yt_sub_playlist',
                '--report', str(REPORTS_DIR / f"dashboard_refresh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            ]
            
            if dry_run:
                cmd.append('--dry-run')
            
            logger.info(f"Running CLI command: {' '.join(cmd)}")
            
            # Change to project root directory
            project_root = Path(__file__).parent.parent.parent
            result = subprocess.run(
                cmd, 
                cwd=project_root,
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            self.last_refresh = datetime.now()
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Playlist refreshed successfully',
                    'timestamp': self.last_refresh.isoformat(),
                    'dry_run': dry_run,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                logger.error(f"CLI command failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
                return {
                    'success': False,
                    'error': f'CLI command failed: {result.stderr}',
                    'timestamp': datetime.now().isoformat(),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'CLI command timed out after 5 minutes',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.exception("Error running CLI tool")
            return {
                'success': False,
                'error': f'Error running CLI tool: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and configuration info."""
        return {
            'cli_available': CLI_AVAILABLE,
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
            'data_sources': {
                'reports_dir_exists': REPORTS_DIR.exists(),
                'reports_dir': str(REPORTS_DIR),
                'data_dir_exists': DATA_DIR.exists(),
                'data_dir': str(DATA_DIR),
                'recent_csv_count': len(list(REPORTS_DIR.glob("*.csv"))) if REPORTS_DIR.exists() else 0
            },
            'timestamp': datetime.now().isoformat()
        }

# Initialize API controller
api = PlaylistAPI()

# Routes
@app.route('/')
def index():
    """Serve the dashboard HTML."""
    return send_from_directory(DASHBOARD_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory(DASHBOARD_DIR, filename)

@app.route('/api/playlist', methods=['GET'])
def get_playlist():
    """Get current playlist data."""
    try:
        playlist_data = api.get_playlist_data()
        return jsonify({
            'success': True,
            'data': playlist_data,
            'count': len(playlist_data),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.exception("Error getting playlist data")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_playlist():
    """Refresh playlist data by running the CLI tool."""
    try:
        # Get optional dry_run parameter
        dry_run = request.json.get('dry_run', False) if request.is_json else False
        
        result = api.refresh_playlist(dry_run=dry_run)
        status_code = 200 if result['success'] else 500
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.exception("Error refreshing playlist")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status and health check."""
    try:
        status = api.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.exception("Error getting system status")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Ensure required directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Log startup info
    logger.info("=== YouTube Playlist Dashboard Backend ===")
    logger.info(f"CLI Available: {CLI_AVAILABLE}")
    logger.info(f"Data Directory: {DATA_DIR}")
    logger.info(f"Reports Directory: {REPORTS_DIR}")
    logger.info(f"Dashboard Directory: {DASHBOARD_DIR}")
    
    # Start the Flask development server
    app.run(
        host='127.0.0.1',
        port=5001,  # Changed from 5000 to avoid macOS AirPlay conflict
        debug=True,
        use_reloader=True
    )