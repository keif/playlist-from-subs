import re
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Set, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_FILE = 'processed_videos.json'
CACHE_TTL_DAYS = 30


def parse_duration_to_seconds(duration: str) -> int:
    """
    Parse ISO 8601 duration format (PT4M13S) to seconds.
    
    Args:
        duration: ISO 8601 duration string (e.g., "PT4M13S", "PT1H2M30S")
        
    Returns:
        Total duration in seconds
        
    Examples:
        >>> parse_duration_to_seconds("PT4M13S")
        253
        >>> parse_duration_to_seconds("PT1H2M30S") 
        3750
        >>> parse_duration_to_seconds("PT30S")
        30
    """
    if not duration or not duration.startswith('PT'):
        return 0
    
    # Remove PT prefix and extract time components
    time_part = duration[2:]
    
    # Initialize components
    hours = minutes = seconds = 0
    
    # Extract hours
    hours_match = re.search(r'(\d+)H', time_part)
    if hours_match:
        hours = int(hours_match.group(1))
    
    # Extract minutes
    minutes_match = re.search(r'(\d+)M', time_part)
    if minutes_match:
        minutes = int(minutes_match.group(1))
    
    # Extract seconds
    seconds_match = re.search(r'(\d+)S', time_part)
    if seconds_match:
        seconds = int(seconds_match.group(1))
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds


def get_published_after_timestamp(lookback_hours: int) -> str:
    """
    Get RFC 3339 timestamp for videos published after lookback period.
    
    Args:
        lookback_hours: Number of hours to look back from now
        
    Returns:
        RFC 3339 formatted timestamp string for YouTube API
    """
    published_after = datetime.utcnow() - timedelta(hours=lookback_hours)
    return published_after.strftime('%Y-%m-%dT%H:%M:%SZ')


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


class VideoCache:
    """
    Simple JSON-based cache for tracking processed video IDs.
    Includes TTL-based garbage collection to prevent unlimited growth.
    """
    
    def __init__(self, cache_file: str = CACHE_FILE, ttl_days: int = CACHE_TTL_DAYS):
        self.cache_file = Path(cache_file)
        self.ttl_days = ttl_days
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk and perform garbage collection."""
        if not self.cache_file.exists():
            self._cache = {}
            return
        
        try:
            with open(self.cache_file, 'r') as f:
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
            with open(self.cache_file, 'w') as f:
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


if __name__ == "__main__":
    # Test duration parsing
    test_cases = [
        ("PT4M13S", 253),
        ("PT1H2M30S", 3750),
        ("PT30S", 30),
        ("PT2H", 7200),
        ("PT45M", 2700),
        ("", 0),
        ("invalid", 0)
    ]
    
    print("Testing duration parsing:")
    for duration, expected in test_cases:
        result = parse_duration_to_seconds(duration)
        status = "✅" if result == expected else "❌"
        print(f"{status} {duration} -> {result}s (expected {expected}s)")
    
    # Test cache functionality
    print("\nTesting video cache:")
    cache = VideoCache('test_cache.json')
    
    cache.mark_processed('test_video_1', 'Test Video', 'Test Channel')
    print(f"✅ Marked video as processed")
    
    is_processed = cache.is_processed('test_video_1')
    print(f"{'✅' if is_processed else '❌'} Cache lookup: {is_processed}")
    
    stats = cache.get_stats()
    print(f"✅ Cache stats: {stats}")
    
    # Clean up test file
    try:
        os.unlink('test_cache.json')
    except FileNotFoundError:
        pass