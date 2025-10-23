# Phase 3: Configuration UI Design

## Overview
Add a configuration interface to the dashboard for managing playlist settings, channel whitelists, and viewing system stats without editing environment files.

## Current Configuration System

### Configurable Parameters
| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `playlist_name` | String | - | "Auto Playlist from Subscriptions" | Name of the YouTube playlist |
| `playlist_visibility` | Enum | private, unlisted, public | unlisted | Playlist visibility setting |
| `min_duration_seconds` | Integer | 0-86400 | 60 | Minimum video duration (seconds) |
| `lookback_hours` | Integer | 1-168 | 24 | How far back to search (hours) |
| `max_videos` | Integer | 1-200 | 50 | Maximum videos to fetch |
| `skip_live_content` | Boolean | true/false | true | Skip live streams and premieres |
| `channel_whitelist` | Set[String] | - | None | Optional channel ID whitelist |

### Current Storage
- Configuration loaded from `.env` file
- Managed by `config/env_loader.py`
- Validated by `config/schema.py`

## Phase 3 Features

### 1. Configuration Management
**API Endpoints:**
```
GET  /api/config          - Get current configuration
PUT  /api/config          - Update configuration
POST /api/config/validate - Validate config without saving
GET  /api/config/defaults - Get default values
```

**Frontend UI:**
- Form with all configurable parameters
- Real-time validation (ranges, types)
- Preview mode to test changes before saving
- Reset to defaults button
- Save configuration button

### 2. Channel Management
**API Endpoints:**
```
GET /api/channels              - List all subscribed channels
GET /api/channels/whitelisted  - Get current whitelist
PUT /api/channels/whitelist    - Update whitelist
```

**Frontend UI:**
- Searchable table of subscribed channels
- Checkboxes to enable/disable channels
- "Select All" / "Deselect All" buttons
- Filter by channel name
- Show channel stats (video count, last upload)

### 3. System Stats & Monitoring
**API Endpoints:**
```
GET /api/quota         - Get API quota usage stats
GET /api/stats/filters - Get last run filtering stats
GET /api/stats/cache   - Get cache statistics
```

**Frontend UI:**
- Quota usage dashboard (daily usage, remaining quota)
- Filter stats from last run (videos filtered, reasons)
- Cache stats (total processed videos, cache age)
- Visual charts/graphs for stats

### 4. Advanced Features
**API Endpoints:**
```
POST /api/preview   - Run with custom config (dry run, don't save)
POST /api/refresh   - Run with current saved config
```

**Frontend UI:**
- "Preview Changes" button (runs dry run with new settings)
- "Apply & Refresh" button (saves config + triggers refresh)
- Live progress indicator for long-running operations
- Result comparison (before/after video counts)

## Implementation Plan

### Backend Changes

#### 1. New API Module: `dashboard/backend/config_api.py`
```python
from flask import Blueprint, request, jsonify
from yt_sub_playlist.config import ConfigSchema, load_config

config_bp = Blueprint('config', __name__)

@config_bp.route('/api/config', methods=['GET'])
def get_config():
    """Return current configuration"""
    pass

@config_bp.route('/api/config', methods=['PUT'])
def update_config():
    """Update and save configuration"""
    pass

@config_bp.route('/api/config/validate', methods=['POST'])
def validate_config():
    """Validate config without saving"""
    pass
```

#### 2. Configuration Persistence
**Options:**
1. **Option A: Update .env file** (simpler, but requires file parsing)
2. **Option B: Use config.json** (easier to read/write, separate from secrets)
3. **Option C: Hybrid** (secrets in .env, settings in config.json)

**Recommended: Option C**
- Keep API credentials in `.env` (gitignored)
- Store user preferences in `config.json` (can be committed)
- Merge both sources in `load_config()`

#### 3. Channel Data API
```python
@channels_bp.route('/api/channels', methods=['GET'])
def get_channels():
    """Get all subscribed channels with metadata"""
    # Fetch from YouTube API or cache
    pass
```

### Frontend Changes

#### 1. New Page: Configuration Settings
**File: `dashboard/config.html`**
- Dedicated configuration page
- Accessible from main dashboard nav
- Organized in sections (playlist, filters, channels)

#### 2. Configuration Form Component
**Sections:**
1. **Playlist Settings**
   - Name input
   - Visibility dropdown

2. **Video Filters**
   - Duration slider (0-24 hours)
   - Lookback period slider (1-168 hours)
   - Max videos slider (1-200)
   - Skip live content checkbox

3. **Channel Whitelist**
   - Searchable channel list
   - Toggle all / none buttons
   - Save whitelist button

4. **Actions**
   - Preview button (test changes)
   - Save button (persist changes)
   - Reset button (revert to defaults)

#### 3. Stats Dashboard Component
**File: `dashboard/stats.html` or add to main page**
- Quota usage chart
- Filter statistics
- Cache information

