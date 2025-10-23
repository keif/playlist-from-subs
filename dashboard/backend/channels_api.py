"""
Channels API Blueprint

Provides REST API endpoints for channel management and whitelist control.
"""

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
channels_bp = Blueprint('channels', __name__, url_prefix='/api/channels')

# Try to import YouTube client
try:
    from yt_sub_playlist.core.youtube_client import YouTubeClient
    from yt_sub_playlist.config.env_loader import load_config as load_env_config
    YOUTUBE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"YouTube client not available: {e}")
    YOUTUBE_AVAILABLE = False


def get_youtube_client():
    """Get YouTube client instance if available."""
    if not YOUTUBE_AVAILABLE:
        return None

    try:
        # Load config to get credentials path
        config = load_env_config()
        client = YouTubeClient()
        return client
    except Exception as e:
        logger.error(f"Error creating YouTube client: {e}")
        return None


@channels_bp.route('', methods=['GET'])
def get_channels():
    """
    Get list of subscribed channels.

    Returns:
        JSON response with list of channels
    """
    try:
        client = get_youtube_client()

        if not client:
            return jsonify({
                'success': False,
                'error': 'YouTube API not available',
                'channels': [],
                'timestamp': datetime.now().isoformat()
            }), 503

        # Get subscriptions
        subscriptions = client.get_all_subscriptions()

        # Format channel data
        channels = []
        for sub in subscriptions:
            channel_info = {
                'channel_id': sub['channel_id'],
                'channel_title': sub['channel_title'],
                'description': sub.get('description', ''),
                'thumbnail': sub.get('thumbnail', ''),
                'subscriber_count': sub.get('subscriber_count'),
                'video_count': sub.get('video_count')
            }
            channels.append(channel_info)

        # Sort by channel title
        channels.sort(key=lambda x: x['channel_title'].lower())

        return jsonify({
            'success': True,
            'channels': channels,
            'count': len(channels),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting channels")
        return jsonify({
            'success': False,
            'error': str(e),
            'channels': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@channels_bp.route('/whitelisted', methods=['GET'])
def get_whitelisted_channels():
    """
    Get current channel whitelist from config.

    Returns:
        JSON response with whitelisted channel IDs
    """
    try:
        from config_manager import ConfigManager

        config_manager = ConfigManager()
        config = config_manager.load_config()

        whitelist = config.get('channel_whitelist', None)

        return jsonify({
            'success': True,
            'enabled': whitelist is not None,
            'channel_ids': whitelist if whitelist else [],
            'count': len(whitelist) if whitelist else 0,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error getting whitelist")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@channels_bp.route('/whitelist', methods=['PUT'])
def update_whitelist():
    """
    Update channel whitelist.

    Expects JSON body with:
    - enabled: boolean (enable/disable whitelist)
    - channel_ids: list of channel IDs (if enabled)

    Returns:
        JSON response with success status
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400

        data = request.get_json()
        enabled = data.get('enabled', False)
        channel_ids = data.get('channel_ids', [])

        # Validate channel_ids is a list
        if not isinstance(channel_ids, list):
            return jsonify({
                'success': False,
                'error': 'channel_ids must be a list'
            }), 400

        from config_manager import ConfigManager

        config_manager = ConfigManager()

        # Update config
        whitelist_value = channel_ids if enabled and channel_ids else None

        result = config_manager.update_config({
            'channel_whitelist': whitelist_value
        })

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Whitelist updated successfully',
                'enabled': whitelist_value is not None,
                'count': len(whitelist_value) if whitelist_value else 0,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'errors': result['errors'],
                'timestamp': datetime.now().isoformat()
            }), 400

    except Exception as e:
        logger.exception("Error updating whitelist")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@channels_bp.route('/search', methods=['GET'])
def search_channels():
    """
    Search subscribed channels by name.

    Query parameters:
    - q: search query

    Returns:
        JSON response with matching channels
    """
    try:
        query = request.args.get('q', '').lower()

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        client = get_youtube_client()

        if not client:
            return jsonify({
                'success': False,
                'error': 'YouTube API not available',
                'channels': []
            }), 503

        # Get all subscriptions
        subscriptions = client.get_all_subscriptions()

        # Filter by query
        matching = [
            {
                'channel_id': sub['channel_id'],
                'channel_title': sub['channel_title'],
                'description': sub.get('description', ''),
                'thumbnail': sub.get('thumbnail', '')
            }
            for sub in subscriptions
            if query in sub['channel_title'].lower() or query in sub.get('description', '').lower()
        ]

        return jsonify({
            'success': True,
            'channels': matching,
            'count': len(matching),
            'query': query,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error searching channels")
        return jsonify({
            'success': False,
            'error': str(e),
            'channels': [],
            'timestamp': datetime.now().isoformat()
        }), 500
