# Phase 2 Setup Guide

## ✅ Phase 2 Complete: Backend Integration

Your dashboard now has a Python Flask backend that integrates with your existing CLI tool!

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install all dependencies from project root
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
# Option 1: Using the convenience script
python run.py

# Option 2: Direct Flask run
python app.py
```

### 3. Open the Dashboard
```bash
# In a new terminal/tab
cd dashboard/
open index.html  # macOS
# or double-click index.html in file manager
```

**The frontend automatically detects the backend and switches to API mode!**

## 🎯 New Features

### Smart Mode Detection
- **Backend Available**: Shows "🔄 Load from API" and "🔄 Refresh Playlist" buttons
- **Static Mode**: Falls back to file-based operation if no backend

### Live Data Integration
- Loads playlist data from your CLI tool's CSV reports
- Falls back to cached JSON data or sample data
- Shows real-time stats from your actual playlists

### Refresh Capability
- Click "🔄 Refresh Playlist" to run your CLI tool via the API
- Generates fresh playlist data using your existing configuration
- Shows loading indicators and success/error messages

### API Endpoints
- `GET /api/playlist` - Get current playlist data
- `POST /api/refresh` - Generate fresh playlist (runs CLI tool)
- `GET /api/status` - System health and data source info

## 🔧 How It Works

### Data Source Priority
1. **Recent CSV reports** from `yt_sub_playlist/reports/` (< 24 hours old)
2. **Cached JSON data** from `yt_sub_playlist/data/`
3. **Sample data** from `dashboard/playlist.json`

### CLI Integration
- Backend imports your `yt_sub_playlist` modules directly
- Runs `python -m yt_sub_playlist --report` for refresh operations
- Handles errors gracefully if CLI tool isn't available

### Smart UI Updates
- Buttons change text and behavior based on backend availability
- Loading overlays for long-running operations
- Success/error messages with auto-hide

## 🧪 Testing the Integration

### Test Backend Connection
1. Start backend: `cd dashboard/backend && python run.py`
2. Visit: http://localhost:5001/api/status
3. Should see JSON with `cli_available: true/false`

### Test Data Loading
1. Open dashboard in browser
2. Should see "🔄 Load from API" button (backend mode)
3. Click it - should load your actual playlist data

### Test Refresh Functionality
1. Click "🔄 Refresh Playlist" 
2. Watch loading spinner and backend logs
3. Should generate fresh data using your CLI tool

## 🐛 Troubleshooting

### "CLI tool not available"
```bash
# Make sure you're in the right directory
cd /path/to/playlist-from-subs/dashboard/backend
python run.py
```

### Frontend shows static mode despite backend running
- Check browser console for CORS errors
- Verify backend is accessible: http://localhost:5001/api/status
- Make sure backend started without errors

### Refresh takes forever
- CLI operations can take 1-5 minutes
- Check backend terminal for progress logs
- YouTube API quotas or network issues can cause delays

### No recent data found
- Run CLI tool once to generate reports: `python -m yt_sub_playlist --report reports/test.csv`
- Check that reports directory exists and has recent files

## 📁 New File Structure

```
dashboard/
├── index.html              # Frontend (updated for API mode)
├── script.js               # JavaScript (backend detection + API calls)
├── styles.css              # Styles (loading + success messages)
├── playlist.json           # Sample data (fallback)
├── backend/
│   ├── app.py              # Flask API server
│   ├── run.py              # Convenience startup script
│   ├── requirements.txt    # Python dependencies
│   └── README.md          # Backend documentation
├── PHASE2_SETUP.md        # This file
└── README.md              # Phase 1 documentation
```

## 🎯 Ready for Phase 3?

Your dashboard now has:
- ✅ Static file support (Phase 1)
- ✅ Backend API integration (Phase 2)

Next up: **Configuration Controls** - Let users tweak filtering parameters and see real-time preview effects!

The backend is perfectly positioned to accept configuration changes and regenerate playlists dynamically.