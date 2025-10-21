# YouTube Playlist Dashboard - Phase 2 Backend

A Flask REST API that serves your YouTube playlist data and integrates with your existing CLI tool.

## Features

✅ **REST API** - Serves playlist data via HTTP endpoints  
✅ **CLI Integration** - Automatically detects and uses your existing yt_sub_playlist tool  
✅ **Live Refresh** - Trigger fresh playlist generation via API  
✅ **Multiple Data Sources** - Loads from CSV reports, JSON files, or sample data  
✅ **Graceful Fallback** - Works even if CLI tool isn't available  
✅ **CORS Enabled** - Frontend can connect from any origin during development

## Quick Start

### 1. Install Dependencies

```bash
# Install from project root (includes both CLI and dashboard dependencies)
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python app.py
```

The server will start at `http://localhost:5001`

### 3. Open the Dashboard

```bash
# In a new terminal, go back to dashboard directory
cd ../
open index.html  # or double-click index.html
```

The frontend will automatically detect the backend and switch to API mode!

## API Endpoints

### `GET /api/playlist`
Get current playlist data

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 25,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### `POST /api/refresh`
Refresh playlist by running the CLI tool

**Request Body:**
```json
{
  "dry_run": false  // optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Playlist refreshed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "dry_run": false
}
```

### `GET /api/status`
Get system status and health check

**Response:**
```json
{
  "cli_available": true,
  "last_refresh": "2024-01-15T10:30:00Z",
  "data_sources": {
    "reports_dir_exists": true,
    "recent_csv_count": 3
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Data Source Priority

The backend loads playlist data in this order:

1. **CSV Reports** (`yt_sub_playlist/reports/*.csv`)
   - Most complete data from CLI runs
   - Must be less than 24 hours old

2. **JSON Cache** (`yt_sub_playlist/data/processed_videos.json`)
   - Cached data from CLI tool

3. **Sample Data** (`dashboard/playlist.json`)
   - Fallback for testing/demo

## CLI Integration

The backend automatically integrates with your existing CLI tool:

- **Auto-detection**: Imports `yt_sub_playlist` modules if available
- **Live refresh**: Runs `python -m yt_sub_playlist --report` when refreshing
- **Error handling**: Graceful fallback if CLI isn't working
- **Timeout protection**: 5-minute timeout for CLI operations

## Development Features

### Hot Reload
Flask development server automatically reloads when you change Python files.

### CORS Support
Frontend can connect from any origin during development (disabled in production).

### Logging
Detailed logging shows:
- Data source selection
- CLI command execution
- API request/response details

### Error Handling
Robust error handling for:
- Missing CLI tool
- Invalid data files
- Network errors
- Timeout issues

## Production Considerations

For production deployment, consider:

1. **Security**: Disable CORS, add authentication
2. **Performance**: Use production WSGI server (gunicorn, uwsgi)
3. **Monitoring**: Add health checks and metrics
4. **Caching**: Add Redis/Memcached for playlist data
5. **Rate Limiting**: Prevent abuse of refresh endpoint

### Example Production Setup

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### "CLI tool not available"
- Make sure you're running from the correct directory
- Check that `yt_sub_playlist` is installed and importable
- Verify your Python path includes the project root

### "No recent CSV reports found"
- Run the CLI tool at least once: `python -m yt_sub_playlist --report reports/test.csv`
- Check that `yt_sub_playlist/reports/` directory exists

### Frontend can't connect to API
- Verify backend is running on `http://localhost:5001`
- Check browser console for CORS errors
- Try accessing `http://localhost:5001/api/status` directly

### Refresh takes too long
- CLI operations can take 1-5 minutes depending on subscriptions
- Check backend logs for CLI output
- Consider running with `dry_run: true` for testing

## File Structure

```
backend/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Next Steps (Phase 3)

Ready for configuration controls? The next phase will add:
- Frontend forms for filter settings
- Dynamic playlist generation with custom parameters
- Real-time preview of filter effects