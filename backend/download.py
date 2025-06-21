#!/usr/bin/env python3
import subprocess
import json

def parse_youtube_url(url):
    """Extract track info from YouTube URL"""
    try:
        cmd = ['yt-dlp', '--flat-playlist', '--print', '%(title)s|%(duration_string)s|%(id)s', url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {'success': False, 'error': result.stderr}
            
        tracks = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    tracks.append({
                        'id': parts[2],
                        'title': parts[0], 
                        'duration': parts[1],
                        'selected': True
                    })
                    
        return {'success': True, 'tracks': tracks}
    except Exception as e:
        return {'success': False, 'error': str(e)}
