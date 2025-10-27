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
            "too_long": 0,
            "outside_date_range": 0,
            "keyword_filtered_include": 0,
            "keyword_filtered_exclude": 0,
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
        max_duration = self.config.get("max_duration_seconds")

        # Get filter mode and lists from config
        filter_mode = self.config.get("channel_filter_mode", "none")
        allowlist = self.config.get("channel_allowlist")
        blocklist = self.config.get("channel_blocklist")

        # Use legacy whitelist if new system not configured
        if filter_mode == "none" and channel_whitelist:
            filter_mode = "allowlist"
            allowlist = channel_whitelist

        for video in videos:
            if not self._should_include_video(video, filter_mode, allowlist, blocklist, min_duration, max_duration):
                continue

            # Video passed all filters
            self.stats["passed_filters"] += 1
            filtered.append(video)

            title = video["title"]
            duration = video["duration_seconds"]
            channel_title = video["channel_title"]
            logger.info(f"✓ {title} ({duration}s) by {channel_title}")

        self._log_filtering_stats(filter_mode, allowlist, blocklist, min_duration, max_duration)
        return filtered
    
    def _should_include_video(
        self,
        video: Dict[str, Any],
        filter_mode: str,
        allowlist: Optional[Set[str]],
        blocklist: Optional[Set[str]],
        min_duration: int,
        max_duration: Optional[int] = None
    ) -> bool:
        """
        Check if a video should be included based on all filters.

        Args:
            video: Video data dictionary
            filter_mode: Channel filter mode ("none", "allowlist", "blocklist")
            allowlist: Set of allowed channel IDs (for allowlist mode)
            blocklist: Set of blocked channel IDs (for blocklist mode)
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds (None = unlimited)

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

        # Check duration filters
        if duration < min_duration:
            logger.debug(f"Skipping too short ({duration}s): {title}")
            self.stats["too_short"] += 1
            return False

        if max_duration and duration > max_duration:
            logger.debug(f"Skipping too long ({duration}s): {title}")
            self.stats["too_long"] += 1
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

        # Check date filter
        if not self._check_date_filter(video):
            logger.debug(f"Skipping outside date range: {title}")
            self.stats["outside_date_range"] += 1
            return False

        # Check keyword filter
        keyword_result = self._check_keyword_filter(video)
        if keyword_result == "filtered_include":
            logger.debug(f"Skipping (not in include keywords): {title}")
            self.stats["keyword_filtered_include"] += 1
            return False
        elif keyword_result == "filtered_exclude":
            logger.debug(f"Skipping (matches exclude keywords): {title}")
            self.stats["keyword_filtered_exclude"] += 1
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

    def _check_date_filter(self, video: Dict[str, Any]) -> bool:
        """
        Check if video passes date filter criteria.

        Args:
            video: Video data dictionary with published_at field

        Returns:
            True if video passes date filter, False otherwise
        """
        date_mode = self.config.get("date_filter_mode", "lookback")

        # Get video published date (assumed to be in ISO format from YouTube API)
        published_at_str = video.get("published_at")
        if not published_at_str:
            # If no published date, allow video through (shouldn't happen with YouTube API)
            return True

        # Parse published date
        try:
            # Handle both RFC 3339 format (with Z) and ISO format
            if published_at_str.endswith('Z'):
                published_at = datetime.strptime(published_at_str, '%Y-%m-%dT%H:%M:%SZ')
            else:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Could not parse published_at date: {published_at_str}")
            return True

        now = datetime.utcnow()

        if date_mode == "lookback":
            # Use lookback_hours (default behavior)
            lookback_hours = self.config.get("lookback_hours", 24)
            cutoff = now - timedelta(hours=lookback_hours)
            return published_at >= cutoff

        elif date_mode == "days":
            # Use date_filter_days (last N days)
            days = self.config.get("date_filter_days", 7)
            cutoff = now - timedelta(days=days)
            # Set cutoff to start of day
            cutoff = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
            return published_at >= cutoff

        elif date_mode == "date_range":
            # Use date_filter_start and date_filter_end
            start_str = self.config.get("date_filter_start")
            end_str = self.config.get("date_filter_end")

            if not start_str or not end_str:
                # Missing date range, allow through (shouldn't happen with validation)
                return True

            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                # Set end_date to end of day (23:59:59)
                end_date = end_date.replace(hour=23, minute=59, second=59)

                return start_date <= published_at <= end_date
            except ValueError:
                logger.warning(f"Could not parse date range: {start_str} to {end_str}")
                return True

        # Unknown mode, allow through
        return True

    def _check_keyword_filter(self, video: Dict[str, Any]) -> Optional[str]:
        """
        Check if video passes keyword filter criteria.

        Args:
            video: Video data dictionary with title and description fields

        Returns:
            None if passes filter
            "filtered_include" if doesn't match include keywords
            "filtered_exclude" if matches exclude keywords
        """
        mode = self.config.get("keyword_filter_mode", "none")

        if mode == "none":
            return None

        # Get search fields
        title = video.get("title", "")
        description = video.get("description", "")
        search_description = self.config.get("keyword_search_description", False)

        # Build search text
        search_text = title
        if search_description and description:
            search_text = f"{title} {description}"

        # Handle case sensitivity
        case_sensitive = self.config.get("keyword_case_sensitive", False)
        if not case_sensitive:
            search_text = search_text.lower()

        # Get keyword lists
        include_list = self.config.get("keyword_include", [])
        exclude_list = self.config.get("keyword_exclude", [])
        match_type = self.config.get("keyword_match_type", "any")

        # Check include filter
        if mode in ["include", "both"]:
            if not include_list:
                # No include list, pass through
                pass
            else:
                # Check if any/all keywords match
                keywords_to_check = [k if case_sensitive else k.lower() for k in include_list]

                if match_type == "any":
                    # At least one keyword must match
                    if not any(keyword in search_text for keyword in keywords_to_check):
                        return "filtered_include"
                else:  # match_type == "all"
                    # All keywords must match
                    if not all(keyword in search_text for keyword in keywords_to_check):
                        return "filtered_include"

        # Check exclude filter
        if mode in ["exclude", "both"]:
            if exclude_list:
                keywords_to_check = [k if case_sensitive else k.lower() for k in exclude_list]

                # If any exclude keyword matches, filter out
                if any(keyword in search_text for keyword in keywords_to_check):
                    return "filtered_exclude"

        return None

    def _log_filtering_stats(
        self,
        filter_mode: str,
        allowlist: Optional[Set[str]],
        blocklist: Optional[Set[str]],
        min_duration: int,
        max_duration: Optional[int] = None
    ) -> None:
        """Log comprehensive filtering statistics."""
        logger.info(f"Video filtering stats:")
        logger.info(f"  Total videos: {self.stats['total']}")
        logger.info(f"  Already processed: {self.stats['already_processed']}")

        # Duration filtering stats
        if max_duration:
            logger.info(f"  Too short (<{min_duration}s): {self.stats['too_short']}")
            logger.info(f"  Too long (>{max_duration}s): {self.stats['too_long']}")
        else:
            logger.info(f"  Too short (<{min_duration}s): {self.stats['too_short']}")

        # Date filtering stats
        if self.stats['outside_date_range'] > 0:
            date_mode = self.config.get("date_filter_mode", "lookback")
            logger.info(f"  Outside date range ({date_mode} mode): {self.stats['outside_date_range']}")

        # Keyword filtering stats
        if self.stats['keyword_filtered_include'] > 0:
            logger.info(f"  Keyword filtered (include): {self.stats['keyword_filtered_include']}")
        if self.stats['keyword_filtered_exclude'] > 0:
            logger.info(f"  Keyword filtered (exclude): {self.stats['keyword_filtered_exclude']}")

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