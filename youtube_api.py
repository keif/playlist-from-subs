import logging
import time
from typing import Any, Dict, List, Optional

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
            logger.error(f"YouTube API error fetching subscriptions: {e}")
            return []

    def _get_channel_recent_uploads(
        self, channel_id: str, channel_title: str, published_after: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Get recent upload videos from a specific channel.

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
            # Search for recent videos from this channel
            request = self.service.search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order="date",
                publishedAfter=published_after,
                maxResults=min(max_results, 50)
            )

            response = request.execute()
            items = response.get("items", [])

            if not items:
                logger.debug(f"No recent videos found for {channel_title}")
                return videos

            # Extract video IDs and get detailed information
            video_ids = [item["id"]["videoId"] for item in items]
            video_details = self._get_videos_details(video_ids)

            # Combine search results with video details
            for item in items:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # Get details from videos API
                details = video_details.get(video_id, {})
                
                video_data = {
                    "video_id": video_id,
                    "title": snippet["title"],
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "published_at": snippet["publishedAt"],
                    "duration_seconds": parse_duration_to_seconds(
                        details.get("duration", "")
                    ),
                    "live_broadcast": details.get("liveBroadcastContent", "none"),
                }
                videos.append(video_data)

            logger.debug(f"Found {len(videos)} recent videos from {channel_title}")
            return videos

        except HttpError as e:
            logger.warning(f"YouTube API error fetching videos for {channel_title}: {e}")
            return []

    def _get_videos_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch video details including duration and live broadcast status for a batch of video IDs.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict mapping video_id to details dict with 'duration' and 'liveBroadcastContent' keys
        """
        details = {}

        if not video_ids:
            return details

        try:
            # YouTube API allows up to 50 IDs per request
            batch_size = 50
            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i : i + batch_size]

                request = self.service.videos().list(
                    part="contentDetails,snippet", id=",".join(batch)
                )

                response = request.execute()

                for item in response.get("items", []):
                    video_id = item["id"]
                    duration = item["contentDetails"]["duration"]
                    live_broadcast_content = item["snippet"].get("liveBroadcastContent", "none")
                    details[video_id] = {
                        "duration": duration,
                        "liveBroadcastContent": live_broadcast_content
                    }

            logger.debug(f"Fetched details for {len(details)} videos")
            return details

        except HttpError as e:
            logger.error(f"YouTube API error fetching video details: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching video details: {e}")
            return {}

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

        # Create new playlist
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
        Add multiple videos to a playlist.

        Args:
            playlist_id: Target playlist ID
            video_ids: List of YouTube video IDs to add

        Returns:
            Dict mapping video_id to success status (True/False)
        """
        results = {}

        for video_id in video_ids:
            success = self.add_video_to_playlist(playlist_id, video_id)
            results[video_id] = success

        successful = sum(results.values())
        logger.info(
            f"Successfully added {successful}/{len(video_ids)} videos to playlist"
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
