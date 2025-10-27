# yt-sub-playlist

Automatically sync your latest YouTube subscription uploads into a custom playlist using the YouTube Data API v3.

> A modular Python package that creates or updates a playlist with your most recent subscribed content — filtered, customizable, and cron-friendly.

---

## Features

- **Web Dashboard Interface** - Modern UI for managing playlists, configuration, and channel filtering
- **Quota-optimized API usage** - Batched operations reduce quota consumption by 95%+
- **Automated quota tracking** - Real-time API call monitoring with detailed usage analysis
- **Intelligent duplicate detection** - Pre-insertion caching prevents wasted API calls
- **Flexible video filtering**:
  - Duration range filtering (minimum and maximum duration support)
  - Live content filtering (livestreams/premieres)
  - Channel allowlist/blocklist support (three modes: none, allowlist, blocklist)
  - Custom filtering rules
- **Channel Management UI** - Visual interface for managing channel filters with real-time search
- **Robust error handling** - Retry logic and graceful degradation
- **Multiple interfaces** - Web dashboard, command-line tool, and shell scripts
- **Comprehensive reporting** - CSV reports with detailed metadata
- **Automated scheduling** - Cron-friendly design with proper logging
- **Dynamic quota management** - Centralized cost configuration with intelligent fallbacks
- **Configuration Management** - JSON-based config with web UI and precedence system

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
    │   ├── schema.py             # Configuration validation and defaults
    │   ├── quota_costs.py        # YouTube API quota cost management
    │   └── youtube_quota_costs.json # Centralized quota cost configuration
    ├── data/
    │   ├── processed_videos.json # Cache of processed video IDs
    │   ├── playlist_cache/       # Cached playlist contents
    │   ├── api_call_log.json     # (Ignored) Real-time API usage tracking; not committed
    │   └── logs/                 # Application logs
    ├── scripts/
    │   ├── run.sh               # Production runner script
    │   ├── dryrun.sh            # Dry-run testing script
    │   ├── reset-auth.sh        # Authentication reset utility
    │   ├── quota_test.sh        # Quota usage simulator runner
    │   └── quota_simulator.py   # Quota estimation utility
    └── reports/
        └── videos_added.csv     # Generated reports
    ```

### Module Overview

- **`core/youtube_client.py`** - Low-level YouTube API operations with batching, caching, and automated call tracking
- **`core/video_filtering.py`** - Video filtering logic and criteria management
- **`core/playlist_manager.py`** - High-level workflow orchestration
- **`core/quota_tracker.py`** - Quota management and estimation utilities
- **`auth/oauth.py`** - OAuth2 flow and credential management
- **`config/env_loader.py`** - Configuration loading and validation
- **`config/schema.py`** - Configuration contracts and defaults
- **`config/quota_costs.py`** - YouTube API quota cost management and loading

---

## Usage

### Web Dashboard (Recommended)

The easiest way to use yt-sub-playlist is through the web dashboard:

```bash
# Start the dashboard server
cd dashboard/backend && python app.py

# Open in your browser
# http://localhost:5001
```

**Dashboard Features:**
- **Main Dashboard** (`/`) - View playlist statistics, quota usage, and manage playlists
- **Settings** (`/config.html`) - Configure all options with visual controls and validation
- **Channel Manager** (`/channels.html`) - Manage channel allowlist/blocklist with search and filtering

### Command-Line Interface

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

# Run quota usage simulator
./yt_sub_playlist/scripts/quota_test.sh
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

### Configuration

**Two Configuration Methods:**

1. **Web Dashboard** (Recommended): Start the dashboard and use the Settings page to manage configuration visually:
   ```bash
   cd dashboard/backend && python app.py
   # Open http://localhost:5001/config.html
   ```

2. **Manual Configuration**: Edit configuration files directly (see below)

**Configuration Sources & Precedence:**

The system loads configuration from multiple sources with the following priority (highest to lowest):

1. **CLI arguments** (e.g., `--limit 10`)
2. **Environment variables** (`.env` file) - for secrets and overrides
3. **User preferences** (`config.json` file) - managed via dashboard
4. **Built-in defaults**

**Environment Variables (`.env`):**

Use for secrets and system-specific overrides:

```bash
# API credentials (secrets - must be in .env)
PLAYLIST_ID=PLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Optional: use existing playlist

