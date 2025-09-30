"""
High-level playlist management and orchestration.

This module provides the main business logic for managing YouTube playlists:
- Video fetching from subscriptions
- Intelligent filtering and deduplication
- Playlist synchronization and updates
- Reporting and analytics
"""

import csv
import logging
import os
from typing import Any, Dict, List

from .youtube_client import YouTubeClient
from .video_filtering import VideoFilter
from ..config.env_loader import VideoCache

logger = logging.getLogger(__name__)


class PlaylistManager:
    """
    High-level manager for YouTube playlist automation.

    Orchestrates the complete workflow:
    1. Fetch videos from subscriptions
    2. Apply filtering rules
    3. Sync videos to target playlist
    4. Generate reports and analytics
    """

    def __init__(self, config: Dict[str, Any], data_dir: str = "yt_sub_playlist/data"):
        """
        Initialize playlist manager.

        Args:
            config: Application configuration dictionary
            data_dir: Directory for data storage and caching
        """
        self.config = config
        self.data_dir = data_dir
        self.client = YouTubeClient(data_dir)
        self.cache = VideoCache(data_dir=data_dir)
        self.filter = VideoFilter(config, self.cache)

    def sync_subscription_videos_to_playlist(
        self,
        playlist_id: str,
        published_after: str,
        channel_whitelist: set = None,
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Main orchestration method for syncing subscription videos to playlist.

        Args:
            playlist_id: Target playlist ID
            published_after: RFC 3339 timestamp for filtering recent videos
            channel_whitelist: Set of allowed channel IDs (None = allow all)
            dry_run: If True, don't actually add videos

        Returns:
            List of video metadata dicts with 'added' field indicating success
        """
        # Step 1: Fetch recent subscription videos
        logger.info(f"Fetching videos published after {published_after}")
        videos = self.client.get_recent_uploads_from_subscriptions(
            published_after=published_after,
            max_per_channel=5
        )

        if not videos:
            logger.info("No recent subscription videos found")
            return []

        # Step 2: Filter videos based on criteria
        filtered_videos = self.filter.filter_videos(videos, channel_whitelist)

        if not filtered_videos:
            logger.info("No videos passed filters")
            return []

        # Step 3: Add videos to playlist
        return self.add_videos_to_playlist(
            playlist_id=playlist_id,
            videos=filtered_videos,
            dry_run=dry_run
        )

    def add_videos_to_playlist(
        self,
        playlist_id: str,
        videos: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Add filtered videos to the playlist and update cache.

        Args:
            playlist_id: Target playlist ID
            videos: List of videos to add
            dry_run: If True, don't actually add videos

        Returns:
            List of video metadata dicts with 'added' field indicating success
        """
        if not videos:
            logger.info("No videos to add to playlist")
            return []

        if dry_run:
            logger.info(f"DRY RUN: Would add {len(videos)} videos to playlist {playlist_id}")
            for video in videos:
                logger.info(f"  - {video['title']} ({video['video_id']})")
            # Return videos with added=True for dry run
            return [dict(video, added=True) for video in videos]

        # Add videos to playlist using the client
        video_ids = [video["video_id"] for video in videos]
        results = self.client.add_videos_to_playlist(playlist_id, video_ids)

        # Create detailed results with metadata
        detailed_results = []
        for video in videos:
            video_id = video["video_id"]
            added = results.get(video_id, False)

            # Update cache for successful additions
            if added:
                self.cache.mark_processed(
                    video_id, title=video["title"], channel=video["channel_title"]
                )
                logger.info(f"✅ Added: {video['title']}")
            else:
                logger.warning(f"❌ Failed to add: {video['title']}")

            # Add the 'added' field to the video metadata
            video_result = dict(video, added=added)
            detailed_results.append(video_result)

        return detailed_results

    def get_or_create_playlist(
        self,
        playlist_id: str = None,
        playlist_name: str = None,
        privacy_status: str = "unlisted"
    ) -> str:
        """
        Get existing playlist or create new one.

        Args:
            playlist_id: Existing playlist ID (if provided)
            playlist_name: Name for new playlist (if creating)
            privacy_status: Privacy setting for new playlist

        Returns:
            Playlist ID

        Raises:
            SystemExit: If playlist operations fail
        """
        resolved_id = self.client.get_or_create_playlist(
            playlist_id=playlist_id,
            playlist_name=playlist_name or "Auto Playlist from Subscriptions",
            privacy_status=privacy_status
        )

        if not resolved_id:
            logger.error("Failed to get or create target playlist")
            raise SystemExit(1)

        return resolved_id

    def write_report(self, video_results: List[Dict[str, Any]], report_path: str) -> None:
        """
        Write video metadata to a CSV report file.

        Args:
            video_results: List of video metadata dicts with 'added' field
            report_path: Path to write the CSV file
        """
        if not video_results:
            logger.info("No videos to report")
            return
            
        try:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'title', 'video_id', 'channel_title', 'channel_id', 
                    'published_at', 'duration_seconds', 'live_broadcast', 'added'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for video in video_results:
                    # Only write the fields we want in the CSV
                    row = {field: video.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            added_count = sum(1 for v in video_results if v.get('added', False))
            logger.info(f"Report written to {report_path} ({added_count}/{len(video_results)} videos added)")
            
        except Exception as e:
            logger.warning(f"Failed to write report to {report_path}: {e}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get video cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats()
    
    def get_filtering_stats(self) -> Dict[str, int]:
        """
        Get video filtering statistics from the last filter operation.
        
        Returns:
            Dictionary with filtering statistics
        """
        return self.filter.get_filtering_stats()