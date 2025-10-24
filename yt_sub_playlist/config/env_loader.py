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

# Config file path
CONFIG_JSON_PATH = Path("config.json")


def load_config_json() -> Dict[str, Any]:
    """
    Load user preferences from config.json file.

    Returns:
        Dictionary with config values, or empty dict if file doesn't exist
    """
    if not CONFIG_JSON_PATH.exists():
        logger.debug("config.json not found, using defaults and environment variables")
        return {}

    try:
        with open(CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
            json_config = json.load(f)
        logger.debug(f"Loaded configuration from {CONFIG_JSON_PATH}")
        return json_config
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load {CONFIG_JSON_PATH}: {e}")
        return {}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from multiple sources with precedence:
    1. Environment variables (.env) - highest priority
    2. Configuration file (config.json)
    3. Hardcoded defaults - lowest priority

    Note: CLI arguments override all of these and are handled in __main__.py
    """
    load_dotenv()

    # Load config.json preferences
    json_config = load_config_json()

    # Define defaults
    defaults = {
        "playlist_name": "Auto Playlist from Subscriptions",
        "playlist_visibility": "unlisted",
        "min_duration_seconds": 60,
        "lookback_hours": 24,
        "max_videos": 50,
        "skip_live_content": True,
        "channel_whitelist": None,  # Legacy
        "channel_filter_mode": "none",
        "channel_allowlist": None,
        "channel_blocklist": None,
    }

    # Build config with precedence: .env > config.json > defaults
    # Note: playlist_id is only from .env (not in config.json)
    config = {
        "playlist_id": os.getenv("PLAYLIST_ID"),
        "playlist_name": os.getenv("PLAYLIST_NAME") or json_config.get("playlist_name", defaults["playlist_name"]),
        "playlist_visibility": os.getenv("PLAYLIST_VISIBILITY") or json_config.get("playlist_visibility", defaults["playlist_visibility"]),
        "min_duration_seconds": int(os.getenv("VIDEO_MIN_DURATION_SECONDS") or json_config.get("min_duration_seconds", defaults["min_duration_seconds"])),
        "lookback_hours": int(os.getenv("LOOKBACK_HOURS") or json_config.get("lookback_hours", defaults["lookback_hours"])),
        "max_videos": int(os.getenv("MAX_VIDEOS_TO_FETCH") or json_config.get("max_videos", defaults["max_videos"])),
        "skip_live_content": _parse_bool(os.getenv("SKIP_LIVE_CONTENT"), json_config.get("skip_live_content", defaults["skip_live_content"])),
        "channel_whitelist": _merge_channel_whitelist(
            os.getenv("CHANNEL_ID_WHITELIST"),
            json_config.get("channel_whitelist")
        ),
        "channel_filter_mode": os.getenv("CHANNEL_FILTER_MODE") or json_config.get("channel_filter_mode", defaults["channel_filter_mode"]),
        "channel_allowlist": _merge_channel_list(
            os.getenv("CHANNEL_ALLOWLIST"),
            json_config.get("channel_allowlist")
        ),
        "channel_blocklist": _merge_channel_list(
            os.getenv("CHANNEL_BLOCKLIST"),
            json_config.get("channel_blocklist")
        ),
    }

    # Migrate legacy whitelist to new system if needed
    config = _migrate_legacy_channel_filter(config)

    return config


def _parse_bool(env_value: Optional[str], json_value: Any) -> bool:
    """
    Parse boolean from environment variable or JSON config.
    Environment variable takes precedence if set.
    """
    if env_value is not None:
        return env_value.lower() in ("true", "1", "yes")
    if isinstance(json_value, bool):
        return json_value
    return False


def _merge_channel_whitelist(env_whitelist: Optional[str], json_whitelist: Optional[Any]) -> Optional[Set[str]]:
    """
    Merge channel whitelist from .env and config.json.
    Environment variable (.env) takes precedence if set.

    Args:
        env_whitelist: Comma-separated channel IDs from .env
        json_whitelist: List of channel IDs from config.json

    Returns:
        Set of channel IDs, or None if no whitelist specified
    """
    # .env takes precedence
    if env_whitelist:
        return parse_channel_whitelist(env_whitelist)

    # Fall back to config.json
    if json_whitelist and isinstance(json_whitelist, list):
        channel_ids = {ch_id for ch_id in json_whitelist if ch_id}
        return channel_ids if channel_ids else None

    return None


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


def _merge_channel_list(env_list: Optional[str], json_list: Optional[Any]) -> Optional[Set[str]]:
    """
    Merge channel list from .env and config.json.
    Environment variable (.env) takes precedence if set.

    Args:
        env_list: Comma-separated channel IDs from .env
        json_list: List of channel IDs from config.json

    Returns:
        Set of channel IDs, or None if no list specified
    """
    # .env takes precedence
    if env_list:
        return parse_channel_whitelist(env_list)

    # Fall back to config.json
    if json_list and isinstance(json_list, list):
        channel_ids = {ch_id for ch_id in json_list if ch_id}
        return channel_ids if channel_ids else None

    return None


def _migrate_legacy_channel_filter(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy channel_whitelist to new allowlist/blocklist system.

    If channel_whitelist is set but new system is not configured,
    migrate to allowlist mode automatically.

    Args:
        config: Configuration dictionary

    Returns:
        Updated configuration with migration applied
    """
    # If new system is already configured, skip migration
    if config.get("channel_filter_mode") != "none":
        return config

    if config.get("channel_allowlist") or config.get("channel_blocklist"):
        return config

    # Check for legacy whitelist
    legacy_whitelist = config.get("channel_whitelist")
    if legacy_whitelist:
        logger.info("Migrating legacy channel_whitelist to channel_allowlist")
        config["channel_filter_mode"] = "allowlist"
        config["channel_allowlist"] = legacy_whitelist
        # Keep legacy field for backward compatibility

    return config


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