# yt-sub-playlist

Automatically sync your latest YouTube subscription uploads into a custom playlist using the YouTube Data API v3.

> A modular Python package that creates or updates a playlist with your most recent subscribed content — filtered, customizable, and cron-friendly.

---

## Features

- **Quota-optimized API usage** - Batched operations reduce quota consumption by 95%+
- **Intelligent duplicate detection** - Pre-insertion caching prevents wasted API calls
- **Flexible video filtering**:
  - Minimum duration requirements (skip shorts)
  - Live content filtering (livestreams/premieres)
  - Channel whitelist support
  - Custom filtering rules
- **Robust error handling** - Retry logic and graceful degradation
- **Multiple interfaces** - Command-line tool and shell scripts
- **Comprehensive reporting** - CSV reports with detailed metadata
- **Automated scheduling** - Cron-friendly design with proper logging

---

## Requirements

- Python 3.8+
- YouTube Data API v3 access
- Google Cloud project with:
  - OAuth 2.0 client ID + secret
  - YouTube Data API enabled

---

## Installation

```bash
git clone https://github.com/yourusername/yt-sub-playlist.git
cd yt-sub-playlist
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Setup

1. **Google Cloud OAuth credentials**
   - Visit https://console.cloud.google.com/
   - Create a new project → enable YouTube Data API v3
   - Create OAuth 2.0 credentials (desktop type)
   - Download `client_secrets.json` and place it in the project root

2. **Create .env file**
   ```bash
   cp .env.example .env
   ```

3. **Run Initial Auth Flow**
   ```bash
   python -m yt_sub_playlist.auth.oauth
   ```
   This will open a browser window to authorize your Google account and store `token.json`.

---

## Architecture

The codebase is organized as a modular Python package:

```
yt_sub_playlist/
├── __main__.py               # CLI entry point
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── youtube_client.py     # YouTube API wrapper with quota optimization
│   ├── video_filtering.py    # Video filtering and processing logic
│   ├── playlist_manager.py   # High-level playlist orchestration
│   └── quota_tracker.py      # Quota management and estimation
├── auth/
│   ├── __init__.py
│   └── oauth.py              # OAuth2 authentication handling
├── config/
│   ├── __init__.py
│   ├── env_loader.py         # Environment configuration management
│   └── schema.py             # Configuration validation and defaults
├── data/
│   ├── processed_videos.json # Cache of processed video IDs
│   ├── playlist_cache/       # Cached playlist contents
│   └── logs/                 # Application logs
├── scripts/
│   ├── run.sh               # Production runner script
│   ├── dryrun.sh            # Dry-run testing script
│   └── reset-auth.sh        # Authentication reset utility
└── reports/
    └── videos_added.csv     # Generated reports
```

### Module Overview

- **`core/youtube_client.py`** - Low-level YouTube API operations with batching and caching
- **`core/video_filtering.py`** - Video filtering logic and criteria management
- **`core/playlist_manager.py`** - High-level workflow orchestration
- **`core/quota_tracker.py`** - Quota management and estimation utilities
- **`auth/oauth.py`** - OAuth2 flow and credential management
- **`config/env_loader.py`** - Configuration loading and validation
- **`config/schema.py`** - Configuration contracts and defaults

---

## Usage

### Basic Usage

```bash
# Normal run - adds new videos to playlist
python -m yt_sub_playlist

# Dry-run mode (shows what would be added without making changes)
python -m yt_sub_playlist --dry-run

# Verbose logging for debugging
python -m yt_sub_playlist --verbose

# Limit number of videos to process
python -m yt_sub_playlist --limit 20

# Generate CSV report
python -m yt_sub_playlist --report reports/videos_added.csv
```

### Helper Scripts

Convenient shell scripts are provided for common operations:

```bash
# Production run with logging
./yt_sub_playlist/scripts/run.sh

# Dry-run mode with verbose output
./yt_sub_playlist/scripts/dryrun.sh

