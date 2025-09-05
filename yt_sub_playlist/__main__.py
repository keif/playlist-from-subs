"""
Main entry point for YouTube Subscription Playlist Manager.

This module provides the command-line interface and orchestrates the complete workflow:
- Configuration loading and validation
- Video fetching from subscriptions  
- Intelligent filtering and deduplication
- Playlist synchronization
- Report generation
"""

import argparse
import logging
import sys
from pathlib import Path

from .config.env_loader import load_config, setup_logging
from .core.playlist_manager import PlaylistManager
from .core.video_filtering import get_published_after_timestamp, parse_channel_whitelist
from .core.youtube_client import dump_api_call_log

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Add new subscription videos to a YouTube playlist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m yt_sub_playlist                    # Normal run with .env config
  python -m yt_sub_playlist --dry-run          # See what would be added without changes
  python -m yt_sub_playlist --verbose          # Enable debug logging
  python -m yt_sub_playlist --limit 10         # Fetch max 10 recent videos
  python -m yt_sub_playlist --report output.csv # Generate CSV report of added videos
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

    parser.add_argument(
        "--report",
        type=str,
        help="Generate a CSV report of added videos at the specified path",
    )

    return parser


def _dump_api_call_log():
    """Dump API call log for quota analysis."""
    try:
        log_path = Path("yt_sub_playlist/data/api_call_log.json")
        dump_api_call_log(log_path)
    except Exception as e:
        logger.debug(f"Failed to dump API call log: {e}")


def main():
    """Main orchestration function."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    try:
        # Load configuration
        config = load_config()
        if args.limit:
            config["max_videos"] = args.limit

        logger.info(
            f"Starting yt-sub-playlist ({'DRY RUN' if args.dry_run else 'LIVE RUN'})"
        )
        logger.info(
            f"Config: {config['lookback_hours']}h lookback, {config['min_duration_seconds']}s min duration"
        )

        # Initialize playlist manager
        manager = PlaylistManager(config)

        # Log cache stats
        cache_stats = manager.get_cache_stats()
        logger.info(
            f"Cache: {cache_stats['total_processed']} videos processed, "
            f"oldest entry {cache_stats['oldest_entry_days']} days"
        )

        # Get or create target playlist
        playlist_id = manager.get_or_create_playlist(
            playlist_id=config["playlist_id"],
            playlist_name=config["playlist_name"],
            privacy_status=config["playlist_visibility"],
        )

        # Fetch recent subscription videos and sync to playlist
        published_after = get_published_after_timestamp(config["lookback_hours"])
        
        video_results = manager.sync_subscription_videos_to_playlist(
            playlist_id=playlist_id,
            published_after=published_after,
            channel_whitelist=config["channel_whitelist"],
            dry_run=args.dry_run
        )

        # Generate report if requested
        if args.report:
            manager.write_report(video_results, args.report)

        # Summary
        successful = sum(1 for v in video_results if v.get('added', False))
        total = len(video_results)

        if args.dry_run:
            logger.info(f"DRY RUN complete: {total} videos would be added")
        else:
            logger.info(
                f"Processing complete: {successful}/{total} videos added successfully"
            )

            if successful < total:
                logger.warning(f"{total - successful} videos failed to add")
                _dump_api_call_log()
                sys.exit(1)
        
        # Dump API call log for quota analysis
        _dump_api_call_log()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        _dump_api_call_log()
        sys.exit(130)

    except SystemExit:
        # Re-raise SystemExit (from authentication failures, etc.)
        _dump_api_call_log()
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        _dump_api_call_log()
        sys.exit(1)


if __name__ == "__main__":
    main()