### Data Flow

```
User modifies config in UI
    ↓
Frontend validates input (client-side)
    ↓
User clicks "Preview"
    ↓
POST /api/preview with config
    ↓
Backend runs dry-run with config
    ↓
Returns preview results
    ↓
User reviews results
    ↓
User clicks "Save & Apply"
    ↓
PUT /api/config (saves to config.json)
    ↓
POST /api/refresh (runs CLI with new config)
    ↓
Dashboard updates with new data
```

## UI Mockup

### Configuration Page Layout
```
┌─────────────────────────────────────────────┐
│  Playlist Configuration                     │
│                                             │
│  Playlist Settings                          │
│  ┌───────────────────────────────────────┐  │
│  │ Name: [Auto Playlist from Subs      ] │  │
│  │ Visibility: [Unlisted ▼]              │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Video Filters                              │
│  ┌───────────────────────────────────────┐  │
│  │ Min Duration: [60s]  [====|----------] │  │
│  │ Lookback: [24h]      [====|----------] │  │
│  │ Max Videos: [50]     [====|----------] │  │
│  │ ☑ Skip live content                   │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Channel Whitelist                          │
│  ┌───────────────────────────────────────┐  │
│  │ Search: [____________] 🔍             │  │
│  │ ☐ Select All  ☐ Clear All            │  │
│  │                                       │  │
│  │ ☑ Channel Name 1     (42 videos)     │  │
│  │ ☑ Channel Name 2     (18 videos)     │  │
│  │ ☐ Channel Name 3     (7 videos)      │  │
│  │ ...                                   │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  [Preview Changes]  [Save & Apply]  [Reset] │
└─────────────────────────────────────────────┘
```

### Stats Panel (on main dashboard)
```
┌─────────────────────────────────────────────┐
│  System Stats                               │
│                                             │
│  API Quota: 8,450 / 10,000 (84% used)      │
│  ████████████░░░░                          │
│                                             │
│  Last Run:                                  │
│  • Total videos: 111                        │
│  • Passed filters: 89                       │
│  • Too short: 12                            │
│  • Live content: 8                          │
│  • Already processed: 2                     │
│                                             │
│  Cache: 1,247 videos (14 days old)         │
│                                             │
│  [View Detailed Stats]                     │
└─────────────────────────────────────────────┘
```

## Testing Plan

### Manual Testing
1. Load configuration page
2. Modify each setting
3. Validate client-side validation works
4. Test preview with different configs
5. Save configuration and verify persistence
6. Verify CLI uses new configuration
7. Test channel whitelist management
8. Verify stats display correctly

### Edge Cases
- Invalid configuration values
- Empty whitelist vs. no whitelist (all channels)
- Concurrent configuration updates
- Configuration file missing/corrupt
- API quota exceeded during preview

## Success Criteria

- [ ] Configuration can be viewed and edited via UI
- [ ] Changes persist across server restarts
- [ ] Preview mode shows expected results
- [ ] Channel whitelist is manageable
- [ ] Stats are visible and accurate
- [ ] No need to manually edit .env for common settings
- [ ] Configuration is validated before saving
- [ ] UI is responsive and user-friendly

## Future Enhancements (Phase 4+)

- **Scheduling**: Configure automatic refresh times
- **Profiles**: Save multiple configuration presets
- **Advanced Filters**: Regex title filters, view count thresholds
- **Notifications**: Email/webhook when new videos match
- **Multi-user**: User accounts with separate configs
- **API Keys**: Manage multiple YouTube API keys
- **Export/Import**: Share configurations as JSON

## Deployment Considerations

### For Hetzner Deployment
When deploying to Hetzner:
1. Configuration file location: `/var/www/playlist-app/config.json`
2. Environment file: `/var/www/playlist-app/.env` (secrets only)
3. File permissions: Ensure web server can read/write config.json
4. Backup strategy: Auto-backup config.json before changes
5. Systemd service: Reload service when config changes

### Security
- Validate all input server-side
- Don't expose API keys in config endpoints
- Rate limit config update endpoints
- Log configuration changes for audit trail
- Sanitize file paths to prevent directory traversal

## Estimated Implementation Time

| Task | Estimate |
|------|----------|
| Backend config endpoints | 2-3 hours |
| Configuration persistence | 1-2 hours |
| Frontend config form | 3-4 hours |
| Channel whitelist UI | 2-3 hours |
| Stats display | 1-2 hours |
| Integration testing | 2-3 hours |
| **Total** | **11-17 hours** |

## Next Steps

1. Decide on configuration storage approach (Option C recommended)
2. Create backend API endpoints
3. Build frontend configuration page
4. Implement channel management UI
5. Add stats display
6. Test end-to-end workflow
7. Deploy to Hetzner with proper file permissions