# User preferences (can be overridden in config.json via dashboard)
PLAYLIST_NAME="My Auto Playlist"              # Name for new playlists
PLAYLIST_VISIBILITY=unlisted                  # private, unlisted, or public
VIDEO_MIN_DURATION_SECONDS=120               # Skip videos shorter than 2 minutes
SKIP_LIVE_CONTENT=true                       # Skip livestreams and premieres
CHANNEL_ID_WHITELIST=UC1234,UC5678          # Optional: only include these channels
LOOKBACK_HOURS=24                            # How far back to look for videos
MAX_VIDEOS_TO_FETCH=50                       # Maximum videos to process per run
```

**User Preferences (`config.json`):**

Automatically created when using the dashboard Settings page. Example:

```json
{
  "playlist_name": "Auto Playlist from Subscriptions",
  "playlist_visibility": "unlisted",
  "min_duration_seconds": 120,
  "max_duration_seconds": null,
  "lookback_hours": 48,
  "max_videos": 50,
  "skip_live_content": true,
  "channel_filter_mode": "none",
  "channel_allowlist": null,
  "channel_blocklist": null
}
```

**Note**: Values in `.env` take precedence over `config.json`. This allows you to override dashboard settings when needed.

---

## Channel Filtering

Control which channels contribute videos to your playlist using three mutually exclusive modes:

### Filter Modes

**1. None (Default)**
- All subscribed channels are included
- No filtering applied

**2. Allowlist Mode**
- Only channels in the allowlist contribute videos
- All other channels are excluded
- Useful when you want content from specific creators only

**3. Blocklist Mode**
- All channels except those in the blocklist contribute videos
- Useful for excluding specific channels while including everyone else

### Managing Channel Filters

**Via Web Dashboard (Recommended):**

1. Start the dashboard: `cd dashboard/backend && python app.py`
2. Navigate to Settings → Channel Filtering → "Manage Channels"
3. Select your filter mode (none/allowlist/blocklist)
4. Search and select channels
5. Save configuration

**Via config.json:**

```json
{
  "channel_filter_mode": "allowlist",
  "channel_allowlist": ["UCxxxxxx1", "UCxxxxxx2"],
  "channel_blocklist": null
}
```

**Via Environment Variables:**

```bash
# Allowlist mode
CHANNEL_FILTER_MODE=allowlist
CHANNEL_ALLOWLIST=UCxxxxxx1,UCxxxxxx2

# Blocklist mode
CHANNEL_FILTER_MODE=blocklist
CHANNEL_BLOCKLIST=UCxxxxxx3,UCxxxxxx4
```

### Migration from Whitelist

The legacy `channel_whitelist` configuration is automatically migrated to `channel_allowlist` when using the new filter system. Your existing whitelist will continue to work seamlessly.

### Use Cases

**Allowlist Examples:**
- Create a playlist from your top 5 favorite channels
- Focus on educational content creators only
- Build a curated playlist for a specific topic

**Blocklist Examples:**
- Exclude gaming channels from your general playlist
- Remove channels that post too frequently
- Filter out channels with content you've already watched elsewhere

---

## Duration Filtering

Control the length of videos included in your playlist using minimum and maximum duration filters.

### Duration Range

Set both minimum and maximum duration limits to create precisely filtered playlists:

- **Minimum Duration** (`min_duration_seconds`): Skip videos shorter than this (default: 60 seconds)
- **Maximum Duration** (`max_duration_seconds`): Skip videos longer than this (default: unlimited/null)

### Configuration

**Via Web Dashboard:**
1. Navigate to Settings page (`http://localhost:5001/config.html`)
2. Adjust the "Min Duration" slider (range: 1s - 7200s)
3. Adjust the "Max Duration" slider (range: 60s - 7200s)
4. Check "Unlimited" for no maximum duration limit
5. Click "Save Configuration"

**Via config.json:**
```json
{
  "min_duration_seconds": 120,
  "max_duration_seconds": 1800
}
```

Set `max_duration_seconds` to `null` for unlimited maximum duration.

### Use Cases

**Skip Shorts AND Long Videos:**
- Min: 300s (5 minutes), Max: 1200s (20 minutes)
- Perfect for focused, mid-length content

**Quick Consumption Playlist:**
- Min: 60s (1 minute), Max: 600s (10 minutes)
- Great for quick viewing sessions

**Deep Dive Content Only:**
- Min: 1800s (30 minutes), Max: null (unlimited)
- Focus on in-depth tutorials and lectures

