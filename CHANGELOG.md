# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 5: Advanced Filtering System ✅

Phase 5 introduces three major filtering enhancements that provide granular control over playlist content. All filters use AND logic (videos must pass all enabled filters) and are fully backward compatible.

#### Phase 5.1 - Duration Range Filter
- Added `max_duration_seconds` configuration field for upper duration limit
- Extended backend validation to enforce `max_duration >= min_duration` constraint
- Implemented "too_long" statistic tracking in video filtering pipeline
- Built max duration slider UI control (range: 60s - 7200s, 1-minute increments)
- Added "Unlimited" checkbox for disabling maximum duration limit
- Updated configuration summary to display duration as range when maximum is set
- Enhanced filtering statistics logging to show both "too_short" and "too_long" counts

**Use Cases Enabled:**
- Filter playlists to specific duration ranges (e.g., 5-20 minute videos only)
- Create "quick consumption" playlists under 10 minutes
- Build "deep dive" playlists with 30+ minute content only
- Exclude lengthy content while still filtering shorts

**Technical Details:**
- **Files Modified**: `yt_sub_playlist/config/schema.py`, `yt_sub_playlist/core/video_filtering.py`, `dashboard/config.html`, `dashboard/config.js`
- **Lines Changed**: 106 insertions, 10 deletions
- **Backward Compatible**: Default value is `null` (unlimited), existing configs unaffected

#### Phase 5.2 - Date Range Filter
- Added `date_filter_mode` configuration field with three modes: "lookback", "days", "date_range"
- Added `date_filter_days` field for "last N days" filtering (1-365 days)
- Added `date_filter_start` and `date_filter_end` fields for specific date ranges (YYYY-MM-DD format)
- Implemented comprehensive date validation (format checking, range logic, mode-specific requirements)
- Built date filter UI with mode dropdown and conditional input fields
- Implemented `_check_date_filter()` method with timezone handling and multiple date formats
- Added "outside_date_range" statistic tracking

**Date Filter Modes:**
- **Lookback**: Uses existing `lookback_hours` parameter (hourly precision, backward compatible)
- **Days**: "Last N days" from start of day (daily granularity, simpler than hours)
- **Date Range**: Specific start/end dates with date pickers (for events, archives)

**Use Cases Enabled:**
- Weekly content roundups with rolling 7-day windows
- Monthly archives with specific date ranges
- Event coverage with precise date boundaries
- Flexible time-based filtering beyond fixed lookback

**Technical Details:**
- **Files Modified**: Same 4 files as Phase 5.1 (iterative enhancement)
- **Lines Changed**: ~233 insertions total
- **Date Handling**: UTC timezone, RFC 3339 and ISO format support, end-of-day inclusion
- **Backward Compatible**: Default mode is "lookback", existing `lookback_hours` unchanged

#### Phase 5.3 - Keyword Filter
- Added `keyword_filter_mode` configuration field with four modes: "none", "include", "exclude", "both"
- Added `keyword_include` and `keyword_exclude` fields (list of strings)
- Added `keyword_match_type` field: "any" (OR logic) or "all" (AND logic) for include mode
- Added `keyword_case_sensitive` field (boolean, default false)
- Added `keyword_search_description` field (boolean, default false - title only)
- Implemented comprehensive keyword validation (list types, empty checks, mode requirements)
- Built keyword filter UI with textareas (one keyword per line) and advanced options panel
- Implemented `_check_keyword_filter()` method with flexible matching logic
- Added "keyword_filtered_include" and "keyword_filtered_exclude" statistic tracking

**Keyword Filter Modes:**
- **None**: No keyword filtering (default)
- **Include**: Videos must contain keyword(s) - whitelist approach
- **Exclude**: Videos must not contain any keywords - blacklist approach
- **Both**: Must match include AND not match exclude - combined filtering

**Advanced Options:**
- **Match Type**: "any" (OR) = at least one keyword, "all" (AND) = every keyword
- **Case Sensitive**: Enable for exact case matching (default: case-insensitive)
- **Search Description**: Search in video description, not just title (default: title only)

**Use Cases Enabled:**
- Tutorial-only playlists with include: ["tutorial", "guide", "how to"]
- Spoiler-free content with exclude: ["spoiler", "ending", "finale"]
- Specific topics with include: ["python", "tutorial"], match: all
- Curated content with both: include ["review"], exclude ["spoiler"]
- Case-sensitive language filtering (e.g., "Python" vs "python")
- Deep search in descriptions for comprehensive keyword matching

**Technical Details:**
- **Files Modified**: Same 4 files as Phase 5.1/5.2 (consistent architecture)
- **Lines Changed**: ~267 insertions
- **Matching**: Simple substring matching (not regex) for safety and simplicity
- **Backward Compatible**: Default mode is "none", no filtering applied

