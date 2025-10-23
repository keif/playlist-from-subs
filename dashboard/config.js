// Configuration Page JavaScript

const API_BASE = 'http://localhost:5001';

// DOM Elements
const elements = {
    playlistName: document.getElementById('playlistName'),
    playlistVisibility: document.getElementById('playlistVisibility'),
    minDuration: document.getElementById('minDuration'),
    minDurationValue: document.getElementById('minDurationValue'),
    lookbackHours: document.getElementById('lookbackHours'),
    lookbackHoursValue: document.getElementById('lookbackHoursValue'),
    maxVideos: document.getElementById('maxVideos'),
    maxVideosValue: document.getElementById('maxVideosValue'),
    skipLiveContent: document.getElementById('skipLiveContent'),
    saveBtn: document.getElementById('saveBtn'),
    previewBtn: document.getElementById('previewBtn'),
    resetBtn: document.getElementById('resetBtn'),
    message: document.getElementById('message'),
    quotaUsed: document.getElementById('quotaUsed'),
    quotaRemaining: document.getElementById('quotaRemaining'),
    quotaBar: document.getElementById('quotaBar'),
    cacheCount: document.getElementById('cacheCount'),
    cacheAge: document.getElementById('cacheAge')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfiguration();
    loadStats();
    setupEventListeners();
});

// Load current configuration
async function loadConfiguration() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const data = await response.json();

        if (data.success) {
            const config = data.config;

            elements.playlistName.value = config.playlist_name || '';
            elements.playlistVisibility.value = config.playlist_visibility || 'unlisted';
            elements.minDuration.value = config.min_duration_seconds || 60;
            elements.lookbackHours.value = config.lookback_hours || 24;
            elements.maxVideos.value = config.max_videos || 50;
            elements.skipLiveContent.checked = config.skip_live_content !== false;

            updateRangeDisplays();
        } else {
            showMessage('Failed to load configuration', 'error');
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showMessage('Error loading configuration. Is the backend running?', 'error');
    }
}

// Load system statistics
async function loadStats() {
    try {
        // Load quota stats
        const quotaResponse = await fetch(`${API_BASE}/api/stats/quota`);
        const quotaData = await quotaResponse.json();

        if (quotaData.success && quotaData.quota) {
            const quota = quotaData.quota;
            elements.quotaUsed.textContent = quota.daily_used.toLocaleString();
            elements.quotaRemaining.textContent = quota.remaining.toLocaleString();

            const percentage = quota.percentage_used;
            elements.quotaBar.style.width = `${percentage}%`;
            elements.quotaBar.textContent = `${percentage.toFixed(1)}%`;

            // Color code the quota bar
            if (percentage > 90) {
                elements.quotaBar.className = 'quota-fill danger';
            } else if (percentage > 70) {
                elements.quotaBar.className = 'quota-fill warning';
            } else {
                elements.quotaBar.className = 'quota-fill';
            }
        }

        // Load cache stats
        const cacheResponse = await fetch(`${API_BASE}/api/stats/cache`);
        const cacheData = await cacheResponse.json();

        if (cacheData.success && cacheData.cache) {
            const cache = cacheData.cache;
            elements.cacheCount.textContent = cache.total_videos.toLocaleString();
            elements.cacheAge.textContent = `${cache.oldest_entry_age_days} days`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        // Don't show error message for stats - it's not critical
    }
}

// Setup event listeners
function setupEventListeners() {
    // Range sliders
    elements.minDuration.addEventListener('input', updateRangeDisplays);
    elements.lookbackHours.addEventListener('input', updateRangeDisplays);
    elements.maxVideos.addEventListener('input', updateRangeDisplays);

    // Buttons
    elements.saveBtn.addEventListener('click', saveConfiguration);
    elements.previewBtn.addEventListener('click', previewChanges);
    elements.resetBtn.addEventListener('click', resetToDefaults);
}

// Update range slider displays
function updateRangeDisplays() {
    // Min duration
    const minDuration = parseInt(elements.minDuration.value);
    const minDurationText = minDuration >= 60
        ? `${Math.floor(minDuration / 60)} min ${minDuration % 60} sec`
        : `${minDuration} seconds`;
    elements.minDurationValue.textContent = minDurationText;

    // Lookback hours
    const lookbackHours = parseInt(elements.lookbackHours.value);
    const lookbackText = lookbackHours >= 24
        ? `${Math.floor(lookbackHours / 24)} days`
        : `${lookbackHours} hours`;
    elements.lookbackHoursValue.textContent = lookbackText;

    // Max videos
    const maxVideos = parseInt(elements.maxVideos.value);
    elements.maxVideosValue.textContent = `${maxVideos} videos`;
}

// Get current form values as config object
function getConfigFromForm() {
    return {
        playlist_name: elements.playlistName.value,
        playlist_visibility: elements.playlistVisibility.value,
        min_duration_seconds: parseInt(elements.minDuration.value),
        lookback_hours: parseInt(elements.lookbackHours.value),
        max_videos: parseInt(elements.maxVideos.value),
        skip_live_content: elements.skipLiveContent.checked
    };
}

// Save configuration
async function saveConfiguration() {
    try {
        setLoading(true);
        const config = getConfigFromForm();

        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            showMessage('✅ Configuration saved successfully!', 'success');
            setTimeout(() => hideMessage(), 3000);
        } else {
            const errors = data.errors ? data.errors.join(', ') : 'Unknown error';
            showMessage(`❌ Failed to save: ${errors}`, 'error');
        }
    } catch (error) {
        console.error('Error saving config:', error);
        showMessage('❌ Error saving configuration', 'error');
    } finally {
        setLoading(false);
    }
}

// Preview changes (dry run)
async function previewChanges() {
    try {
        setLoading(true);
        const config = getConfigFromForm();

        showMessage('🔍 Running preview with new settings... This may take a few minutes.', 'success');

        // First validate the config
        const validateResponse = await fetch(`${API_BASE}/api/config/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const validateData = await validateResponse.json();

        if (!validateData.valid) {
            const errors = validateData.errors.join(', ');
            showMessage(`❌ Invalid configuration: ${errors}`, 'error');
            return;
        }

        // TODO: Implement preview refresh endpoint
        // For now, just show a message
        showMessage('Preview mode is coming soon! For now, save your changes and run a manual refresh.', 'success');

    } catch (error) {
        console.error('Error previewing:', error);
        showMessage('❌ Error running preview', 'error');
    } finally {
        setLoading(false);
    }
}

// Reset to defaults
async function resetToDefaults() {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
        return;
    }

    try {
        setLoading(true);

        const response = await fetch(`${API_BASE}/api/config/reset`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showMessage('✅ Configuration reset to defaults', 'success');
            // Reload the configuration
            await loadConfiguration();
            setTimeout(() => hideMessage(), 3000);
        } else {
            showMessage('❌ Failed to reset configuration', 'error');
        }
    } catch (error) {
        console.error('Error resetting config:', error);
        showMessage('❌ Error resetting configuration', 'error');
    } finally {
        setLoading(false);
    }
}

// Show message
function showMessage(text, type) {
    elements.message.textContent = text;
    elements.message.className = `message ${type} show`;
}

// Hide message
function hideMessage() {
    elements.message.className = 'message';
}

// Set loading state
function setLoading(isLoading) {
    const container = document.querySelector('.config-container');
    if (isLoading) {
        container.classList.add('loading');
    } else {
        container.classList.remove('loading');
    }
}

// Format duration for display
function formatDuration(seconds) {
    if (seconds >= 3600) {
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    } else if (seconds >= 60) {
        return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}