**No Lengthy Content:**
- Min: 60s (1 minute), Max: 900s (15 minutes)
- Avoid time-consuming videos

### Statistics

The filtering process tracks duration-based exclusions:
- **too_short**: Videos rejected for being under minimum duration
- **too_long**: Videos rejected for exceeding maximum duration

These statistics appear in logs and help tune your duration range settings.

---

## Date Filtering

Control which videos are included based on their publish date using flexible date filtering modes.

### Date Filter Modes

Choose from three different date filtering approaches:

**1. Lookback Mode** (default)
- Uses `lookback_hours` parameter for hourly precision
- Example: "Last 24 hours", "Last 48 hours"
- Best for: Frequent updates, recent content focus

**2. Days Mode**
- Filter by "last N days" with daily granularity
- Range: 1-365 days
- Cutoff is start of day (00:00:00)
- Example: "Last 7 days" includes all videos from 7 days ago at midnight to now
- Best for: Weekly/monthly playlists, consistent rolling windows

**3. Date Range Mode**
- Filter by specific start and end dates
- Date picker interface (YYYY-MM-DD format)
- End date includes full day (23:59:59)
- Example: "October 1-27, 2025"
- Best for: Event coverage, monthly archives, specific time periods

### Configuration

**Via Web Dashboard:**
1. Navigate to Settings page (`http://localhost:5001/config.html`)
2. Select "Date Filter Mode" from dropdown
3. Configure based on selected mode:
   - **Lookback**: Adjust hours slider (1-168 hours)
   - **Days**: Enter number of days (1-365)
   - **Date Range**: Select start and end dates
4. Click "Save Configuration"

**Via config.json:**
```json
{
  "date_filter_mode": "days",
  "date_filter_days": 7,
  "date_filter_start": null,
  "date_filter_end": null
}
```

Or for date range mode:
```json
{
  "date_filter_mode": "date_range",
  "date_filter_days": null,
  "date_filter_start": "2025-10-01",
  "date_filter_end": "2025-10-27"
}
```

### Use Cases

**Weekly Content Roundup:**
- Mode: days
- Days: 7
- Result: Rolling 7-day window for weekly playlists

**Monthly Archives:**
- Mode: date_range
- Start: 2025-10-01, End: 2025-10-31
- Result: All October 2025 videos

**Recent Updates Only:**
- Mode: lookback
- Hours: 24
- Result: Videos from last 24 hours (backward compatible)

**Event Coverage:**
- Mode: date_range
- Start: 2025-10-15, End: 2025-10-20
- Result: Videos published during specific event dates

### Statistics

The filtering process tracks date-based exclusions:
- **outside_date_range**: Videos rejected for being outside the configured date filter

These statistics appear in logs and show which date filter mode is active.

---

## Keyword Filtering

Filter videos based on keywords found in their title or description, with flexible matching options.

### Keyword Filter Modes

Choose from four filtering approaches:

**1. None** (default)
- No keyword filtering applied
- All videos pass keyword filter

**2. Include Mode** (whitelist)
- Videos must contain specific keyword(s)
- Match type options:
  - **Any**: Video needs at least one keyword (OR logic)
  - **All**: Video needs every keyword (AND logic)
- Example: Include ["tutorial", "guide"] with "any" = videos containing "tutorial" OR "guide"

**3. Exclude Mode** (blacklist)
- Videos must NOT contain any exclude keywords
- Always uses OR logic (any match = reject)
- Example: Exclude ["spoiler", "ending"] = reject videos with "spoiler" OR "ending"

**4. Both Mode** (combined)
- Must pass include check (with any/all logic)
- Must NOT match any exclude keywords
- Example: Include ["review"] + Exclude ["spoiler"] = reviews without spoilers

### Configuration

**Via Web Dashboard:**
1. Navigate to Settings page (`http://localhost:5001/config.html`)
2. Select "Keyword Filter Mode" from dropdown
3. Enter keywords (one per line) in appropriate text area:
   - **Include Keywords**: For include/both modes
   - **Exclude Keywords**: For exclude/both modes
4. Configure advanced options (for include/both modes):
   - **Match Type**: "any" (OR) or "all" (AND) for include keywords
   - **Case Sensitive**: Enable for exact case matching
   - **Search Description**: Enable to search video descriptions (not just titles)
5. Click "Save Configuration"

