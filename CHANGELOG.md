# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## 4.1.0 (2025-10-27)


### Features

* add CSV reporting functionality with --report flag ([#2](https://github.com/yourusername/yt-sub-playlist/issues/2)) ([ea59302](https://github.com/yourusername/yt-sub-playlist/commit/ea593021b3aa34132224acd4d53c0aaca16b602b))
* add CSV reporting functionality with --report flag ([#3](https://github.com/yourusername/yt-sub-playlist/issues/3)) ([40825b5](https://github.com/yourusername/yt-sub-playlist/commit/40825b5eb6792f29ad036abca955bcba503a5ba8))
* add CSV reporting functionality with --report flag ([#4](https://github.com/yourusername/yt-sub-playlist/issues/4)) ([80efe1a](https://github.com/yourusername/yt-sub-playlist/commit/80efe1abb511ea0129fd4bad3b2ded431624ea71))
* add livestream and premiere filtering via SKIP_LIVE_CONTENT ([#1](https://github.com/yourusername/yt-sub-playlist/issues/1)) ([b4b95c6](https://github.com/yourusername/yt-sub-playlist/commit/b4b95c681b75f302df35ad45c47497b06fd995a7))
* **api:** reuse existing playlists instead of creating duplicates ([d7eaf34](https://github.com/yourusername/yt-sub-playlist/commit/d7eaf34e4b99e84c2d50cc5c68b6958d3fbf0d74))
* **automation:** implement automatic CSV-to-JSON conversion for dashboard ([5eb6930](https://github.com/yourusername/yt-sub-playlist/commit/5eb69301ed4f3a8a34da7e2eab7b7c2a26ee4230))
* **config:** implement Phase 3 configuration management system ([6c1ca4f](https://github.com/yourusername/yt-sub-playlist/commit/6c1ca4f2619e173d9ab898872d4112745547a09b))
* **config:** integrate config.json with CLI - Phase 3.1 ([8c50722](https://github.com/yourusername/yt-sub-playlist/commit/8c50722dffbeaa15e53906aa2d50e60d30c5f87e))
* **dashboard:** complete Phase 2 with backend integration and data pipeline ([225cd28](https://github.com/yourusername/yt-sub-playlist/commit/225cd287a2abd75424b58b6e75ab7ba9ff843d6b))
* **dashboard:** implement static playlist preview (Phase 1) ([bfbd5dd](https://github.com/yourusername/yt-sub-playlist/commit/bfbd5ddc115ea1dd738e32643b785b2067df1a9a))
* enhance quota error handling and early termination support ([0d4951d](https://github.com/yourusername/yt-sub-playlist/commit/0d4951d03ab8ebaad61233d27295ba2901f316e3))
* **filtering:** add date range filter with three modes (lookback/days/date_range) ([a09aea9](https://github.com/yourusername/yt-sub-playlist/commit/a09aea92d2476849a1dfd86f6a91275590df40e9))
* **filtering:** add duration range filter with max duration ([8c99333](https://github.com/yourusername/yt-sub-playlist/commit/8c9933311e1be1d681747901fb27369a243ae0c6))
* **filtering:** implement channel allowlist/blocklist system - Phase 4.1 ([e57c287](https://github.com/yourusername/yt-sub-playlist/commit/e57c287186e0be20835dc41fd4c75d61d8688d3d))
* **filtering:** implement Phase 5 advanced filtering system ([5d99c00](https://github.com/yourusername/yt-sub-playlist/commit/5d99c004caaba74332c0dbcbe9c0a3e271c4f53b))
* improved video search ([bdf905f](https://github.com/yourusername/yt-sub-playlist/commit/bdf905fccc6204bb7137bac9eb59b7139d7699b9))
* init creation and auth steps ([fa2ce0a](https://github.com/yourusername/yt-sub-playlist/commit/fa2ce0ac5f92f9136535108ec815f84afd53f3cd))
* quota tester to determine improvements ([2afff5c](https://github.com/yourusername/yt-sub-playlist/commit/2afff5c7772fab6318fc352c1f529fd16e2a29cc))
* **ui:** implement channel allowlist/blocklist management UI - Phase 4.2 ([6e10443](https://github.com/yourusername/yt-sub-playlist/commit/6e10443eed89694eb1e2b6cc5faa4a825896164b))


### Bug Fixes

* **bash:** we were clearing logs before directory creation ([d137131](https://github.com/yourusername/yt-sub-playlist/commit/d137131097da23ae422de200f46f02c090baccd3))
* clear logs directory (for now) ([558b742](https://github.com/yourusername/yt-sub-playlist/commit/558b742210f42831e72e022938772aff9fa969df))
* **report:** auto-create parent directory for CSV export ([15d1ea8](https://github.com/yourusername/yt-sub-playlist/commit/15d1ea8f03ee2ae5e84b0b3be89304e32f64826f))
* **server:** change backend port from 5000 to 5001 to avoid macOS AirPlay conflict ([939992e](https://github.com/yourusername/yt-sub-playlist/commit/939992e41a52f2f694e02b49b3de7a8ea0a2c7c0))


### Code Refactoring

* complete migration to modular package structure ([dc4a42c](https://github.com/yourusername/yt-sub-playlist/commit/dc4a42c0e0d685760147c30202a46901fc8c1abe))
* modularize project into package structure with updated README ([dc0327d](https://github.com/yourusername/yt-sub-playlist/commit/dc0327d93deef5cb8815c2343bcf6f479d9df42a))
* **ui:** replace emojis with Lucide icon library ([cfe14d1](https://github.com/yourusername/yt-sub-playlist/commit/cfe14d124f73aec2771a8efd0e3ecbfbefe0237f))


### Documentation

* add comprehensive documentation for Phase 4 and changelog automation ([0a367f2](https://github.com/yourusername/yt-sub-playlist/commit/0a367f2aac5ccd63779c74303ed95e438ba28b58))
* add Phase 2 documentation and update .gitignore ([47fd00c](https://github.com/yourusername/yt-sub-playlist/commit/47fd00c7d80bcf4232b542684a055ff786e7932a))
* add Phase 5.1 duration range filter documentation ([f62883d](https://github.com/yourusername/yt-sub-playlist/commit/f62883d0c62cdb23f05b7ac9536410c31392f72c))
* clarify autogenerated files in data/playlist_cache and api_call_log.json ([1833502](https://github.com/yourusername/yt-sub-playlist/commit/18335026d014e5fce351d41fb743c141ca9d8060))
* complete Phase 5 documentation with filtering guide ([33934ee](https://github.com/yourusername/yt-sub-playlist/commit/33934eef2c14b21be448875ce962a6f2e0c0429c))
* update readme with helper scripts ([d96b6a7](https://github.com/yourusername/yt-sub-playlist/commit/d96b6a7e46fb52fff4bec9ea186b0e4f4545c389))
* update README with helper scripts and CSV reporting instructions ([#5](https://github.com/yourusername/yt-sub-playlist/issues/5)) ([5e13260](https://github.com/yourusername/yt-sub-playlist/commit/5e1326048688e3d90161a83b15249baf68673db4))

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
