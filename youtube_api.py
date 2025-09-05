import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Set

from googleapiclient.errors import HttpError

from auth import get_authenticated_service
from utils import parse_duration_to_seconds

logger = logging.getLogger(__name__)


class YouTubeAPI:
    """
    Wrapper for YouTube Data API v3 with methods specific to playlist automation.
    Handles API calls, error handling, and data transformation.
    """

    def __init__(self):
        self.service = get_authenticated_service()
        self.quota_exceeded = False  # Track quota status

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
        cache_file = f"existing_playlist_items_{playlist_id}.json"
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
            max_results: Maximum number of activities to fetch (default 50, max 50)

        Returns:
            List of video data dictionaries with keys: video_id, title, channel_id,
            channel_title, published_at, duration_seconds, live_broadcast
        """
        videos = []

        try:
            # Get subscription activities (uploads from subscribed channels)
            request = self.service.activities().list(
                part="snippet,contentDetails",
                home=True,
                publishedAfter=published_after,
                maxResults=min(max_results, 50),  # API limit is 50
            )

            response = request.execute()

            if "items" not in response:
                logger.warning("No activities found in API response")
                return videos

            # Extract video IDs for batch duration lookup
            video_ids = []
            activity_map = {}

            for item in response["items"]:
                # Only process upload activities
                if item["snippet"]["type"] == "upload" and "upload" in item.get(
                    "contentDetails", {}
                ):

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
                        "duration_seconds": parse_duration_to_seconds(
                            details.get("duration", "")
                        ),
                        "live_broadcast": details.get("liveBroadcastContent", "none"),
                    }
                    videos.append(video_data)

            logger.info(f"Found {len(videos)} recent videos from subscriptions")
            return videos

        except HttpError as e:
            logger.error(f"YouTube API error fetching subscription activity: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching subscription activity: {e}")
            return []

    def get_recent_uploads_from_subscriptions(
        self, published_after: str, max_per_channel: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent videos from subscribed channels by fetching subscriptions
        and then searching each channel individually. More reliable than activities API.

        Args:
            published_after: RFC 3339 timestamp for filtering recent videos
            max_per_channel: Maximum number of videos to fetch per channel

        Returns:
            List of video data dictionaries with keys: video_id, title, channel_id,
            channel_title, published_at, duration_seconds, live_broadcast
        """
        videos = []

        try:
            # Get all subscriptions
            subscriptions = self._get_all_subscriptions()
            if not subscriptions:
                logger.warning("No subscriptions found")
                return videos

            logger.info(f"Found {len(subscriptions)} subscribed channels")

            # Process each subscribed channel
            total_channels = len(subscriptions)
            for i, subscription in enumerate(subscriptions, 1):
                channel_id = subscription["snippet"]["resourceId"]["channelId"]
                channel_title = subscription["snippet"]["title"]

                # Log progress every 10 channels
                if i % 10 == 0 or i == total_channels:
                    logger.info(f"Processing channel {i}/{total_channels}: {channel_title}")

                # Get recent uploads for this channel
                channel_videos = self._get_channel_recent_uploads(
                    channel_id, channel_title, published_after, max_per_channel
                )
                videos.extend(channel_videos)

                # Add small delay to avoid quota spikes
                time.sleep(0.25)

            logger.info(f"Found {len(videos)} total recent videos from {total_channels} channels")
            return videos

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                self.quota_exceeded = True
                logger.error("YouTube API quota exceeded. Try again after 12AM Pacific Time.")
                logger.error("Consider reducing max_per_channel or running less frequently.")
            else:
                logger.error(f"YouTube API error fetching subscription uploads: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching subscription uploads: {e}")
            return []

    def _get_all_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Fetch all user subscriptions using pagination.

        Returns:
            List of subscription data dictionaries
        """
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
                items = response.get("items", [])
                subscriptions.extend(items)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            return subscriptions

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                logger.error("YouTube API quota exceeded while fetching subscriptions.")
                logger.error("Try again after 12AM Pacific Time.")
            else:
                logger.error(f"YouTube API error fetching subscriptions: {e}")
            return []

    def _get_channel_recent_uploads(
        self, channel_id: str, channel_title: str, published_after: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Get recent upload videos from a specific channel using the uploads playlist.
        This is much more quota-efficient than search() API (1 unit vs 100 units).

        Args:
            channel_id: YouTube channel ID
            channel_title: Channel display name (for logging)
            published_after: RFC 3339 timestamp for filtering
            max_results: Maximum number of videos to fetch

        Returns:
            List of video data dictionaries
        """
        videos = []

        try:
            # QUOTA OPTIMIZATION: Replace expensive search().list() (100 units) 
            # with channels().list() + playlistItems().list() (1 unit each)
            
            # Step 1: Get the channel's uploads playlist ID (1 quota unit)
            uploads_playlist_id = self._get_channel_uploads_playlist_id(channel_id, channel_title)
            if not uploads_playlist_id:
                return videos

            # Step 2: Fetch recent videos from uploads playlist (1 quota unit per 50 items)
            playlist_items = self._get_playlist_recent_items(
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
                # but we still need to filter by our specific timeframe)
                published_at_str = snippet["publishedAt"]
                published_at_dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                
                if published_at_dt < published_after_dt:
                    continue  # Skip videos older than our lookback period
                
                # Get details from videos API
                details = video_details.get(video_id, {})
                
                video_data = {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "published_at": published_at_str,
                    "duration_seconds": parse_duration_to_seconds(
                        details.get("duration", "")
                    ),
                    "live_broadcast": details.get("liveBroadcastContent", "none"),
                }
                videos.append(video_data)

            logger.debug(f"Found {len(videos)} recent videos from {channel_title}")
            return videos

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                logger.warning(f"YouTube API quota exceeded while fetching videos for {channel_title}.")
                logger.warning("Stopping channel processing due to quota limits.")
            else:
                logger.warning(f"YouTube API error fetching videos for {channel_title}: {e}")
            return []

    def _get_channel_uploads_playlist_id(self, channel_id: str, channel_title: str) -> Optional[str]:
        """
        Get the uploads playlist ID for a channel. This is more quota-efficient 
        than using search() API.

        Args:
            channel_id: YouTube channel ID
            channel_title: Channel display name (for logging)

        Returns:
            Uploads playlist ID if found, None otherwise
        """
        try:
            # Use channels().list() to get channel details (1 quota unit)
            request = self.service.channels().list(
                part="contentDetails",
                id=channel_id
            )

            response = request.execute()
            items = response.get("items", [])

            if not items:
                logger.debug(f"No channel details found for {channel_title}")
                return None

            # Extract uploads playlist ID
            content_details = items[0].get("contentDetails", {})
            uploads_playlist_id = content_details.get("relatedPlaylists", {}).get("uploads")

            if not uploads_playlist_id:
                logger.debug(f"No uploads playlist found for {channel_title}")
                return None

            logger.debug(f"Found uploads playlist {uploads_playlist_id} for {channel_title}")
            return uploads_playlist_id

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                logger.warning(f"YouTube API quota exceeded while getting uploads playlist for {channel_title}.")
            else:
                logger.warning(f"YouTube API error getting uploads playlist for {channel_title}: {e}")
            return None

    def _get_playlist_recent_items(self, playlist_id: str, channel_title: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Get recent items from a playlist (typically a channel's uploads playlist).
        This is very quota-efficient (1 unit per 50 items).

        Args:
            playlist_id: YouTube playlist ID
            channel_title: Channel display name (for logging)
            max_results: Maximum number of items to fetch

        Returns:
            List of playlist item dictionaries
        """
        try:
            # Use playlistItems().list() to get recent uploads (1 quota unit per 50 items)
            request = self.service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=min(max_results, 50)  # API limit is 50
            )

            response = request.execute()
            items = response.get("items", [])

            logger.debug(f"Found {len(items)} playlist items for {channel_title}")
            return items

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
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
        playlist_name: str = "Auto Playlist from Subscriptions",
        privacy_status: str = "unlisted",
    ) -> Optional[str]:
        """
        Get existing playlist or create a new one if it doesn't exist.

        Args:
            playlist_id: Existing playlist ID, or None to create new
            playlist_name: Name for new playlist if creation is needed
            privacy_status: Privacy setting (public, private, unlisted)

        Returns:
            Playlist ID if successful, None if failed
        """
        if playlist_id:
            # Verify existing playlist exists and is accessible
            if self._verify_playlist_exists(playlist_id):
                logger.info(f"Using existing playlist: {playlist_id}")
                return playlist_id
            else:
                logger.warning(f"Playlist {playlist_id} not found or inaccessible")

        # Check if playlist with this name already exists
        existing_playlist = self._find_playlist_by_name(playlist_name)
        if existing_playlist:
            logger.info(f"Found existing playlist '{playlist_name}' with ID: {existing_playlist}")
            return existing_playlist

        # Create new playlist only if none exists with this name
        logger.info(f"No existing playlist found with name '{playlist_name}', creating new one")
        return self._create_playlist(playlist_name, privacy_status)

    def _verify_playlist_exists(self, playlist_id: str) -> bool:
        """Check if playlist exists and is accessible."""
        try:
            request = self.service.playlists().list(part="snippet", id=playlist_id)
            response = request.execute()
            return len(response.get("items", [])) > 0

        except HttpError as e:
            logger.debug(f"Error verifying playlist {playlist_id}: {e}")
            return False

    def _find_playlist_by_name(self, playlist_name: str) -> Optional[str]:
        """
        Find existing playlist by name to avoid creating duplicates.

        Args:
            playlist_name: Name of playlist to search for

        Returns:
            Playlist ID if found, None otherwise
        """
        try:
            next_page_token = None
            
            while True:
                request = self.service.playlists().list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                    pageToken=next_page_token
                )

                response = request.execute()
                items = response.get("items", [])

                # Check each playlist for matching name
                for playlist in items:
                    if playlist["snippet"]["title"] == playlist_name:
                        playlist_id = playlist["id"]
                        logger.debug(f"Found existing playlist '{playlist_name}': {playlist_id}")
                        return playlist_id

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            logger.debug(f"No existing playlist found with name '{playlist_name}'")
            return None

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                logger.warning("YouTube API quota exceeded while searching for existing playlists.")
                logger.warning("Will attempt to create new playlist instead.")
            else:
                logger.warning(f"Error searching for playlist '{playlist_name}': {e}")
            return None

    def _create_playlist(self, title: str, privacy_status: str) -> Optional[str]:
        """Create a new playlist."""
        try:
            playlist_body = {
                "snippet": {
                    "title": title,
                    "description": "Automatically generated playlist from subscription videos",
                },
                "status": {"privacyStatus": privacy_status},
            }

            request = self.service.playlists().insert(
                part="snippet,status", body=playlist_body
            )

            response = request.execute()
            playlist_id = response["id"]

            logger.info(f"Created new playlist '{title}' with ID: {playlist_id}")
            return playlist_id

        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                logger.error("YouTube API quota exceeded while creating playlist.")
                logger.error("Try again after 12AM Pacific Time.")
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


if __name__ == "__main__":
    # Simple test to verify API functionality
    import os
    from datetime import datetime, timedelta

    from utils import get_published_after_timestamp, setup_logging

    setup_logging(verbose=True)

    try:
        api = YouTubeAPI()

        # Test fetching recent subscription activity
        print("Testing new subscription uploads fetch...")
        published_after = get_published_after_timestamp(24)
        videos = api.get_recent_uploads_from_subscriptions(published_after, max_per_channel=3)

        print(f"Found {len(videos)} recent videos:")
        for video in videos[:3]:  # Show first 3
            print(
                f"  - {video['title']} ({video['duration_seconds']}s) by {video['channel_title']}"
            )

        # Test playlist verification (will fail gracefully if no playlist ID provided)
        print("\nTesting playlist operations...")
        test_playlist = api.get_or_create_playlist(
            playlist_id=None,  # Will create a new test playlist
            playlist_name="Test Playlist from Script",
            privacy_status="private",
        )

        if test_playlist:
            print(f"✅ Playlist ready: {test_playlist}")
        else:
            print("❌ Failed to get/create playlist")

    except SystemExit:
        print("❌ Authentication failed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
