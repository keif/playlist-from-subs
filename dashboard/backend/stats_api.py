"""
Stats API Blueprint

Provides REST API endpoints for system statistics, quota usage, and filtering stats.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Create blueprint
stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

# File paths
DATA_DIR = Path(__file__).parent.parent.parent / "yt_sub_playlist" / "data"
API_CALL_LOG_FILE = DATA_DIR / "api_call_log.json"


@stats_bp.route('/quota', methods=['GET'])
def get_quota_stats():
    """
    Get API quota usage statistics.

    Returns:
        JSON response with quota usage data
    """
    try:
        if not API_CALL_LOG_FILE.exists():
            return jsonify({
                'success': True,
                'quota': {
                    'daily_used': 0,
                    'daily_limit': 10000,
                    'percentage_used': 0,
                    'remaining': 10000,
                    'calls_today': 0,
                    'reset_time': None
                },
                'message': 'No API calls logged yet',
                'timestamp': datetime.now().isoformat()
            })

        # Read API call log
        with open(API_CALL_LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        # Extract quota info
        daily_quota_used = log_data.get('daily_quota_used', 0)
        daily_quota_limit = log_data.get('daily_quota_limit', 10000)
        percentage_used = (daily_quota_used / daily_quota_limit * 100) if daily_quota_limit > 0 else 0
        remaining = max(0, daily_quota_limit - daily_quota_used)

        # Get today's calls
        today_str = datetime.now().strftime('%Y-%m-%d')
        calls = log_data.get('calls', [])
        calls_today = [c for c in calls if c.get('timestamp', '').startswith(today_str)]

        # Calculate reset time (midnight UTC)
        from datetime import timedelta
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        reset_time = datetime.combine(tomorrow, datetime.min.time()).isoformat() + 'Z'

        return jsonify({
            'success': True,
            'quota': {
                'daily_used': daily_quota_used,
                'daily_limit': daily_quota_limit,
                'percentage_used': round(percentage_used, 2),
                'remaining': remaining,
                'calls_today': len(calls_today),
                'reset_time': reset_time,
                'total_calls_logged': len(calls)
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting quota stats")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@stats_bp.route('/quota/history', methods=['GET'])
def get_quota_history():
    """
    Get quota usage history.

    Query parameters:
    - days: number of days to retrieve (default: 7)

    Returns:
        JSON response with daily quota usage
    """
    try:
        days = int(request.args.get('days', 7))

        if not API_CALL_LOG_FILE.exists():
            return jsonify({
                'success': True,
                'history': [],
                'message': 'No API calls logged yet',
                'timestamp': datetime.now().isoformat()
            })

        with open(API_CALL_LOG_FILE, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        calls = log_data.get('calls', [])

        # Group by date
        from collections import defaultdict
        daily_usage = defaultdict(int)

        for call in calls:
            timestamp = call.get('timestamp', '')
            cost = call.get('cost', 0)
            if timestamp:
                date = timestamp.split('T')[0]
                daily_usage[date] += cost

        # Convert to list and sort
        history = [
            {'date': date, 'quota_used': usage}
            for date, usage in sorted(daily_usage.items(), reverse=True)[:days]
        ]

        return jsonify({
            'success': True,
            'history': history,
            'days': days,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting quota history")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@stats_bp.route('/cache', methods=['GET'])
def get_cache_stats():
    """
    Get video cache statistics.

    Returns:
        JSON response with cache stats
    """
    try:
        from yt_sub_playlist.config.env_loader import VideoCache

        cache = VideoCache()
        stats = cache.get_stats()

        return jsonify({
            'success': True,
            'cache': {
                'total_videos': stats['total_processed'],
                'oldest_entry_age_days': stats['oldest_entry_days'],
                'cache_file': str(cache.cache_file),
                'cache_exists': cache.cache_file.exists()
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting cache stats")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@stats_bp.route('/filters', methods=['GET'])
def get_filter_stats():
    """
    Get filtering statistics from last run.

    This would require storing filter stats somewhere after each run.
    For now, returns a placeholder indicating this feature needs implementation.

    Returns:
        JSON response with filter statistics
    """
    try:
        # TODO: Implement filter stats persistence
        # For now, return placeholder data

        return jsonify({
            'success': True,
            'filters': {
                'available': False,
                'message': 'Filter statistics are not yet persisted. Run the CLI tool to generate stats.'
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting filter stats")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@stats_bp.route('/system', methods=['GET'])
def get_system_stats():
    """
    Get overall system statistics.

    Returns:
        JSON response with comprehensive system stats
    """
    try:
        # Get quota stats
        quota_info = {'available': False}
        if API_CALL_LOG_FILE.exists():
            try:
                with open(API_CALL_LOG_FILE, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                quota_info = {
                    'available': True,
                    'daily_used': log_data.get('daily_quota_used', 0),
                    'daily_limit': log_data.get('daily_quota_limit', 10000)
                }
            except:
                pass

        # Get cache stats
        cache_info = {'available': False}
        try:
            from yt_sub_playlist.config.env_loader import VideoCache
            cache = VideoCache()
            stats = cache.get_stats()
            cache_info = {
                'available': True,
                'total_videos': stats['total_processed'],
                'oldest_entry_age_days': stats['oldest_entry_days']
            }
        except:
            pass

        # Get config info
        config_info = {'available': False}
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_config()
            config_info = {
                'available': True,
                'min_duration_seconds': config['min_duration_seconds'],
                'lookback_hours': config['lookback_hours'],
                'max_videos': config['max_videos'],
                'whitelist_enabled': config['channel_whitelist'] is not None
            }
        except:
            pass

        return jsonify({
            'success': True,
            'system': {
                'quota': quota_info,
                'cache': cache_info,
                'config': config_info
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting system stats")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
