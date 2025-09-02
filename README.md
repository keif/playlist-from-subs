# yt-sub-playlist

Automatically sync your latest YouTube subscription uploads into a custom playlist using the YouTube Data API v3.

> A Python-powered automation tool that creates or updates a playlist with your most recent subscribed content — filtered, customizable, and cron-friendly.

---

## Features

- Pulls uploads from your subscribed channels
- Adds them to a target playlist (new or existing)
- Filters out:
  - Shorts or very short videos (configurable minimum duration)
  - Livestreams and premieres (enabled by default, configurable)
  - Videos from non-whitelisted channels (optional)
- Configurable daily cron job
- OAuth2 token flow for secure access
- Logging and dry-run support
- CSV reporting of processed videos

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

1.	Google Cloud OAuth credentials
	-	Visit https://console.cloud.google.com/
	-	Create a new project -> enable YouTube Data API v3
	-	Create OAuth 2.0 credentials (desktop type)
	-	Download client_secrets.json and place it in the project root.
2.	Create .env file

```bash
cp .env.example .env
```

3. Run Initial Auth Flow

```bash
python auth.py
```
This will open a browser window to authorize your Google account and store `token.json`.

---

## Usage

### Basic Usage
```bash
# Normal run - adds new videos to playlist
python main.py

# Dry-run mode (shows what would be added without making changes)
python main.py --dry-run

# Verbose logging for debugging
python main.py --verbose

# Limit number of videos to process
python main.py --limit 20
```

### CSV Reporting
Generate a CSV report of all processed videos:
```bash
# Generate report with video metadata
python main.py --report videos_added.csv

# Combine with dry-run to see what would be processed
python main.py --dry-run --report preview.csv
```

The CSV report includes: title, video_id, channel_title, channel_id, published_at, duration_seconds, live_broadcast, added

### Environment Configuration
Key settings in `.env`:
```bash
# Skip livestreams and premieres (default: true)
SKIP_LIVE_CONTENT=true

# Minimum video duration in seconds
VIDEO_MIN_DURATION_SECONDS=120

# Hours to look back for new videos
LOOKBACK_HOURS=24

# Channel whitelist (comma-separated IDs, optional)
CHANNEL_ID_WHITELIST=UC1234567890,UC0987654321
```

---

## Automation

You can run the script on a schedule using `cron`:
```bash
0 * * * * /path/to/yt-sub-playlist/venv/bin/python /path/to/yt-sub-playlist/main.py >> /path/to/yt-sub-playlist/log.txt 2>&1
```

Or use APScheduler inside Python to run periodically.

---

## Folder Structure

```bash
.
├── auth.py               # OAuth flow and token management
├── main.py               # Playlist sync logic
├── youtube_api.py        # Wrapper functions for YouTube API calls
├── utils.py              # Time parsing, filtering, logging helpers
├── requirements.txt
├── client_secrets.json   # Your Google Cloud OAuth credentials
├── token.json            # Auto-generated user auth token
└── .env
```

---

## TODO
-	Add GUI or web dashboard (optional)
-	Option to remove old videos from playlist
-	Telegram or email alert for failures
-	JSON report format option