// Pan-Pup Music Downloader JavaScript
class PanPup {
    constructor() {
        this.parsedTracks = [];
        this.currentUrl = '';
        this.isLoading = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkClipboardOnLoad();
    }

    initializeElements() {
        this.urlInput = document.getElementById('urlInput');
        this.parseBtn = document.getElementById('parseBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.trackList = document.getElementById('trackList');
        this.status = document.getElementById('status');
    }

    setupEventListeners() {
        // Auto-detect clipboard changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkClipboard();
            }
        });

        // URL input change detection
        this.urlInput.addEventListener('input', (e) => {
            const url = e.target.value.trim();
            if (this.isYouTubeUrl(url)) {
                this.currentUrl = url;
                // Auto-parse playlists
                if (this.isPlaylist(url)) {
                    setTimeout(() => this.parsePlaylist(), 500);
                }
            }
        });

        // Enter key to parse
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.parsePlaylist();
            }
        });
    }

    async checkClipboard() {
        if (!navigator.clipboard || !navigator.clipboard.readText) {
            return;
        }

        try {
            const text = await navigator.clipboard.readText();
            if (this.isYouTubeUrl(text) && text !== this.urlInput.value) {
                this.urlInput.value = text;
                this.currentUrl = text;
                
                // Auto-parse playlists
                if (this.isPlaylist(text)) {
                    this.parsePlaylist();
                }
            }
        } catch (err) {
            // Clipboard access might be denied, that's ok
            console.log('Clipboard access not available');
        }
    }

    async checkClipboardOnLoad() {
        // Try to auto-detect clipboard on page load
        setTimeout(() => this.checkClipboard(), 500);
    }

    isYouTubeUrl(url) {
        return url.includes('youtube.com') || url.includes('youtu.be');
    }

    isPlaylist(url) {
        return url.includes('playlist') || url.includes('list=');
    }

    async parsePlaylist() {
        const url = this.urlInput.value.trim();
        
        if (!url) {
            this.showStatus('Please paste a YouTube URL first!', 'error');
            return;
        }

        if (!this.isYouTubeUrl(url)) {
            this.showStatus('Please enter a valid YouTube URL!', 'error');
            return;
        }

        this.setLoading(true, 'Parsing tracks...');
        
        try {
            const response = await fetch('/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const result = await response.json();
            
            if (result.success) {
                this.parsedTracks = result.tracks;
                this.currentUrl = url;
                this.renderTrackList();
                this.showStatus(`Found ${result.tracks.length} track(s)!`, 'success');
            } else {
                this.showStatus(`Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showStatus('Network error. Make sure the server is running!', 'error');
            console.error('Parse error:', error);
        } finally {
            this.setLoading(false);
        }
    }

    renderTrackList() {
        if (this.parsedTracks.length === 0) {
            this.trackList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎵</div>
                    <p>No tracks found</p>
                </div>
            `;
            this.downloadBtn.disabled = true;
            return;
        }

        this.trackList.innerHTML = this.parsedTracks.map((track, index) => `
            <div class="track-item" onclick="panPup.toggleTrack('${track.id}')">
                <input type="checkbox" 
                       class="track-checkbox" 
                       ${track.selected ? 'checked' : ''} 
                       onchange="panPup.toggleTrack('${track.id}')"
                       onclick="event.stopPropagation()">
                <div class="track-info">
                    <div class="track-title" title="${this.escapeHtml(track.title)}">
                        ${this.escapeHtml(track.title)}
                    </div>
                    <div class="track-duration">${track.duration}</div>
                </div>
            </div>
        `).join('');

        this.downloadBtn.disabled = false;
        this.updateDownloadButton();
    }

    toggleTrack(trackId) {
        const track = this.parsedTracks.find(t => t.id === trackId);
        if (track) {
            track.selected = !track.selected;
            this.renderTrackList();
        }
    }

    selectAll() {
        this.parsedTracks.forEach(track => track.selected = true);
        this.renderTrackList();
    }

    selectNone() {
        this.parsedTracks.forEach(track => track.selected = false);
        this.renderTrackList();
    }

    updateDownloadButton() {
        const selectedCount = this.parsedTracks.filter(track => track.selected).length;
        this.downloadBtn.disabled = selectedCount === 0;
        
        if (selectedCount === 0) {
            this.downloadBtn.textContent = '🎵 Download Selected';
        } else {
            this.downloadBtn.textContent = `🎵 Download ${selectedCount} Track${selectedCount > 1 ? 's' : ''}`;
        }
    }

    async downloadSelected() {
        const selectedTracks = this.parsedTracks.filter(track => track.selected);
        
        if (selectedTracks.length === 0) {
            this.showStatus('Please select at least one track!', 'error');
            return;
        }

        this.setLoading(true, `Downloading ${selectedTracks.length} track(s)...`);
        
        try {
            const trackIds = selectedTracks.map(track => track.id);
            
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    url: this.currentUrl,
                    track_ids: trackIds 
                })
            });

            const result = await response.json();
            
            if (result.success) {
                const successful = result.downloads.filter(d => d.success).length;
                const failed = result.downloads.length - successful;
                
                let message = `✅ Downloaded ${successful} track(s)!`;
                if (failed > 0) {
                    message += ` (${failed} failed)`;
                }
                message += ' Check your music library.';
                
                this.showStatus(message, 'success');
            } else {
                this.showStatus(`Download error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showStatus('Network error during download!', 'error');
            console.error('Download error:', error);
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(loading, message = '') {
        this.isLoading = loading;
        this.parseBtn.disabled = loading;
        this.downloadBtn.disabled = loading || this.parsedTracks.filter(t => t.selected).length === 0;
        
        if (loading && message) {
            this.showStatus(message, 'loading');
        }
    }

    showStatus(message, type) {
        this.status.textContent = message;
        this.status.className = `status ${type}`;
        this.status.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                this.status.style.display = 'none';
            }, 4000);
        }
        
        // Auto-hide loading messages when not loading
        if (type === 'loading') {
            this.status.classList.add('loading');
        } else {
            this.status.classList.remove('loading');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for onclick handlers
function parsePlaylist() {
    panPup.parsePlaylist();
}

function downloadSelected() {
    panPup.downloadSelected();
}

function selectAll() {
    panPup.selectAll();
}

function selectNone() {
    panPup.selectNone();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.panPup = new PanPup();
    console.log('🐕 Pan-Pup initialized!');
});
