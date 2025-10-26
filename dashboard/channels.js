/**
 * Channel Management Interface
 *
 * Provides UI for managing channel allowlist/blocklist filtering.
 */

// State management
let allChannels = [];
let filteredChannels = [];
let selectedChannelIds = new Set();
let currentMode = 'none';
let searchQuery = '';

// DOM elements
const elements = {
    modeCards: null,
    searchSection: null,
    searchInput: null,
    channelsSection: null,
    channelList: null,
    channelListTitle: null,
    filterInfo: null,
    selectAllBtn: null,
    deselectAllBtn: null,
    saveBtn: null,
    cancelBtn: null,
    statusMessage: null
};

// API endpoints
const API_BASE = 'http://localhost:5001/api';

/**
 * Initialize the application
 */
async function init() {
    // Cache DOM elements
    elements.searchSection = document.getElementById('searchSection');
    elements.searchInput = document.getElementById('searchInput');
    elements.channelsSection = document.getElementById('channelsSection');
    elements.channelList = document.getElementById('channelList');
    elements.channelListTitle = document.getElementById('channelListTitle');
    elements.filterInfo = document.getElementById('filterInfo');
    elements.selectAllBtn = document.getElementById('selectAllBtn');
    elements.deselectAllBtn = document.getElementById('deselectAllBtn');
    elements.saveBtn = document.getElementById('saveBtn');
    elements.cancelBtn = document.getElementById('cancelBtn');
    elements.statusMessage = document.getElementById('statusMessage');

    // Set up event listeners
    setupEventListeners();

    // Load current configuration
    await loadFilterConfig();

    // Load channels
    await loadChannels();

    // Update UI based on mode
    updateUIForMode();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Mode selection
    document.querySelectorAll('input[name="filterMode"]').forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });

    // Search
    elements.searchInput.addEventListener('input', handleSearchInput);

    // Bulk actions
    elements.selectAllBtn.addEventListener('click', selectAllChannels);
    elements.deselectAllBtn.addEventListener('click', deselectAllChannels);

    // Save/Cancel
    elements.saveBtn.addEventListener('click', saveConfiguration);
    elements.cancelBtn.addEventListener('click', () => {
        window.location.href = 'config.html';
    });
}

/**
 * Load current filter configuration from API
 */
async function loadFilterConfig() {
    try {
        const response = await fetch(`${API_BASE}/channels/filter-config`);
        const data = await response.json();

        if (data.success) {
            currentMode = data.filter_mode;

            // Update selected channels based on current mode
            if (currentMode === 'allowlist' && data.allowlist.channel_ids) {
                selectedChannelIds = new Set(data.allowlist.channel_ids);
            } else if (currentMode === 'blocklist' && data.blocklist.channel_ids) {
                selectedChannelIds = new Set(data.blocklist.channel_ids);
            }

            // Set the active radio button
            const radio = document.querySelector(`input[name="filterMode"][value="${currentMode}"]`);
            if (radio) {
                radio.checked = true;
                updateModeCardStyles();
            }
        } else {
            showError('Failed to load filter configuration');
        }
    } catch (error) {
        console.error('Error loading filter config:', error);
        showError('Failed to load filter configuration');
    }
}

/**
 * Load all subscribed channels from API
 */
async function loadChannels() {
    try {
        const response = await fetch(`${API_BASE}/channels`);

        // Handle non-JSON responses (like plain error text)
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();

        if (data.success && data.channels) {
            // Normalize channel data (handle both 'title' and 'channel_title')
            allChannels = data.channels.map(ch => ({
                channel_id: ch.channel_id,
                title: ch.title || ch.channel_title || 'Unknown Channel',
                description: ch.description || '',
                thumbnail: ch.thumbnail || ''
            }));
            filteredChannels = [...allChannels];
            renderChannels();
        } else {
            const errorMsg = data.error || 'No channels found. Please check your YouTube subscription data.';
            showEmptyState(errorMsg);
        }
    } catch (error) {
        console.error('Error loading channels:', error);
        showEmptyState('Failed to load channels. YouTube API credentials may not be configured. Please set up OAuth credentials to use channel management.');
    }
}

/**
 * Handle mode change
 */
function handleModeChange(event) {
    const newMode = event.target.value;

    // If there are selected channels and we're switching modes, confirm with user
    if (selectedChannelIds.size > 0 && newMode !== currentMode) {
        const proceed = confirm(
            `You have ${selectedChannelIds.size} selected channel(s). ` +
            `Switching modes will clear your current selection. Continue?`
        );

        if (!proceed) {
            // Revert to previous mode
            const previousRadio = document.querySelector(`input[name="filterMode"][value="${currentMode}"]`);
            if (previousRadio) {
                previousRadio.checked = true;
            }
            return;
        }

        // Clear selection when switching modes
        selectedChannelIds.clear();
    }

    currentMode = newMode;
    updateModeCardStyles();
    updateUIForMode();
    renderChannels();
}

/**
 * Update mode card visual styles
 */