#### Phase 5.4 - Documentation & Polish
- Created comprehensive `docs/PHASE5_DESIGN.md` with complete Phase 5 architecture
- Updated README with detailed sections for all three filter types:
  - Duration Filtering (Phase 5.1)
  - Date Filtering (Phase 5.2 - new)
  - Keyword Filtering (Phase 5.3 - new)
  - Filter Execution Order (new section explaining AND logic and pipeline)
- Added filter combination examples with complete config and expected results
- Added statistics output examples showing filtering breakdown
- Updated example configurations throughout documentation

### Phase 5 Summary

**Total Implementation:**
- **Time**: ~2.5 hours (matched estimates perfectly)
- **Files Modified**: 4 core files (schema.py, video_filtering.py, config.html, config.js)
- **Lines Added**: ~600 across all sub-phases
- **Tests**: 13/13 passing (schema validation + video filtering)
- **Backward Compatible**: All new fields optional with sensible defaults

**Filter Capabilities:**
- ✅ Duration: min + max (range support)
- ✅ Date: 3 modes (lookback/days/date_range)
- ✅ Keywords: 4 modes (none/include/exclude/both) with flexible matching
- ✅ Channels: 3 modes (none/allowlist/blocklist) - from Phase 4
- ✅ Live content: skip/include toggle

**Filter Execution Pipeline:**
1. Already processed check (cache)
2. Duration filter (min/max)
3. Date filter (mode-specific)
4. Channel filter (allowlist/blocklist)
5. Keyword filter (include/exclude)
6. Live content filter

All filters use AND logic - videos must pass every enabled filter. Statistics tracked for each stage to help users tune their filters.

## [4.0.0] - 2025-10-26

### Added - Phase 4: Channel Allowlist/Blocklist System

#### Phase 4.2 - Frontend UI
- Channel management page (`dashboard/channels.html`) with complete filtering interface
- Three-mode visual selector (none/allowlist/blocklist) with interactive cards
- Real-time local search with 300ms debounce (no API quota usage)
- Channel selection UI with checkboxes and click-to-toggle functionality
- Bulk selection controls (select all/deselect all)
- Confirmation dialogs to prevent accidental selection loss during mode switching
- Integration with config page via "Manage Channels" button
- Graceful error handling for missing OAuth credentials
- Consistent styling with existing dashboard using Lucide icons
- Client-side state management with API-first architecture
- XSS protection with HTML escaping
- Auto-redirect after successful save

#### Phase 4.1 - Backend Implementation
- REST API endpoints for filter configuration (`GET/PUT /api/channels/filter-config`)
- Three mutually exclusive filter modes (none, allowlist, blocklist)
- Automatic migration from legacy `channel_whitelist` to `channel_allowlist`
- Mode switching logic with automatic opposite list clearing
- Channel filtering logic in video processing pipeline
- Configuration persistence to `config.json`
- Comprehensive error handling and validation
- Support for both set and list data structures in Python config loading

### Changed
- Updated configuration schema to support new filter modes
- Modified `video_filtering.py` to use new filtering system
- Enhanced `env_loader.py` to handle allowlist/blocklist configuration
- Updated dashboard navigation flow to include channel management

### Deprecated
- `channel_whitelist` configuration field (automatically migrated to `channel_allowlist`)

### Technical Details
- **Files Created**: `dashboard/channels.html` (382 lines), `dashboard/channels.js` (417 lines)
- **Files Modified**: `dashboard/config.html`, `yt_sub_playlist/config/schema.py`, `yt_sub_playlist/core/video_filtering.py`
- **API Endpoints**: 2 new endpoints for filter management
- **Testing**: Backend API testing, manual UI testing

---

## [3.1.0] - 2025-10-XX

### Added - Phase 3.1: CLI Integration with config.json

- CLI integration to read configuration from `config.json`
- Command-line arguments now work in conjunction with config file
- Configuration precedence system (CLI args → env vars → config.json → defaults)

### Changed
- Enhanced `env_loader.py` to support multi-source configuration loading
- Updated CLI argument parsing to respect config file settings

---

## [3.0.0] - 2025-10-XX

### Added - Phase 3: Configuration Management System

- Web-based configuration UI (`dashboard/config.html`)
- Interactive settings page with visual controls and validation
- `config.json` file for persistent user preferences
- REST API endpoints for configuration management:
  - `GET /api/config` - Retrieve current configuration
  - `PUT /api/config` - Update configuration settings
- Real-time configuration validation with user-friendly error messages
- Configuration schema with validation rules and defaults
- Support for all core settings:
  - Playlist name and visibility
  - Video duration filtering
  - Lookback hours
  - Max videos per run
  - Live content filtering
  - Channel whitelist (legacy)

### Changed
- Centralized configuration management in `config/schema.py`
- Enhanced `env_loader.py` to support JSON config files
- Improved configuration precedence system

### Technical Details
- **Files Created**: `dashboard/config.html`, `dashboard/config.js`, `yt_sub_playlist/config/schema.py`
- **API Endpoints**: 2 new configuration endpoints
- **Configuration Sources**: CLI args, environment variables, config.json, built-in defaults

