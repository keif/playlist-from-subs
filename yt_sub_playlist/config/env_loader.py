"""
Environment configuration loader and video cache management.

This module handles:
- Loading and validating environment variables
- Providing configuration defaults
- Managing the video processing cache
- Logging configuration
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Set

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_FILE = 'processed_videos.json'
CACHE_TTL_DAYS = 30


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables with defaults."""
    load_dotenv()

    config = {
        "playlist_id": os.getenv("PLAYLIST_ID"),
        "playlist_name": os.getenv("PLAYLIST_NAME", "Auto Playlist from Subscriptions"),
        "playlist_visibility": os.getenv("PLAYLIST_VISIBILITY", "unlisted"),
        "min_duration_seconds": int(os.getenv("VIDEO_MIN_DURATION_SECONDS", "60")),
        "lookback_hours": int(os.getenv("LOOKBACK_HOURS", "24")),
        "channel_whitelist": parse_channel_whitelist(os.getenv("CHANNEL_ID_WHITELIST")),
        "max_videos": int(os.getenv("MAX_VIDEOS_TO_FETCH", "50")),
        "skip_live_content": os.getenv("SKIP_LIVE_CONTENT", "true").lower() in ("true", "1", "yes"),
    }

    return config


def parse_channel_whitelist(whitelist_str: Optional[str]) -> Optional[Set[str]]:
    """
    Parse comma-separated channel ID whitelist from environment variable.
    
    Args:
        whitelist_str: Comma-separated string of channel IDs, or None
        
    Returns:
        Set of channel IDs, or None if no whitelist specified
    """
    if not whitelist_str or not whitelist_str.strip():
        return None
    
    channel_ids = {
        channel_id.strip() 
        for channel_id in whitelist_str.split(',') 
        if channel_id.strip()
    }
    
    return channel_ids if channel_ids else None


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: Enable debug-level logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from Google libraries
    logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)
    logging.getLogger('google.auth').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)


class VideoCache:
    """
    Simple JSON-based cache for tracking processed video IDs.
    Includes TTL-based garbage collection to prevent unlimited growth.
    """
    
    def __init__(self, cache_file: str = None, ttl_days: int = CACHE_TTL_DAYS, data_dir: str = "data"):
        """
        Initialize video cache.
        
        Args:
            cache_file: Path to cache file (defaults to processed_videos.json in data_dir)
            ttl_days: Time-to-live for cache entries in days
            data_dir: Directory for cache storage
        """
        if cache_file is None:
            cache_file = os.path.join(data_dir, CACHE_FILE)
            
        self.cache_file = Path(cache_file)
        self.ttl_days = ttl_days
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Ensure parent directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk and perform garbage collection."""
        if not self.cache_file.exists():
            self._cache = {}
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                raw_cache = json.load(f)
            
            # Garbage collect expired entries
            cutoff = (datetime.utcnow() - timedelta(days=self.ttl_days)).isoformat()
            self._cache = {
                video_id: data
                for video_id, data in raw_cache.items()
                if data.get('added_at', '') > cutoff
            }
            
            # Save cleaned cache back if we removed items
            if len(self._cache) != len(raw_cache):
                self._save_cache()
                logger.debug(f"Garbage collected {len(raw_cache) - len(self._cache)} expired cache entries")
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to load cache file {self.cache_file}: {e}")
            logger.warning("Starting with empty cache")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
            logger.debug(f"Cache saved to {self.cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def is_processed(self, video_id: str) -> bool:
        """Check if video ID has been processed."""
        return video_id in self._cache
    
    def mark_processed(self, video_id: str, title: str = "", channel: str = "") -> None:
        """Mark video as processed with metadata."""
        self._cache[video_id] = {
            'added_at': datetime.utcnow().isoformat(),
            'title': title,
            'channel': channel
        }
        self._save_cache()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'total_processed': len(self._cache),
            'oldest_entry_days': self._get_oldest_entry_age_days()
        }
    
    def _get_oldest_entry_age_days(self) -> int:
        """Get age in days of oldest cache entry."""
        if not self._cache:
            return 0
        
        oldest_timestamp = min(
            data.get('added_at', datetime.utcnow().isoformat())
            for data in self._cache.values()
        )
        
        try:
            oldest_date = datetime.fromisoformat(oldest_timestamp.replace('Z', '+00:00'))
            age = datetime.utcnow() - oldest_date.replace(tzinfo=None)
            return age.days
        except ValueError:
            return 0