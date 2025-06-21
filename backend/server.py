#!/usr/bin/env python3
"""
Pan-Pup Backend Server
Flask API endpoints for YouTube downloading
"""

import os
import subprocess
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import NotFound

# Configuration
DOWNLOAD_DIR = "/home/kc/all_music/downloads"
FRONTEND_DIR = "../frontend"

app = Flask(__name__)

class YouTubeProcessor:
    def __init__(self):
        self.ensure_download_dir()
    
    def ensure_download_dir(self):
        """Create download directory if it doesn't exist"""
        Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        print(f"✅ Download directory ready: {DOWNLOAD_DIR}")

    def parse_youtube_url(self, url):
        """Extract track info from YouTube URL using yt-dlp"""
        try:
            print(f"🐕 Parsing URL: {url}")
            
            # Use yt-dlp to get playlist/video info
            cmd = [
                'yt-dlp', 
                '--flat-playlist',
                '--print', '%(title)s|%(duration_string)s|%(id)s',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Unknown yt-dlp error"
                print(f"❌ yt-dlp error: {error_msg}")
                return {'success': False, 'error': error_msg}
            
            tracks = []
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            for line in lines:
                if '|' in line:
                    parts = line.split('|', 2)  # Split into max 3 parts
                    if len(parts) >= 3:
                        title = parts[0].strip()
                        duration = parts[1].strip() if parts[1].strip() != 'NA' else 'Unknown'
                        video_id = parts[2].strip()
                        
                        tracks.append({
                            'id': video_id,
                            'title': title,
                            'duration': duration,
                            'selected': True
                        })
            
            if not tracks:
                # Fallback for single videos that might not parse correctly
                print("🔄 Trying fallback method for single video...")
                return self.parse_single_video_fallback(url)
            
            print(f"✅ Found {len(tracks)} track(s)")
            return {'success': True, 'tracks': tracks}
            
        except subprocess.TimeoutExpired:
            print("⏰ Parse request timed out")
            return {'success': False, 'error': 'Request timed out (60s limit)'}
        except Exception as e:
            print(f"💥 Parse exception: {str(e)}")
            return {'success': False, 'error': f'Parse error: {str(e)}'}

    def parse_single_video_fallback(self, url):
        """Fallback method for single videos"""
        try:
            cmd = [
                'yt-dlp',
                '--print', '%(title)s|%(duration_string)s|%(id)s',
                '--no-playlist',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {'success': False, 'error': 'Could not parse video info'}
            
            line = result.stdout.strip()
            if '|' in line:
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    return {
                        'success': True, 
                        'tracks': [{
                            'id': parts[2].strip(),
                            'title': parts[0].strip(),
                            'duration': parts[1].strip() if parts[1].strip() != 'NA' else 'Unknown',
                            'selected': True
                        }]
                    }
            
            return {'success': False, 'error': 'Could not extract video info'}
            
        except Exception as e:
            return {'success': False, 'error': f'Fallback parse error: {str(e)}'}

    def download_tracks(self, url, track_ids):
        """Download selected tracks using yt-dlp"""
        try:
            print(f"🐕 Starting download of {len(track_ids)} track(s)")
            downloads = []
            
            for track_id in track_ids:
                print(f"📥 Downloading track: {track_id}")
                
                # Construct YouTube URL for the specific track
                track_url = f"https://www.youtube.com/watch?v={track_id}"
                
                # yt-dlp command for audio download
                cmd = [
                    'yt-dlp',
                    '-x',  # Extract audio
                    '--audio-format', 'mp3',
                    '--audio-quality', '0',  # Best quality
                    '--add-metadata',  # Add metadata to file
                    '--embed-thumbnail',  # Embed album art if available
                    '-o', f'{DOWNLOAD_DIR}/%(artist)s - %(title)s.%(ext)s',
                    track_url
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout per track
                    
                    success = result.returncode == 0
                    error_msg = None
                    
                    if not success:
                        error_msg = result.stderr.strip() or "Download failed"
                        print(f"❌ Failed to download {track_id}: {error_msg}")
                    else:
                        print(f"✅ Successfully downloaded {track_id}")
                    
                    downloads.append({
                        'id': track_id,
                        'success': success,
                        'error': error_msg
                    })
                    
                except subprocess.TimeoutExpired:
                    print(f"⏰ Download timeout for {track_id}")
                    downloads.append({
                        'id': track_id,
                        'success': False,
                        'error': 'Download timed out (5 minutes)'
                    })
                except Exception as e:
                    print(f"💥 Download exception for {track_id}: {str(e)}")
                    downloads.append({
                        'id': track_id,
                        'success': False,
                        'error': str(e)
                    })
            
            successful_downloads = sum(1 for d in downloads if d['success'])
            print(f"🎉 Download complete: {successful_downloads}/{len(track_ids)} successful")
            
            return {'success': True, 'downloads': downloads}
            
        except Exception as e:
            print(f"💥 Download batch error: {str(e)}")
            return {'success': False, 'error': f'Download error: {str(e)}'}

# Initialize processor
processor = YouTubeProcessor()

# API Routes
@app.route('/api/parse', methods=['POST'])
def api_parse():
    """Parse YouTube URL for track information"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        url = data['url'].strip()
        if not url:
            return jsonify({'success': False, 'error': 'Empty URL provided'})
        
        # Basic URL validation
        if not ('youtube.com' in url or 'youtu.be' in url):
            return jsonify({'success': False, 'error': 'Not a valid YouTube URL'})
        
        result = processor.parse_youtube_url(url)
        return jsonify(result)
        
    except Exception as e:
        print(f"💥 API parse error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error during parsing'})

@app.route('/api/download', methods=['POST'])
def api_download():
    """Download selected tracks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        url = data.get('url', '').strip()
        track_ids = data.get('track_ids', [])
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'})
        
        if not track_ids or not isinstance(track_ids, list):
            return jsonify({'success': False, 'error': 'No track IDs provided'})
        
        if len(track_ids) > 50:  # Reasonable limit
            return jsonify({'success': False, 'error': 'Too many tracks (max 50)'})
        
        result = processor.download_tracks(url, track_ids)
        return jsonify(result)
        
    except Exception as e:
        print(f"💥 API download error: {str(e)}")
        return jsonify({'success': False, 'error': 'Server error during download'})

@app.route('/api/status')
def api_status():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': '🐕 Pan-Pup backend is ready!',
        'download_dir': DOWNLOAD_DIR,
        'yt_dlp_available': True  # We can add actual check later
    })

# Static file serving (for when this runs standalone)
@app.route('/')
def serve_index():
    """Serve the main frontend page"""
    try:
        return send_from_directory(FRONTEND_DIR, 'index.html')
    except NotFound:
        return "Frontend files not found. Make sure frontend/ directory exists.", 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files (CSS, JS, etc.)"""
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except NotFound:
        return f"File {filename} not found", 404

if __name__ == '__main__':
    print("🐕 Pan-Pup Backend Server Starting...")
    print(f"📁 Download directory: {DOWNLOAD_DIR}")
    print(f"🌐 Frontend directory: {FRONTEND_DIR}")
    
    # Test yt-dlp availability
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ yt-dlp available: {result.stdout.strip()}")
        else:
            print("❌ yt-dlp not working properly")
    except Exception as e:
        print(f"❌ yt-dlp not found: {e}")
        print("Install with: pip3 install --break-system-packages yt-dlp")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