---

## [2.0.0] - 2025-10-XX

### Added - Phase 2: Web Dashboard

- Flask-based web dashboard backend (`dashboard/backend/app.py`)
- Modern responsive web UI for playlist management
- Main dashboard page (`dashboard/index.html`) with:
  - Playlist statistics and video counts
  - YouTube API quota usage monitoring
  - Last refresh timestamp
  - Quick action buttons (refresh, view playlist)
- REST API endpoints:
  - `GET /api/playlist` - Retrieve playlist data and statistics
  - `GET /api/status` - Server status and last run information
  - `GET /api/stats/quota` - YouTube API quota usage
  - `GET /api/stats/cache` - Video cache statistics
  - `GET /api/channels` - List subscribed channels
  - `GET /api/channels/search` - Search channels
- Real-time server status monitoring
- Responsive CSS styling with modern design

### Changed
- Refactored emoji usage across UI (later replaced with Lucide icons)
- Enhanced error handling for API endpoints
- Improved quota tracking integration

### Technical Details
- **Technology Stack**: Flask, vanilla JavaScript, HTML/CSS
- **Files Created**: Multiple dashboard files in `dashboard/` directory
- **API Endpoints**: 8+ REST endpoints for dashboard functionality

---

## [1.0.0] - 2025-10-XX

### Added - Phase 1: Core CLI Tool

- Initial release of YouTube subscription playlist manager
- Command-line interface for playlist management
- YouTube Data API v3 integration with OAuth2 authentication
- Quota-optimized API usage with batching and caching
- Automated quota tracking system:
  - Real-time API call monitoring
  - Persistent call logging (`data/api_call_log.json`)
  - Quota usage simulator and analyzer
- Video filtering capabilities:
  - Minimum duration requirements
  - Live content filtering (livestreams/premieres)
  - Channel whitelist support
  - Lookback time window
- Intelligent duplicate detection with caching
- CSV report generation with detailed metadata
- Comprehensive error handling and retry logic
- Shell scripts for common operations:
  - `run.sh` - Production execution
  - `dryrun.sh` - Dry-run mode
  - `reset-auth.sh` - Authentication reset
  - `quota_test.sh` - Quota analysis
- Centralized quota cost management:
  - JSON-based quota cost configuration
  - Dynamic cost loading with fallbacks
  - Method-level quota tracking

### Core Modules
- **`core/youtube_client.py`** - YouTube API wrapper with optimization
- **`core/video_filtering.py`** - Video filtering and processing logic
- **`core/playlist_manager.py`** - High-level playlist orchestration
- **`core/quota_tracker.py`** - Quota management and estimation
- **`auth/oauth.py`** - OAuth2 authentication handling
- **`config/env_loader.py`** - Environment configuration management
- **`config/quota_costs.py`** - Quota cost management

### Features
- Batched operations (up to 50 videos per API call)
- Smart caching with 12-hour TTL
- Playlist content caching to prevent reprocessing
- Dry-run mode for testing
- Verbose logging for debugging
- CSV reporting with video metadata
- Cron-friendly design for automation

### Configuration
- Environment variable support via `.env` file
- Configurable playlist settings (name, visibility)
- Flexible filtering options (duration, lookback, max videos)
- Channel whitelist support
- Built-in defaults for all settings

### Quota Optimization
- 85-90% quota reduction through intelligent batching
- Real-time quota usage tracking
- Automated call counting and cost calculation
- Detailed per-method usage breakdown
- Quota simulator for usage analysis

---

## Version History Summary

- **v4.0.0** - Channel allowlist/blocklist system with web UI
- **v3.1.0** - CLI integration with config.json
- **v3.0.0** - Configuration management UI and REST API
- **v2.0.0** - Web dashboard interface
- **v1.0.0** - Core CLI tool with quota optimization

---

## Migration Notes

### Upgrading to 4.0.0
- The legacy `channel_whitelist` configuration is automatically migrated to `channel_allowlist`
- No manual intervention required for existing configurations
- The new filter system is backward-compatible

### Upgrading to 3.0.0
- Configuration can now be managed via web UI at `/config.html`
- Existing `.env` configurations continue to work
- `.env` values take precedence over `config.json`

### Upgrading to 2.0.0
- Start the dashboard with: `cd dashboard/backend && python app.py`
- Dashboard accessible at `http://localhost:5001`
- CLI tool continues to work independently

---

## Links

- [Repository](https://github.com/yourusername/yt-sub-playlist)
- [Documentation](README.md)
- [Issues](https://github.com/yourusername/yt-sub-playlist/issues)

---

## Automated Changelog Generation

This project follows [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

- `feat:` - New features
- `fix:` - Bug fixes
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `chore:` - Maintenance tasks

To generate changelog entries automatically, use tools like:
- [conventional-changelog](https://github.com/conventional-changelog/conventional-changelog)
- [standard-version](https://github.com/conventional-changelog/standard-version)
- [release-please](https://github.com/googleapis/release-please)