# Reset authentication tokens
./yt_sub_playlist/scripts/reset-auth.sh
```

> All scripts are automatically made executable during setup.

### CSV Reporting

Generate detailed CSV reports of all processed videos:

```bash
# Generate report with video metadata
python -m yt_sub_playlist --report reports/videos_added.csv

# Combine with dry-run to preview what would be processed
python -m yt_sub_playlist --dry-run --report reports/preview.csv
```

**CSV Fields**: title, video_id, channel_title, channel_id, published_at, duration_seconds, live_broadcast, added

### Environment Configuration

Key settings in `.env`:

```bash
# Playlist configuration
PLAYLIST_ID=PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Optional: use existing playlist
PLAYLIST_NAME="My Auto Playlist"              # Name for new playlists
PLAYLIST_VISIBILITY=unlisted                  # private, unlisted, or public

# Video filtering
VIDEO_MIN_DURATION_SECONDS=120               # Skip videos shorter than 2 minutes
SKIP_LIVE_CONTENT=true                       # Skip livestreams and premieres
CHANNEL_ID_WHITELIST=UC1234,UC5678          # Optional: only include these channels

# Fetching behavior  
LOOKBACK_HOURS=24                            # How far back to look for videos
MAX_VIDEOS_TO_FETCH=50                       # Maximum videos to process per run
```

---

## Automation

### Cron Job Setup

Run the script on a schedule using cron:

```bash
# Edit your crontab
crontab -e

# Add entry to run every 2 hours
0 */2 * * * cd /path/to/yt-sub-playlist && ./yt_sub_playlist/scripts/run.sh
```

### Advanced Scheduling

For more complex scheduling needs, consider using:
- **systemd timers** (Linux)
- **Task Scheduler** (Windows)  
- **APScheduler** (Python-based)
- **GitHub Actions** (cloud-based)

---

## API Quota Optimization

This tool is designed to minimize YouTube API quota usage:

- **Batched operations** - Up to 50 videos per API call
- **Smart caching** - 12-hour TTL for playlist contents
- **Duplicate detection** - Pre-insertion filtering prevents waste
- **Efficient subscription handling** - Uses uploads playlist lookup vs expensive search

**Typical quota usage**:
- Before optimization: ~8,000 units per run
- After optimization: ~500-1,000 units per run
- **~85-90% quota reduction**

---

## Troubleshooting

### Authentication Issues

```bash
# Reset stored tokens and re-authenticate
./yt_sub_playlist/scripts/reset-auth.sh

# Test authentication manually
python -m yt_sub_playlist.auth.oauth
```

### Configuration Problems

```bash
# Validate your .env configuration
python -c "
from yt_sub_playlist.config.env_loader import load_config
from yt_sub_playlist.config.schema import ConfigSchema
config = load_config()
print(ConfigSchema.get_config_summary(config))
"
```

### Quota Exceeded

If you hit quota limits:
1. Wait until midnight Pacific Time for quota reset
2. Reduce `LOOKBACK_HOURS` to process fewer videos
3. Use `--limit` flag to restrict processing
4. Check quota usage in Google Cloud Console

---

## Development

### Running Tests

```bash
# Test core functionality
python -m pytest tests/

# Test specific modules
python -m pytest tests/test_video_filtering.py -v
```

### Code Structure

The modular design supports:
- **Easy testing** - Each module has clear responsibilities
- **Flexible configuration** - Environment-based settings
- **Extensible filtering** - Add custom video criteria
- **Multiple interfaces** - CLI, scripts, or direct imports

---

## TODO

- [ ] Web dashboard interface
- [ ] Advanced video filtering rules (regex, custom criteria)
- [ ] Playlist cleanup (remove old videos)
- [ ] Multiple playlist targets
- [ ] Notification integrations (email, Slack, Discord)
- [ ] Performance metrics and quota tracking
- [ ] Docker container support

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.