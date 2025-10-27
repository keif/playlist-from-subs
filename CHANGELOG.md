# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
