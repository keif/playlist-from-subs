class PlaylistDashboard {
    constructor() {
        this.currentPlaylist = [];
        this.apiBaseUrl = 'http://localhost:5001/api';
        this.isBackendMode = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.checkBackendAvailability();
        console.log('🎵 Playlist Dashboard initialized');
    }

    setupEventListeners() {
        // File input handler
        document.getElementById('file-input').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.loadPlaylistFromFile(file);
            }
        });

        // Load sample data button
        document.getElementById('load-sample').addEventListener('click', () => {
            if (this.isBackendMode) {
                this.loadFromAPI();
            } else {
                this.loadSampleData();
            }
        });

        // Clear playlist button
        document.getElementById('clear-playlist').addEventListener('click', () => {
            this.clearPlaylist();
        });
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('drop-zone');
        const body = document.body;

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            body.addEventListener(eventName, this.preventDefaults, false);
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            body.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            body.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            }, false);
        });

        // Handle dropped files
        body.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type === 'application/json' || file.name.endsWith('.json')) {
                    this.loadPlaylistFromFile(file);
                } else {
                    this.showError('Please drop a JSON file');
                }
            }
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async checkBackendAvailability() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/status`);
            if (response.ok) {
                this.isBackendMode = true;
                this.updateUIForBackendMode();
                console.log('✅ Backend detected - API mode enabled');
                // Auto-load playlist data from API
                this.loadFromAPI();
            } else {
                throw new Error('Backend not responding');
            }
        } catch (error) {
            console.log('ℹ️ No backend detected - static mode only');
            this.isBackendMode = false;
            this.updateUIForStaticMode();
        }
    }

    updateUIForBackendMode() {
        const loadButton = document.getElementById('load-sample');
        loadButton.innerHTML = '<i data-lucide="rotate-cw" style="width: 16px; height: 16px;"></i> Load from API';
        loadButton.title = 'Load playlist data from the backend server';
        lucide.createIcons();
        
        // Add refresh button
        this.addRefreshButton();
        
        // Update file info text
        const fileInfo = document.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.textContent = 'or drag & drop a JSON file anywhere (backend mode active)';
        }
    }

    updateUIForStaticMode() {
        const loadButton = document.getElementById('load-sample');
        loadButton.textContent = 'Load Sample Data';
        loadButton.title = 'Load static sample data';
        
        // Update file info text
        const fileInfo = document.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.textContent = 'or drag & drop a JSON file anywhere (static mode)';
        }
    }

    addRefreshButton() {
        const controls = document.querySelector('.controls');
        
        // Don't add if already exists
        if (document.getElementById('refresh-playlist')) return;
        
        const refreshButton = document.createElement('button');
        refreshButton.id = 'refresh-playlist';
        refreshButton.className = 'button-secondary';
        refreshButton.innerHTML = '<i data-lucide="refresh-cw" style="width: 16px; height: 16px;"></i> Refresh Playlist';
        refreshButton.title = 'Generate fresh playlist data using the CLI tool';
        lucide.createIcons();
        
        refreshButton.addEventListener('click', () => {
            this.refreshPlaylist();
        });
        
        controls.appendChild(refreshButton);
    }

    async loadFromAPI() {
        try {
            this.showLoading('Loading playlist from API...');
            
            const response = await fetch(`${this.apiBaseUrl}/playlist`);
            if (!response.ok) {
                throw new Error(`API error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            this.hideLoading();
            
            if (result.success) {
                this.displayPlaylist(result.data);
                console.log(`✅ Loaded ${result.count} videos from API`);
            } else {
                throw new Error(result.error || 'Unknown API error');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error loading from API:', error);
            this.showError(`Could not load playlist from API: ${error.message}`);
        }
    }

    async refreshPlaylist(dryRun = false) {
        try {
            const refreshButton = document.getElementById('refresh-playlist');
            const originalText = refreshButton.textContent;
            
            refreshButton.disabled = true;
            refreshButton.textContent = '⏳ Refreshing...';
            
            this.showLoading('Generating fresh playlist data...');
            
            const response = await fetch(`${this.apiBaseUrl}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dry_run: dryRun })
            });
            
            const result = await response.json();
            
            this.hideLoading();
            
            if (result.success) {
                this.showSuccess(`Playlist refreshed successfully! ${dryRun ? '(Dry run)' : ''}`);
                // Reload the playlist data
                setTimeout(() => this.loadFromAPI(), 1000);
            } else {
                throw new Error(result.error || 'Refresh failed');
            }
            
        } catch (error) {
            this.hideLoading();
            console.error('Error refreshing playlist:', error);
            this.showError(`Could not refresh playlist: ${error.message}`);
        } finally {
            const refreshButton = document.getElementById('refresh-playlist');
            if (refreshButton) {
                refreshButton.disabled = false;
                refreshButton.innerHTML = '<i data-lucide="refresh-cw" style="width: 16px; height: 16px;"></i> Refresh Playlist';
                lucide.createIcons();
            }
        }
    }

    async loadSampleData() {
        try {
            const response = await fetch('./playlist.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.displayPlaylist(data);
        } catch (error) {
            console.error('Error loading sample data:', error);
            this.showError('Could not load sample data. Make sure playlist.json exists in the same directory.');
        }
    }

    loadPlaylistFromFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.displayPlaylist(data);
                this.hideError();
            } catch (error) {
                console.error('Error parsing JSON:', error);
                this.showError('Invalid JSON file. Please check the file format.');
            }
        };
        reader.onerror = () => {
            this.showError('Error reading file');
        };
        reader.readAsText(file);
    }

    displayPlaylist(videos) {
        if (!Array.isArray(videos)) {
            this.showError('Invalid playlist format. Expected an array of videos.');
            return;
        }

        this.currentPlaylist = videos;
        this.updateStats();
        this.renderVideoGrid();
        
        // Show playlist container and hide drop zone
        document.getElementById('playlist-container').style.display = 'block';
        document.getElementById('drop-zone').style.display = 'none';
        document.getElementById('playlist-stats').style.display = 'flex';
    }

    updateStats() {
        const videoCount = this.currentPlaylist.length;
        const totalSeconds = this.currentPlaylist.reduce((sum, video) => sum + (video.duration_seconds || 0), 0);
        const uniqueChannels = new Set(this.currentPlaylist.map(video => video.channel_id)).size;

        document.getElementById('video-count').textContent = videoCount;
        document.getElementById('total-duration').textContent = this.formatDuration(totalSeconds);
        document.getElementById('channel-count').textContent = uniqueChannels;
    }

    renderVideoGrid() {
        const container = document.getElementById('video-grid');
        container.innerHTML = '';

        this.currentPlaylist.forEach((video, index) => {
            const videoCard = this.createVideoCard(video, index);
            container.appendChild(videoCard);
        });
    }

    createVideoCard(video, index) {
        const card = document.createElement('div');
        card.className = 'video-card';
        
        const thumbnailUrl = this.getYouTubeThumbnail(video.video_id);
        const publishDate = this.formatDate(video.published_at);
        const duration = this.formatDuration(video.duration_seconds);
        const youtubeUrl = `https://www.youtube.com/watch?v=${video.video_id}`;

        card.innerHTML = `
            <div class="video-thumbnail">
                <img src="${thumbnailUrl}" alt="${video.title}" loading="lazy">
                <div class="video-duration">${duration}</div>
            </div>
            <div class="video-info">
                <h3 class="video-title">
                    <a href="${youtubeUrl}" target="_blank" rel="noopener noreferrer">
                        ${this.escapeHtml(video.title)}
                    </a>
                </h3>
                <div class="video-meta">
                    <div class="channel-name">${this.escapeHtml(video.channel_title)}</div>
                    <div class="publish-date">${publishDate}</div>
                </div>
                <div class="video-actions">
                    <a href="${youtubeUrl}" target="_blank" class="watch-button">
                        ▶️ Watch
                    </a>
                    <span class="video-status ${video.added ? 'added' : 'not-added'}">
                        ${video.added ? '✅ Added' : '❌ Not Added'}
                    </span>
                </div>
            </div>
        `;

        return card;
    }

    getYouTubeThumbnail(videoId) {
        // Use medium quality thumbnail (320x180)
        return `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
    }

    formatDuration(seconds) {
        if (!seconds || seconds === 0) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    clearPlaylist() {
        this.currentPlaylist = [];
        document.getElementById('playlist-container').style.display = 'none';
        document.getElementById('playlist-stats').style.display = 'none';
        document.getElementById('drop-zone').style.display = 'flex';
        document.getElementById('file-input').value = '';
        this.hideError();
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        errorText.textContent = message;
        errorElement.style.display = 'flex';
        
        // Auto-hide error after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    hideError() {
        document.getElementById('error-message').style.display = 'none';
    }

    showLoading(message = 'Loading...') {
        // Show loading in the drop zone or create a loading overlay
        const dropZone = document.getElementById('drop-zone');
        const playlistContainer = document.getElementById('playlist-container');
        
        if (playlistContainer.style.display !== 'none') {
            // Show loading overlay on playlist
            this.showLoadingOverlay(message);
        } else {
            // Show loading in drop zone
            dropZone.innerHTML = `
                <div class="drop-zone-content">
                    <div class="loading-spinner">⏳</div>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    hideLoading() {
        this.hideLoadingOverlay();
        // Reset drop zone if needed - will be handled by other methods
    }

    showLoadingOverlay(message) {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner">⏳</div>
                <p>${message}</p>
            </div>
        `;
        overlay.style.display = 'flex';
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showSuccess(message) {
        // Create or update success message element
        let successElement = document.getElementById('success-message');
        if (!successElement) {
            successElement = document.createElement('div');
            successElement.id = 'success-message';
            successElement.className = 'success-message';
            successElement.innerHTML = `
                <span class="success-icon">✅</span>
                <span id="success-text"></span>
            `;
            
            // Insert after error message
            const errorMessage = document.getElementById('error-message');
            errorMessage.parentNode.insertBefore(successElement, errorMessage.nextSibling);
        }
        
        document.getElementById('success-text').textContent = message;
        successElement.style.display = 'flex';
        
        // Auto-hide success after 3 seconds
        setTimeout(() => {
            successElement.style.display = 'none';
        }, 3000);
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new PlaylistDashboard();
});