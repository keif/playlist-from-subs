# YouTube Playlist Dashboard - Phase 1

A static web preview for your YouTube playlist automation project.

## Features

✅ **Load playlist data** - Drag & drop JSON files or click to browse  
✅ **Video grid display** - Thumbnails, titles, channels, duration, publish dates  
✅ **YouTube links** - Click any video to watch on YouTube  
✅ **Playlist stats** - Video count, total duration, unique channels  
✅ **Responsive design** - Works on desktop, tablet, and mobile  
✅ **Offline capable** - No external dependencies, works without internet

## Quick Start

1. **Open the dashboard**:
   ```bash
   cd dashboard/
   open index.html  # macOS
   # or double-click index.html in file explorer
   ```

2. **Load your playlist**:
   - Click "Load Sample Data" to see example videos
   - Or drag/drop your own `playlist.json` file
   - Or click "Load Playlist JSON" to browse for a file

## File Structure

```
dashboard/
├── index.html      # Main dashboard page
├── styles.css      # CSS styling
├── script.js       # JavaScript functionality
├── playlist.json   # Sample playlist data
└── README.md       # This file
```

## JSON Format

The dashboard expects an array of video objects:

```json
[
  {
    "title": "Video Title",
    "video_id": "YouTube_Video_ID",
    "channel_title": "Channel Name",
    "channel_id": "YouTube_Channel_ID", 
    "published_at": "2024-01-15T10:30:00Z",
    "duration_seconds": 1245,
    "live_broadcast": "none",
    "added": true
  }
]
```

## Features Breakdown

### 🎯 Core Functionality
- **File Loading**: Drag & drop or file picker for JSON files
- **Video Display**: Grid layout with thumbnails and metadata
- **Stats Dashboard**: Quick overview of playlist metrics
- **YouTube Integration**: Direct links to watch videos

### 🎨 User Experience  
- **Modern Design**: Gradient background, clean cards, smooth animations
- **Mobile Responsive**: Adapts to different screen sizes
- **Error Handling**: Clear messages for invalid files or loading issues
- **Accessibility**: Proper contrast, semantic HTML, keyboard navigation

### 🔧 Technical Details
- **No Build Process**: Pure HTML/CSS/JS - just open in browser
- **No External Dependencies**: Works completely offline
- **Cross-browser Compatible**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Performance Optimized**: Lazy loading images, efficient DOM manipulation

## Next Steps (Phase 2)

Ready to add backend integration? The next phase will:
- Add Python Flask/FastAPI server
- Serve playlist data via REST API
- Enable dynamic playlist generation
- Add refresh capabilities

## Troubleshooting

**Can't load sample data?**
- Make sure `playlist.json` is in the same directory as `index.html`
- Check browser console for errors

**Videos not displaying correctly?**
- Verify your JSON matches the expected format
- Check that video IDs are valid YouTube IDs

**Styling looks broken?**
- Ensure `styles.css` is in the same directory
- Check browser console for 404 errors