**Via config.json:**
```json
{
  "keyword_filter_mode": "include",
  "keyword_include": ["tutorial", "guide", "how to"],
  "keyword_exclude": null,
  "keyword_match_type": "any",
  "keyword_case_sensitive": false,
  "keyword_search_description": false
}
```

Or for both mode:
```json
{
  "keyword_filter_mode": "both",
  "keyword_include": ["review", "analysis"],
  "keyword_exclude": ["spoiler", "clickbait"],
  "keyword_match_type": "any",
  "keyword_case_sensitive": false,
  "keyword_search_description": false
}
```

### Use Cases

**Tutorial Content Only:**
- Mode: include
- Keywords: ["tutorial", "guide", "how to"]
- Match: any
- Result: Only educational/instructional content

**Avoid Spoilers:**
- Mode: exclude
- Keywords: ["spoiler", "ending", "finale", "twist"]
- Result: No spoiler-containing videos

**Specific Topic (Strict):**
- Mode: include
- Keywords: ["python", "tutorial"]
- Match: all
- Result: Only videos with BOTH "python" AND "tutorial"

**Curated Reviews:**
- Mode: both
- Include: ["review", "analysis"]
- Exclude: ["spoiler", "unboxing"]
- Result: Reviews and analysis without spoilers or unboxings

**Case-Sensitive Filtering:**
- Mode: include
- Keywords: ["Python"]  (capital P)
- Case Sensitive: enabled
- Result: Matches "Python" but not "python"

**Deep Search:**
- Mode: include
- Keywords: ["machine learning"]
- Search Description: enabled
- Result: Finds keyword in title OR description

### Advanced Options

**Match Type** (for include mode):
- **Any (OR)**: Video needs at least one include keyword
- **All (AND)**: Video needs every include keyword

**Case Sensitive**:
- Default: false (case-insensitive matching)
- When enabled: "Python" ≠ "python"

**Search Description**:
- Default: false (title only)
- When enabled: searches both title and description text

### Statistics

The filtering process tracks keyword-based exclusions:
- **keyword_filtered_include**: Videos rejected for not matching include keywords
- **keyword_filtered_exclude**: Videos rejected for matching exclude keywords

These statistics appear in logs and help tune your keyword filters.

---

## Filter Execution Order

All filters use AND logic - videos must pass every enabled filter to be included in the playlist.

**Filtering Pipeline:**

1. **Already Processed Check**: Skip videos already in playlist (cache lookup)
2. **Duration Filter**: Check min/max duration constraints
3. **Date Filter**: Check publish date against selected mode (lookback/days/date_range)
4. **Channel Filter**: Check allowlist/blocklist (if enabled)
5. **Keyword Filter**: Check include/exclude keywords (if enabled)
6. **Live Content Filter**: Skip livestreams/premieres (if enabled)

**Filter Combination Example:**

```json
{
  "min_duration_seconds": 300,
  "max_duration_seconds": 1200,
  "date_filter_mode": "days",
  "date_filter_days": 7,
  "channel_filter_mode": "allowlist",
  "channel_allowlist": ["UCxxxxx", "UCyyyyy"],
  "keyword_filter_mode": "both",
  "keyword_include": ["tutorial"],
  "keyword_exclude": ["beginner"],
  "skip_live_content": true
}
```

This configuration creates a playlist with:
- ✅ Videos between 5-20 minutes long
- ✅ Published in the last 7 days
- ✅ From specific whitelisted channels
- ✅ Containing "tutorial" in title
- ✅ NOT containing "beginner" in title
- ✅ No livestreams or premieres

**Result**: Intermediate/advanced tutorials from trusted creators, published recently.

**Statistics Output:**

The filtering process logs statistics for each stage:
```
Video filtering stats:
  Total videos: 50
  Already processed: 5
  Too short (<300s): 8
  Too long (>1200s): 6
  Outside date range (days mode): 4
  Not in allowlist: 12
  Keyword filtered (include): 3
  Keyword filtered (exclude): 2
  Live content skipped: 1
  Passed filters: 9
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

This tool is designed to minimize YouTube API quota usage with intelligent monitoring:

### Core Optimizations
- **Batched operations** - Up to 50 videos per API call
- **Smart caching** - 12-hour TTL for playlist contents
- **Duplicate detection** - Pre-insertion filtering prevents waste
- **Efficient subscription handling** - Uses uploads playlist lookup vs expensive search

### Automated Quota Tracking
- **Real-time API monitoring** - Every API call is automatically tracked
- **Dynamic quota analysis** - Live usage data replaces static estimates
- **Centralized cost management** - All quota costs stored in `config/youtube_quota_costs.json`
- **Intelligent reporting** - Detailed per-method breakdown with call counts and costs

### Usage Analysis

Run the quota simulator to analyze your actual API usage:

```bash
# After running the main application, analyze real usage
./yt_sub_playlist/scripts/quota_test.sh