function updateModeCardStyles() {
    document.querySelectorAll('.mode-card').forEach(card => {
        card.classList.remove('active');
    });

    const activeCard = document.getElementById(`mode${currentMode.charAt(0).toUpperCase() + currentMode.slice(1)}`);
    if (activeCard) {
        activeCard.classList.add('active');
    }
}

/**
 * Update UI based on current mode
 */
function updateUIForMode() {
    if (currentMode === 'none') {
        // Hide channel selection for "none" mode
        elements.searchSection.style.display = 'none';
        elements.channelsSection.style.display = 'none';
    } else {
        // Show channel selection for allowlist/blocklist
        elements.searchSection.style.display = 'block';
        elements.channelsSection.style.display = 'block';

        // Update title and info based on mode
        if (currentMode === 'allowlist') {
            elements.channelListTitle.textContent = 'Select Channels to Include';
            elements.filterInfo.innerHTML = '<strong>Allowlist Mode:</strong> Only videos from selected channels will be included in the playlist.';
        } else if (currentMode === 'blocklist') {
            elements.channelListTitle.textContent = 'Select Channels to Exclude';
            elements.filterInfo.innerHTML = '<strong>Blocklist Mode:</strong> Videos from selected channels will be excluded from the playlist.';
        }
    }
}

/**
 * Handle search input with debouncing
 */
let searchTimeout;
function handleSearchInput(event) {
    clearTimeout(searchTimeout);
    searchQuery = event.target.value.toLowerCase().trim();

    searchTimeout = setTimeout(() => {
        filterChannels();
        renderChannels();
    }, 300);
}

/**
 * Filter channels based on search query
 */
function filterChannels() {
    if (!searchQuery) {
        filteredChannels = [...allChannels];
    } else {
        filteredChannels = allChannels.filter(channel => {
            const nameMatch = channel.title.toLowerCase().includes(searchQuery);
            const idMatch = channel.channel_id.toLowerCase().includes(searchQuery);
            return nameMatch || idMatch;
        });
    }
}

/**
 * Render channels in the list
 */
function renderChannels() {
    if (currentMode === 'none') {
        return;
    }

    if (filteredChannels.length === 0) {
        if (searchQuery) {
            showEmptyState('No channels match your search.');
        } else {
            showEmptyState('No channels available.');
        }
        return;
    }

    let html = '';
    filteredChannels.forEach(channel => {
        const isSelected = selectedChannelIds.has(channel.channel_id);
        const selectedClass = isSelected ? 'selected' : '';

        html += `
            <div class="channel-item ${selectedClass}" onclick="toggleChannel('${channel.channel_id}')">
                <input type="checkbox"
                       class="channel-checkbox"
                       ${isSelected ? 'checked' : ''}
                       onchange="toggleChannel('${channel.channel_id}')">
                <div class="channel-info">
                    <div class="channel-name">${escapeHtml(channel.title)}</div>
                    <div class="channel-id">${escapeHtml(channel.channel_id)}</div>
                </div>
            </div>
        `;
    });

    elements.channelList.innerHTML = html;
}

/**
 * Toggle channel selection
 */
function toggleChannel(channelId) {
    if (selectedChannelIds.has(channelId)) {
        selectedChannelIds.delete(channelId);
    } else {
        selectedChannelIds.add(channelId);
    }
    renderChannels();
}

/**
 * Select all visible channels
 */
function selectAllChannels() {
    filteredChannels.forEach(channel => {
        selectedChannelIds.add(channel.channel_id);
    });
    renderChannels();
}

/**
 * Deselect all channels
 */
function deselectAllChannels() {
    selectedChannelIds.clear();
    renderChannels();
}

/**
 * Save configuration to API
 */
async function saveConfiguration() {
    // Prepare data based on mode
    const allowlist = currentMode === 'allowlist' ? Array.from(selectedChannelIds) : [];
    const blocklist = currentMode === 'blocklist' ? Array.from(selectedChannelIds) : [];

    const payload = {
        mode: currentMode,
        allowlist: allowlist,
        blocklist: blocklist
    };

    try {
        elements.saveBtn.disabled = true;
        elements.saveBtn.textContent = 'Saving...';

        const response = await fetch(`${API_BASE}/channels/filter-config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
            showSuccess('Configuration saved successfully!');
            setTimeout(() => {
                window.location.href = 'config.html';
            }, 1500);
        } else {
            showError(data.error || 'Failed to save configuration');
            elements.saveBtn.disabled = false;
            elements.saveBtn.innerHTML = '<i data-lucide="save"></i> Save Changes';
            lucide.createIcons();
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        showError('Failed to save configuration. Please try again.');
        elements.saveBtn.disabled = false;
        elements.saveBtn.innerHTML = '<i data-lucide="save"></i> Save Changes';
        lucide.createIcons();
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = 'status-message success';
    setTimeout(() => {
        elements.statusMessage.className = 'status-message';
    }, 5000);
}

/**
 * Show error message
 */
function showError(message) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = 'status-message error';
    setTimeout(() => {
        elements.statusMessage.className = 'status-message';
    }, 5000);
}

/**
 * Show empty state in channel list
 */
function showEmptyState(message) {
    elements.channelList.innerHTML = `
        <div class="empty-state">
            <p>${message}</p>
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
