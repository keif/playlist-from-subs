#!/usr/bin/env python3
"""
playlist-from-subs: Automatically add new subscription videos to a YouTube playlist

This script fetches recent videos from your YouTube subscriptions, filters them
based on duration and other criteria, and adds them to a specified playlist.
Perfect for running as a cron job to keep your playlists updated.
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv

from utils import (
    VideoCache,
    get_published_after_timestamp,
    parse_channel_whitelist,
    setup_logging,
)
from youtube_api import YouTubeAPI

logger = logging.getLogger(__name__)


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


def filter_videos(
    videos: List[Dict[str, Any]],
    config: Dict[str, Any],
    cache: VideoCache,
    channel_whitelist: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter videos based on duration, whitelist, and cache status.

    Args:
        videos: List of video data from YouTube API
        config: Configuration dictionary
        cache: VideoCache instance for checking processed videos
        channel_whitelist: Set of allowed channel IDs (None = allow all)

    Returns:
        Filtered list of videos that should be added to playlist
    """
    filtered = []
    stats = {
        "total": len(videos),
        "too_short": 0,
        "not_whitelisted": 0,
        "already_processed": 0,
        "live_content_skipped": 0,
        "passed_filters": 0,
    }

    min_duration = config["min_duration_seconds"]

    for video in videos:
        video_id = video["video_id"]
        title = video["title"]
        channel_title = video["channel_title"]
        duration = video["duration_seconds"]

        # Check if already processed
        if cache.is_processed(video_id):
            logger.debug(f"Skipping already processed: {title}")
            stats["already_processed"] += 1
            continue

        # Check duration filter
        if duration < min_duration:
            logger.debug(f"Skipping too short ({duration}s): {title}")
            stats["too_short"] += 1
            continue

        # Check channel whitelist
        if channel_whitelist is not None:
            if video["channel_id"] not in channel_whitelist:
                logger.debug(
                    f"Skipping non-whitelisted channel {channel_title}: {title}"
                )
                stats["not_whitelisted"] += 1
                continue

        # Check live content filter
        if config["skip_live_content"]:
            live_broadcast = video.get("live_broadcast", "none")
            if live_broadcast != "none":
                live_type = "livestream" if live_broadcast == "live" else "premiere"
                logger.info(f"Skipping {live_type}: {title}")
                stats["live_content_skipped"] += 1
                continue

        # Video passed all filters
        stats["passed_filters"] += 1
        filtered.append(video)
        logger.info(f"✓ {title} ({duration}s) by {channel_title}")

    # Log filtering statistics
    logger.info(f"Video filtering stats:")
    logger.info(f"  Total videos: {stats['total']}")
    logger.info(f"  Already processed: {stats['already_processed']}")
    logger.info(f"  Too short (<{min_duration}s): {stats['too_short']}")
    if channel_whitelist:
        logger.info(f"  Not in whitelist: {stats['not_whitelisted']}")
    if config["skip_live_content"]:
        logger.info(f"  Live content skipped: {stats['live_content_skipped']}")
    logger.info(f"  Passed filters: {stats['passed_filters']}")

    return filtered


def add_videos_to_playlist(
    api: YouTubeAPI,
    playlist_id: str,
    videos: List[Dict[str, Any]],
    cache: VideoCache,
    dry_run: bool = False,
) -> Dict[str, bool]:
    """
    Add filtered videos to the playlist and update cache.

    Args:
        api: YouTube API wrapper instance
        playlist_id: Target playlist ID
        videos: List of videos to add
        cache: VideoCache instance for tracking processed videos
        dry_run: If True, don't actually add videos

    Returns:
        Dict mapping video_id to success status
    """
    if not videos:
        logger.info("No videos to add to playlist")
        return {}

    if dry_run:
        logger.info(
            f"DRY RUN: Would add {len(videos)} videos to playlist {playlist_id}"
        )
        for video in videos:
            logger.info(f"  - {video['title']} ({video['video_id']})")
        return {video["video_id"]: True for video in videos}

    # Add videos to playlist
    video_ids = [video["video_id"] for video in videos]
    results = api.add_videos_to_playlist(playlist_id, video_ids)

    # Update cache for successful additions
    for video in videos:
        video_id = video["video_id"]
        if results.get(video_id, False):
            cache.mark_processed(
                video_id, title=video["title"], channel=video["channel_title"]
            )
            logger.info(f"✅ Added: {video['title']}")
        else:
            logger.warning(f"❌ Failed to add: {video['title']}")

    return results


def main():
    """Main orchestration function."""
    parser = argparse.ArgumentParser(
        description="Add new subscription videos to a YouTube playlist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Normal run with .env config
  python main.py --dry-run          # See what would be added without changes
  python main.py --verbose          # Enable debug logging
  python main.py --limit 10         # Fetch max 10 recent videos
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be added without making changes",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose debug logging"
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of recent videos to fetch (overrides MAX_VIDEOS_TO_FETCH)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    try:
        # Load configuration
        config = load_config()
        if args.limit:
            config["max_videos"] = args.limit

        logger.info(
            f"Starting playlist-from-subs ({'DRY RUN' if args.dry_run else 'LIVE RUN'})"
        )
        logger.info(
            f"Config: {config['lookback_hours']}h lookback, {config['min_duration_seconds']}s min duration"
        )

        # Initialize components
        api = YouTubeAPI()
        cache = VideoCache()

        # Log cache stats
        cache_stats = cache.get_stats()
        logger.info(
            f"Cache: {cache_stats['total_processed']} videos processed, "
            f"oldest entry {cache_stats['oldest_entry_days']} days"
        )

        # Get or create target playlist
        playlist_id = api.get_or_create_playlist(
            playlist_id=config["playlist_id"],
            playlist_name=config["playlist_name"],
            privacy_status=config["playlist_visibility"],
        )

        if not playlist_id:
            logger.error("Failed to get or create target playlist")
            sys.exit(1)

        # Fetch recent subscription videos
        published_after = get_published_after_timestamp(config["lookback_hours"])
        logger.info(f"Fetching videos published after {published_after}")

        videos = api.get_subscription_activity(
            published_after=published_after, max_results=config["max_videos"]
        )

        if not videos:
            logger.info("No recent subscription videos found")
            sys.exit(0)

        # Filter videos based on criteria
        filtered_videos = filter_videos(
            videos=videos,
            config=config,
            cache=cache,
            channel_whitelist=config["channel_whitelist"],
        )

        if not filtered_videos:
            logger.info("No videos passed filters")
            sys.exit(0)

        # Add videos to playlist
        results = add_videos_to_playlist(
            api=api,
            playlist_id=playlist_id,
            videos=filtered_videos,
            cache=cache,
            dry_run=args.dry_run,
        )

        # Summary
        successful = sum(results.values())
        total = len(results)

        if args.dry_run:
            logger.info(f"DRY RUN complete: {total} videos would be added")
        else:
            logger.info(
                f"Processing complete: {successful}/{total} videos added successfully"
            )

            if successful < total:
                logger.warning(f"{total - successful} videos failed to add")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)

    except SystemExit:
        # Re-raise SystemExit (from authentication failures, etc.)
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