# Or run directly
python yt_sub_playlist/scripts/quota_simulator.py
```

**Sample output**:
```
📄 Loaded API call counts from yt_sub_playlist/data/api_call_log.json

📊 Quota Usage Analysis:
  channels.list            :  15 calls ×  1 units =   15 units
  subscriptions.list       :   3 calls ×  1 units =    3 units
  playlistItems.list       :  12 calls ×  1 units =   12 units
  videos.list              :   8 calls ×  1 units =    8 units
  playlistItems.insert     :  45 calls × 50 units = 2250 units
  playlists.list           :   1 calls ×  1 units =    1 units

🔢 Total Estimated Usage: 2289 / 10000 units
```

**Typical quota usage**:
- Before optimization: ~8,000 units per run
- After optimization: ~500-1,000 units per run
- **~85-90% quota reduction**

---

## Quota Configuration Management

### Centralized Cost Configuration

All YouTube API quota costs are managed in `config/youtube_quota_costs.json`:

```json
{
  "channels.list": 1,
  "playlistItems.insert": 50,
  "playlistItems.list": 1,
  "playlists.list": 1,
  "subscriptions.list": 1,
  "videos.list": 1,
  "search.list": 100,
  "playlists.insert": 50
}
```

### Dynamic Cost Loading

The system automatically loads quota costs at runtime with intelligent fallbacks:

```python
from yt_sub_playlist.config.quota_costs import get_quota_cost

# Automatically loads from JSON config with fallback to default (1)
cost = get_quota_cost("videos.list")  # Returns: 1
cost = get_quota_cost("playlistItems.insert")  # Returns: 50
cost = get_quota_cost("unknown.method")  # Returns: 1 (with warning log)
```

### Automated Tracking

Every API call is automatically tracked without manual intervention:

- **Real-time counting** - All YouTube API methods are instrumented
- **Persistent logging** - Usage data saved to `data/api_call_log.json`
- **Session tracking** - Counters persist across application runs
- **Error resilience** - Tracking continues even if individual API calls fail

### Quota Analysis Workflow

1. **Run your application**: `python -m yt_sub_playlist`
2. **API calls are tracked automatically** - No configuration needed
3. **Analyze real usage**: `./yt_sub_playlist/scripts/quota_test.sh`
4. **Optimize based on data** - Focus on high-cost operations

---

## Ignored Files and Folders

The following files are automatically generated at runtime and excluded from version control:

- `data/playlist_cache/*.json` — Cached playlist contents (used to prevent reprocessing and reduce API quota usage)
- `data/api_call_log.json` — Real-time API usage tracking used by the quota simulator

> These are listed in `.gitignore` to ensure they are not committed.

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

## Project Roadmap

### Completed Features ✅
- [x] Web dashboard interface (Phases 2-4)
- [x] Channel allowlist/blocklist filtering (Phase 4)
- [x] Configuration management UI (Phase 3)
- [x] Real-time quota tracking and monitoring
- [x] CSV reporting with detailed metadata
- [x] Automated duplicate detection

### Future Enhancements
- [ ] Scheduling system with cron integration
- [ ] Analytics dashboard (playlist growth, channel stats)
- [ ] Multi-playlist support
- [ ] Advanced video filtering rules (duration ranges, keyword filters, date ranges)
- [ ] Notification integrations (email, Slack, Discord)
- [ ] Playlist cleanup (remove old videos)
- [ ] Docker container support
- [ ] Channel metadata display (thumbnails, subscriber counts)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/) format:
   ```bash
   git commit -m 'feat(scope): add amazing feature'
   ```
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Format

This project uses Conventional Commits for automatic changelog generation:

- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `test:` - Test additions
- `chore:` - Maintenance tasks

**Examples:**
```bash
git commit -m "feat(ui): add dark mode support"
git commit -m "fix(api): resolve quota tracking issue"
git commit -m "docs(readme): update installation instructions"
```

See [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for details on changelog automation.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.