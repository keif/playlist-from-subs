# yt-sub-playlist

Automatically sync your latest YouTube subscription uploads into a custom playlist using the YouTube Data API v3.

> A Python-powered automation tool that creates or updates a playlist with your most recent subscribed content — filtered, customizable, and cron-friendly.

---

## Features

- Pulls uploads from your subscribed channels
- Adds them to a target playlist (new or existing)
- Filters out:
  - Shorts or very short videos (e.g. under 60s)
  - Livestreams (optional)
  - Member-only videos (optional, via metadata filtering)
- Configurable daily cron job
- OAuth2 token flow for secure access
- Logging and dry-run support

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
```bash
python main.py
```

For dry-run mode (no actual playlist modification):
```bash
python main.py --dry-run
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
-	Add livestream/member-only skip logic
-	Add GUI or web dashboard (optional)
-	Option to remove old videos from playlist
-	Telegram or email alert for failures