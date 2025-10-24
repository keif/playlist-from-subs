"""
Video filtering and processing utilities.

This module handles filtering videos based on various criteria:
- Duration thresholds
- Channel allowlists and blocklists
- Live content detection
- Duplicate processing tracking
- Custom filtering rules
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ..config.env_loader import VideoCache

logger = logging.getLogger(__name__)


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


class VideoFilter:
    """
    Comprehensive video filtering system.
    
    Filters videos based on configurable criteria including:
    - Minimum duration requirements
    - Channel whitelist restrictions
    - Live content filtering
    - Duplicate processing prevention
    """
    
    def __init__(self, config: Dict[str, Any], cache: VideoCache):
        """
        Initialize video filter with configuration and cache.
        
        Args:
            config: Configuration dictionary with filtering settings
            cache: VideoCache instance for tracking processed videos
        """
        self.config = config
        self.cache = cache
        self.stats = self._init_stats()
    
    def _init_stats(self) -> Dict[str, int]:
        """Initialize filtering statistics."""
        return {
            "total": 0,
            "too_short": 0,
            "not_whitelisted": 0,  # Legacy stat name
            "not_in_allowlist": 0,
            "in_blocklist": 0,
            "already_processed": 0,
            "live_content_skipped": 0,
            "passed_filters": 0,
        }
    
    def filter_videos(
        self,
        videos: List[Dict[str, Any]],
        channel_whitelist: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter videos based on all configured criteria.

        Args:
            videos: List of video data from YouTube API
            channel_whitelist: Set of allowed channel IDs (None = allow all) - LEGACY parameter

        Returns:
            Filtered list of videos that should be added to playlist
        """
        self.stats = self._init_stats()
        self.stats["total"] = len(videos)

        filtered = []
        min_duration = self.config["min_duration_seconds"]

        # Get filter mode and lists from config
        filter_mode = self.config.get("channel_filter_mode", "none")
        allowlist = self.config.get("channel_allowlist")
        blocklist = self.config.get("channel_blocklist")

        # Use legacy whitelist if new system not configured
        if filter_mode == "none" and channel_whitelist:
            filter_mode = "allowlist"
            allowlist = channel_whitelist

        for video in videos:
            if not self._should_include_video(video, filter_mode, allowlist, blocklist, min_duration):
                continue

            # Video passed all filters
            self.stats["passed_filters"] += 1
            filtered.append(video)

            title = video["title"]
            duration = video["duration_seconds"]
            channel_title = video["channel_title"]
            logger.info(f"✓ {title} ({duration}s) by {channel_title}")

        self._log_filtering_stats(filter_mode, allowlist, blocklist, min_duration)
        return filtered
    
    def _should_include_video(
        self,
        video: Dict[str, Any],
        filter_mode: str,
        allowlist: Optional[Set[str]],
        blocklist: Optional[Set[str]],
        min_duration: int
    ) -> bool:
        """
        Check if a video should be included based on all filters.

        Args:
            video: Video data dictionary
            filter_mode: Channel filter mode ("none", "allowlist", "blocklist")
            allowlist: Set of allowed channel IDs (for allowlist mode)
            blocklist: Set of blocked channel IDs (for blocklist mode)
            min_duration: Minimum duration in seconds

        Returns:
            True if video passes all filters, False otherwise
        """
        video_id = video["video_id"]
        title = video["title"]
        channel_id = video["channel_id"]
        channel_title = video["channel_title"]
        duration = video["duration_seconds"]

        # Check if already processed
        if self.cache.is_processed(video_id):
            logger.debug(f"Skipping already processed: {title}")
            self.stats["already_processed"] += 1
            return False

        # Check duration filter
        if duration < min_duration:
            logger.debug(f"Skipping too short ({duration}s): {title}")
            self.stats["too_short"] += 1
            return False

        # Check channel filtering
        if filter_mode == "allowlist" and allowlist:
            if channel_id not in allowlist:
                logger.debug(f"Skipping channel not in allowlist {channel_title}: {title}")
                self.stats["not_in_allowlist"] += 1
                self.stats["not_whitelisted"] += 1  # Legacy stat
                return False

        elif filter_mode == "blocklist" and blocklist:
            if channel_id in blocklist:
                logger.debug(f"Skipping blocked channel {channel_title}: {title}")
                self.stats["in_blocklist"] += 1
                return False

        # Check live content filter
        if self.config["skip_live_content"]:
            live_broadcast = video.get("live_broadcast", "none")
            if live_broadcast != "none":
                live_type = "livestream" if live_broadcast == "live" else "premiere"
                logger.info(f"Skipping {live_type}: {title}")
                self.stats["live_content_skipped"] += 1
                return False

        return True
    
    def _log_filtering_stats(
        self,
        filter_mode: str,
        allowlist: Optional[Set[str]],
        blocklist: Optional[Set[str]],
        min_duration: int
    ) -> None:
        """Log comprehensive filtering statistics."""
        logger.info(f"Video filtering stats:")
        logger.info(f"  Total videos: {self.stats['total']}")
        logger.info(f"  Already processed: {self.stats['already_processed']}")
        logger.info(f"  Too short (<{min_duration}s): {self.stats['too_short']}")

        if filter_mode == "allowlist" and allowlist:
            logger.info(f"  Not in allowlist: {self.stats['not_in_allowlist']}")
        elif filter_mode == "blocklist" and blocklist:
            logger.info(f"  Blocked channels: {self.stats['in_blocklist']}")

        if self.config["skip_live_content"]:
            logger.info(f"  Live content skipped: {self.stats['live_content_skipped']}")

        logger.info(f"  Passed filters: {self.stats['passed_filters']}")
    
    def get_filtering_stats(self) -> Dict[str, int]:
        """
        Get the current filtering statistics.
        
        Returns:
            Dictionary of filtering statistics
        """
        return self.stats.copy()


# Legacy function for backward compatibility
def filter_videos(
    videos: List[Dict[str, Any]],
    config: Dict[str, Any],
    cache: VideoCache,
    channel_whitelist: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Legacy filter function for backward compatibility.
    
    This function maintains compatibility with existing code while
    using the new VideoFilter class internally.
    """
    filter_instance = VideoFilter(config, cache)
    return filter_instance.filter_videos(videos, channel_whitelist)