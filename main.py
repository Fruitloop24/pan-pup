#!/usr/bin/env python3
"""
Pan-Pup Music Downloader
Main server that handles both frontend serving and backend API
"""

import os
import json
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.exceptions import NotFound

app = Flask(__name__)

# Configuration
DOWNLOAD_DIR = "/home/kc/all_music/downloads"
FRONTEND_DIR = "frontend"
PORT = 3000

class PanPupServer:
    def __init__(self):
        self.ensure_download_dir()
    
    def ensure_download_dir(self):
        """Create download directory if it doesn't exist"""
        Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        print(f"✅ Download directory ready: {DOWNLOAD_DIR}")

    def parse_playlist(self, url):
        """Use yt-dlp to parse playlist/video info"""
        try:
            cmd = [
                'yt-dlp', 
                '--flat-playlist',
                '--print', '%(title)s|%(duration_string)s|%(id)s',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"yt-dlp error: {result.stderr}")
            
            tracks = []
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        tracks.append({
                            'id': parts[2],
                            'title': parts[0],
                            'duration': parts[1] if parts[1] != 'NA' else 'Unknown',
                            'selected': True
                        })
            
            return {'success': True, 'tracks': tracks}
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Request timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def download_tracks(self, url, track_ids):
        """Download selected tracks"""
        try:
            downloads = []
            
            if len(track_ids) == 1 and not self.is_playlist(url):
                # Single video download
                cmd = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '-o', f'{DOWNLOAD_DIR}/%(artist)s - %(title)s.%(ext)s',
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                downloads.append({
                    'id': track_ids[0],
                    'success': result.returncode == 0,
                    'error': result.stderr if result.returncode != 0 else None
                })
            else:
                # Multiple tracks from playlist
                for track_id in track_ids:
                    track_url = f"https://www.youtube.com/watch?v={track_id}"
                    cmd = [
                        'yt-dlp',
                        '-x', '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '-o', f'{DOWNLOAD_DIR}/%(artist)s - %(title)s.%(ext)s',
                        track_url
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    downloads.append({
                        'id': track_id,
                        'success': result.returncode == 0,
                        'error': result.stderr if result.returncode != 0 else None
                    })
            
            return {'success': True, 'downloads': downloads}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def is_playlist(self, url):
        """Check if URL is a playlist"""
        return 'playlist' in url or 'list=' in url

# Initialize server
pup_server = PanPupServer()

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)"""
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except NotFound:
        return "File not found", 404

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """Parse YouTube URL for track information"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    print(f"🐕 Parsing: {url}")
    result = pup_server.parse_playlist(url)
    
    if result['success']:
        print(f"✅ Found {len(result['tracks'])} track(s)")
    else:
        print(f"❌ Parse error: {result['error']}")
    
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def api_download():
    """Download selected tracks"""
    data = request.get_json()
    url = data.get('url')
    track_ids = data.get('track_ids', [])
    
    if not url or not track_ids:
        return jsonify({'success': False, 'error': 'Missing URL or track IDs'})
    
    print(f"🐕 Downloading {len(track_ids)} track(s)...")
    result = pup_server.download_tracks(url, track_ids)
    
    if result['success']:
        successful = sum(1 for d in result['downloads'] if d['success'])
        print(f"✅ Downloaded {successful}/{len(track_ids)} track(s)")
    else:
        print(f"❌ Download error: {result['error']}")
    
    return jsonify(result)

@app.route('/api/status')
def api_status():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': '🐕 Pan-Pup is ready!',
        'download_dir': DOWNLOAD_DIR
    })

if __name__ == '__main__':
    print("🐕 Starting Pan-Pup Music Downloader...")
    print(f"📁 Download directory: {DOWNLOAD_DIR}")
    print(f"🌐 Server starting on port {PORT}")
    print(f"🔗 Access at: http://localhost:{PORT}")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
