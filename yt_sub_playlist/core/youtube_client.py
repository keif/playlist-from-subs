"""
YouTube Data API v3 client wrapper.

This module provides a high-level interface to the YouTube Data API v3,
with features specifically designed for playlist automation:

- Quota-optimized batched operations
- Intelligent caching and duplicate detection  
- Robust error handling and retry logic
- Subscription and video management
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

from googleapiclient.errors import HttpError

from ..auth.oauth import get_authenticated_service

logger = logging.getLogger(__name__)


def parse_duration_to_seconds(duration: str) -> int:
    """
    Parse ISO 8601 duration format (PT4M13S) to seconds.
    
    Args:
        duration: ISO 8601 duration string (e.g., "PT4M13S", "PT1H2M30S")
        
    Returns:
        Total duration in seconds
    """
    import re
    
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


class YouTubeClient:
    """
    Wrapper for YouTube Data API v3 with methods specific to playlist automation.
    
    Features:
    - Quota-optimized operations with batching
    - Intelligent duplicate detection and caching
    - Robust error handling with retry logic
    - Subscription and playlist management
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize YouTube API client.
        
        Args:
            data_dir: Directory for storing cache files and data
        """
        self.service = get_authenticated_service()
        self.quota_exceeded = False
        self.data_dir = data_dir
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "playlist_cache"), exist_ok=True)

    def fetch_existing_playlist_items(self, playlist_id: str) -> Set[str]:
        """
        Fetch all existing video IDs from a playlist with disk-based caching.
        
        Uses disk cache with 12-hour TTL to avoid repeated API calls.
        Supports pagination for playlists with >50 videos.
        
        Args:
            playlist_id: Target playlist ID to check for existing videos
            
        Returns:
            Set of video IDs currently in the playlist
        """
        cache_file = os.path.join(
            self.data_dir, "playlist_cache", f"existing_playlist_items_{playlist_id}.json"
        )
        cache_ttl_hours = 12
        
        # Check if cache exists and is still valid
        if os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_ttl_hours * 3600:  # Convert hours to seconds
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        video_ids = set(cached_data.get('video_ids', []))
                        logger.info(f"Using cached playlist items ({len(video_ids)} videos, {cache_age/3600:.1f}h old)")
                        return video_ids
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to read playlist cache: {e}")
                # Continue to fresh fetch
        
        # Fetch fresh data from API
        logger.info(f"Fetching existing playlist items for {playlist_id}")
        video_ids = set()
        next_page_token = None
        page_count = 0
        
        try:
            while True:
                page_count += 1
                request = self.service.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Extract video IDs from this page
                for item in response.get('items', []):
                    content_details = item.get('contentDetails', {})
                    video_id = content_details.get('videoId')
                    if video_id:
                        video_ids.add(video_id)
                
                # Check for more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
                # Safety check to avoid infinite loops
                if page_count > 100:  # Max 5000 videos
                    logger.warning(f"Reached page limit fetching playlist items")
                    break
            
            logger.info(f"Fetched {len(video_ids)} existing videos from playlist ({page_count} API pages)")
            
            # Cache the results
            try:
                cache_data = {
                    'video_ids': list(video_ids),
                    'fetched_at': time.time(),
                    'playlist_id': playlist_id
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
                logger.debug(f"Cached playlist items to {cache_file}")
            except OSError as e:
                logger.warning(f"Failed to cache playlist items: {e}")
                
        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.warning("YouTube API quota exceeded while fetching playlist items.")
            else:
                logger.error(f"Failed to fetch playlist items: {e}")
            return set()  # Return empty set on error
        except Exception as e:
            logger.error(f"Unexpected error fetching playlist items: {e}")
            return set()
        
        return video_ids

    def get_subscription_activity(
        self, published_after: str, max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent videos from subscribed channels using the activities endpoint.
        This is more efficient than fetching each channel individually.

        Args:
            published_after: RFC 3339 timestamp for filtering recent videos
            max_results: Maximum number of activities to fetch

        Returns:
            List of video data dictionaries
        """
        videos = []
        
        try:
            request = self.service.activities().list(
                part="snippet,contentDetails",
                mine=True,
                publishedAfter=published_after,
                maxResults=max_results
            )
            
            response = request.execute()
            activity_map = {}
            video_ids = []

            # Extract upload activities
            for item in response.get("items", []):
                if item["snippet"]["type"] == "upload":
                    video_id = item["contentDetails"]["upload"]["videoId"]
                    video_ids.append(video_id)
                    activity_map[video_id] = item

            if not video_ids:
                logger.info("No upload activities found in recent subscriptions")
                return videos

            # Batch fetch video details including duration
            videos_details = self._get_videos_details(video_ids)

            # Combine activity data with video details
            for video_id, details in videos_details.items():
                if video_id in activity_map:
                    activity = activity_map[video_id]

                    video_data = {
                        "video_id": video_id,
                        "title": activity["snippet"]["title"],
                        "channel_id": activity["snippet"]["channelId"],
                        "channel_title": activity["snippet"]["channelTitle"],
                        "published_at": activity["snippet"]["publishedAt"],
                        "duration_seconds": parse_duration_to_seconds(details["duration"]),
                        "live_broadcast": details["liveBroadcastContent"]
                    }
                    videos.append(video_data)

            logger.info(f"Found {len(videos)} recent subscription videos")
            return videos

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.error("YouTube API quota exceeded while fetching subscription activities.")
            else:
                logger.error(f"YouTube API error fetching subscription activities: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching subscription activities: {e}")
            return []

    def get_recent_uploads_from_subscriptions(
        self, published_after: str, max_per_channel: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent uploads from all subscribed channels using optimized uploads playlist lookup.
        
        This method is quota-optimized (~98% reduction vs search API) by:
        1. Fetching subscriptions list (1 unit)
        2. Getting channel uploads playlist IDs (1 unit per ~50 channels)
        3. Fetching recent videos from uploads playlists (1 unit per ~50 videos)
        4. Batch fetching video details (1 unit per ~50 videos)

        Args:
            published_after: RFC 3339 timestamp for filtering recent videos  
            max_per_channel: Maximum videos to fetch per channel

        Returns:
            List of video data dictionaries
        """
        videos = []

        try:
            # Step 1: Get all subscribed channels
            subscriptions = self._get_all_subscriptions()
            
            if not subscriptions:
                logger.info("No subscriptions found")
                return videos

            logger.info(f"Processing {len(subscriptions)} subscribed channels")

            # Step 2: Process each channel's uploads playlist
            for subscription in subscriptions:
                channel_id = subscription["snippet"]["resourceId"]["channelId"]
                channel_title = subscription["snippet"]["title"]
                
                # Get the uploads playlist ID for this channel
                uploads_playlist_id = self._get_uploads_playlist_id(channel_id, channel_title)
                if not uploads_playlist_id:
                    continue

                # Get recent videos from the uploads playlist
                channel_videos = self._get_recent_videos_from_uploads_playlist(
                    uploads_playlist_id, channel_title, max_per_channel, published_after
                )
                
                videos.extend(channel_videos)

            logger.info(f"Found {len(videos)} total recent videos from subscriptions")
            return videos

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.error("YouTube API quota exceeded while fetching subscription uploads.")
            else:
                logger.error(f"YouTube API error fetching subscription uploads: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching subscription uploads: {e}")
            return []

    def _get_all_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all user subscriptions with pagination support."""
        subscriptions = []
        next_page_token = None
        
        try:
            while True:
                request = self.service.subscriptions().list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                    pageToken=next_page_token
                )
                
                response = request.execute()
                subscriptions.extend(response.get("items", []))
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
                # Safety check
                if len(subscriptions) > 1000:
                    logger.warning("Reached subscription limit of 1000")
                    break
            
            logger.debug(f"Retrieved {len(subscriptions)} subscriptions")
            return subscriptions
            
        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.error("YouTube API quota exceeded while fetching subscriptions.")
            else:
                logger.error(f"YouTube API error fetching subscriptions: {e}")
            return []

    def _get_uploads_playlist_id(self, channel_id: str, channel_title: str) -> Optional[str]:
        """Get the uploads playlist ID for a specific channel."""
        try:
            request = self.service.channels().list(
                part="contentDetails",
                id=channel_id
            )
            
            response = request.execute()
            items = response.get("items", [])
            
            if not items:
                logger.debug(f"No channel data found for {channel_title}")
                return None
                
            uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
            logger.debug(f"Got uploads playlist {uploads_playlist_id} for {channel_title}")
            return uploads_playlist_id
            
        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.warning("YouTube API quota exceeded while fetching channel details.")
            else:
                logger.warning(f"YouTube API error fetching channel {channel_title}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching channel {channel_title}: {e}")
            return None

    def _get_recent_videos_from_uploads_playlist(
        self, uploads_playlist_id: str, channel_title: str, max_results: int, published_after: str
    ) -> List[Dict[str, Any]]:
        """Get recent videos from a channel's uploads playlist."""
        videos = []
        
        try:
            # Get recent playlist items (uploads are ordered by upload time)
            playlist_items = self._get_playlist_items(
                uploads_playlist_id, channel_title, max_results
            )

            if not playlist_items:
                logger.debug(f"No recent videos found for {channel_title}")
                return videos

            # Step 3: Extract video IDs and get detailed information
            video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]
            video_details = self._get_videos_details(video_ids)

            # Step 4: Filter by published date and combine with video details
            from datetime import datetime
            published_after_dt = datetime.fromisoformat(published_after.replace('Z', '+00:00'))

            for item in playlist_items:
                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]
                
                # Filter by publish date (playlist items are ordered by upload date, 
                # but we need to check the actual publish date)
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace('Z', '+00:00'))
                if published_at <= published_after_dt:
                    continue  # Skip older videos
                
                # Get video details if available
                if video_id not in video_details:
                    logger.debug(f"No details found for video {video_id}")
                    continue
                    
                details = video_details[video_id]
                
                video_data = {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "channel_id": snippet["channelId"],
                    "channel_title": channel_title,
                    "published_at": snippet["publishedAt"],
                    "duration_seconds": parse_duration_to_seconds(details["duration"]),
                    "live_broadcast": details["liveBroadcastContent"]
                }
                videos.append(video_data)

            if videos:
                logger.debug(f"Found {len(videos)} recent videos from {channel_title}")

            return videos

        except Exception as e:
            logger.warning(f"Error processing uploads for {channel_title}: {e}")
            return []

    def _get_playlist_items(
        self, uploads_playlist_id: str, channel_title: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Get playlist items with error handling."""
        try:
            request = self.service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=min(max_results, 50)  # API limit is 50
            )
            
            response = request.execute()
            return response.get("items", [])
            
        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.warning(f"YouTube API quota exceeded while fetching playlist items for {channel_title}.")
            else:
                logger.warning(f"YouTube API error fetching playlist items for {channel_title}: {e}")
            return []

    def _get_videos_details_batch(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch video details for a batch of up to 50 video IDs with retry logic.
        
        Args:
            video_ids: List of YouTube video IDs (max 50)
            
        Returns:
            Dict mapping video_id to details dict with 'duration' and 'liveBroadcastContent' keys
        """
        if not video_ids or len(video_ids) > 50:
            logger.warning(f"Invalid batch size: {len(video_ids)}. Expected 1-50 video IDs.")
            return {}
            
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                request = self.service.videos().list(
                    part="contentDetails,snippet", 
                    id=",".join(video_ids)
                )
                
                response = request.execute()
                batch_details = {}
                
                for item in response.get("items", []):
                    video_id = item["id"]
                    duration = item["contentDetails"]["duration"]
                    live_broadcast_content = item["snippet"].get("liveBroadcastContent", "none")
                    batch_details[video_id] = {
                        "duration": duration,
                        "liveBroadcastContent": live_broadcast_content
                    }
                
                # Log any missing videos from the batch
                missing_videos = set(video_ids) - set(batch_details.keys())
                if missing_videos:
                    logger.warning(f"Videos not found or unavailable: {list(missing_videos)}")
                
                return batch_details
                
            except HttpError as e:
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    self.quota_exceeded = True
                    logger.error("YouTube API quota exceeded while fetching video details.")
                    logger.error("Try again after 12AM Pacific Time.")
                    return {}
                elif attempt < max_retries:
                    logger.warning(f"YouTube API error fetching video batch (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    logger.error(f"YouTube API error fetching video details after {max_retries + 1} attempts: {e}")
                    return {}
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Unexpected error fetching video batch (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    logger.error(f"Unexpected error fetching video details after {max_retries + 1} attempts: {e}")
                    return {}
        
        return {}

    def _get_videos_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch video details including duration and live broadcast status for multiple video IDs.
        
        Efficiently batches requests to use up to 50 video IDs per API call, dramatically 
        reducing quota usage compared to individual requests.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict mapping video_id to details dict with 'duration' and 'liveBroadcastContent' keys
        """
        if not video_ids:
            return {}

        # Remove duplicates while preserving order
        unique_video_ids = list(dict.fromkeys(video_ids))
        
        if len(unique_video_ids) != len(video_ids):
            logger.debug(f"Removed {len(video_ids) - len(unique_video_ids)} duplicate video IDs")

        details = {}
        batch_size = 50
        total_batches = (len(unique_video_ids) + batch_size - 1) // batch_size
        failed_batches = 0
        
        logger.info(f"Fetching details for {len(unique_video_ids)} videos using {total_batches} batched API calls")

        for i in range(0, len(unique_video_ids), batch_size):
            # Stop processing if quota was exceeded
            if self.quota_exceeded:
                logger.warning(f"Skipping remaining video detail batches due to quota exceeded")
                break
                
            batch = unique_video_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.debug(f"Processing video batch {batch_num}/{total_batches} ({len(batch)} videos)")
            
            batch_details = self._get_videos_details_batch(batch)
            
            if batch_details:
                details.update(batch_details)
                logger.debug(f"Batch {batch_num}: fetched {len(batch_details)} video details")
            else:
                failed_batches += 1
                logger.warning(f"Batch {batch_num}: failed to fetch video details")

        successful_videos = len(details)
        failed_videos = len(unique_video_ids) - successful_videos
        quota_used = total_batches - failed_batches  # Each successful batch = 1 quota unit
        quota_saved = len(unique_video_ids) - quota_used  # vs individual calls
        
        logger.info(f"Video details summary: {successful_videos} fetched, {failed_videos} failed, "
                   f"{quota_used} quota units used (saved {quota_saved} units vs individual calls)")
        
        if failed_batches > 0:
            logger.warning(f"{failed_batches}/{total_batches} batches failed")
            
        return details

    def get_or_create_playlist(
        self,
        playlist_id: Optional[str],
        playlist_name: str,
        privacy_status: str = "unlisted",
    ) -> Optional[str]:
        """
        Get existing playlist by ID or create a new one.
        
        Args:
            playlist_id: Existing playlist ID (if None, creates new playlist)
            playlist_name: Name for new playlist
            privacy_status: Privacy setting ('private', 'unlisted', 'public')
            
        Returns:
            Playlist ID if successful, None if failed
        """
        if playlist_id:
            # Verify the playlist exists and is accessible
            try:
                request = self.service.playlists().list(
                    part="snippet", id=playlist_id
                )
                response = request.execute()

                if response.get("items"):
                    playlist_title = response["items"][0]["snippet"]["title"]
                    logger.info(f"Using existing playlist: {playlist_title} ({playlist_id})")
                    return playlist_id
                else:
                    logger.error(f"Playlist {playlist_id} not found or not accessible")
                    return None

            except HttpError as e:
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    self.quota_exceeded = True
                    logger.error("YouTube API quota exceeded while checking playlist.")
                    return None
                else:
                    logger.error(f"Error checking playlist {playlist_id}: {e}")
                    return None

        # Create new playlist
        try:
            playlist_body = {
                "snippet": {
                    "title": playlist_name,
                    "description": f"Automatically curated playlist created by yt-sub-playlist",
                },
                "status": {"privacyStatus": privacy_status},
            }

            request = self.service.playlists().insert(
                part="snippet,status", body=playlist_body
            )
            
            response = request.execute()
            new_playlist_id = response["id"]
            
            logger.info(f"Created new playlist: {playlist_name} ({new_playlist_id})")
            return new_playlist_id

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.error("YouTube API quota exceeded while creating playlist.")
            else:
                logger.error(f"Failed to create playlist: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating playlist: {e}")
            return None

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> bool:
        """
        Add a single video to a playlist.

        Args:
            playlist_id: Target playlist ID
            video_id: YouTube video ID to add

        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_item_body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            }

            request = self.service.playlistItems().insert(
                part="snippet", body=playlist_item_body
            )

            response = request.execute()
            logger.debug(f"Added video {video_id} to playlist {playlist_id}")
            return True

        except HttpError as e:
            # Handle common errors gracefully
            if e.resp.status == 409:
                logger.debug(f"Video {video_id} already in playlist {playlist_id}")
                return True  # Consider duplicates as success
            elif e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.warning("YouTube API quota exceeded while adding videos to playlist.")
                logger.warning("Try again after 12AM Pacific Time.")
                return False
            else:
                logger.warning(f"Failed to add video {video_id} to playlist: {e}")
                return False
        except Exception as e:
            logger.warning(f"Unexpected error adding video {video_id} to playlist: {e}")
            return False

    def add_videos_to_playlist(
        self, playlist_id: str, video_ids: List[str]
    ) -> Dict[str, bool]:
        """
        Add multiple videos to a playlist with duplicate detection and quota-aware early termination.

        Args:
            playlist_id: Target playlist ID
            video_ids: List of YouTube video IDs to add

        Returns:
            Dict mapping video_id to success status (True/False)
        """
        if not video_ids:
            return {}
            
        # Fetch existing playlist items to avoid duplicates
        existing_video_ids = self.fetch_existing_playlist_items(playlist_id)
        
        # Filter out duplicates before attempting insertion
        new_video_ids = []
        skipped_duplicates = []
        
        for video_id in video_ids:
            if video_id in existing_video_ids:
                skipped_duplicates.append(video_id)
                logger.info(f"Skipping duplicate video: {video_id}")
            else:
                new_video_ids.append(video_id)
        
        # Log duplicate detection results
        if skipped_duplicates:
            logger.info(f"Skipped {len(skipped_duplicates)} duplicate videos (quota saved: {len(skipped_duplicates) * 50} units)")
        
        if not new_video_ids:
            logger.info("All videos already exist in playlist - no insertions needed")
            # Return success for all videos since they're already in the playlist
            return {video_id: True for video_id in video_ids}

        # Process only new videos
        results = {}
        
        # Mark all skipped duplicates as successful (they're already in the playlist)
        for video_id in skipped_duplicates:
            results[video_id] = True

        # Add only the new videos
        logger.info(f"Adding {len(new_video_ids)} new videos to playlist")
        for video_id in new_video_ids:
            # Stop processing if quota was exceeded
            if self.quota_exceeded:
                logger.warning(f"Skipping remaining videos due to quota exceeded")
                break
                
            success = self.add_video_to_playlist(playlist_id, video_id)
            results[video_id] = success

        successful = sum(results.values())
        total_attempted = len([v for v in video_ids if v not in skipped_duplicates])
        
        if self.quota_exceeded and len(results) < len(video_ids):
            processed = len(results) - len(skipped_duplicates)
            logger.warning(
                f"Quota exceeded: only processed {processed}/{total_attempted} new videos, "
                f"{successful} total successful (including {len(skipped_duplicates)} pre-existing)"
            )
        else:
            new_additions = successful - len(skipped_duplicates)
            logger.info(
                f"Successfully processed {len(video_ids)} videos: "
                f"{new_additions} newly added, {len(skipped_duplicates)} already existed"
            )

        return results