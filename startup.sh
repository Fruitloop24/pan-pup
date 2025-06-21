#!/bin/bash

# Pan-Pup Music Downloader Smart Startup Script
echo "🐕 Starting Pan-Pup Music Downloader..."

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found. Run this from the pan-pup root directory."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Run this from the pan-pup root directory."
    exit 1
fi

# Go to backend directory
cd backend

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Make sure python3-venv is installed."
        exit 1
    fi
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if packages are installed
echo "📥 Checking/installing requirements..."
pip install -r ../requirements.txt

# Install yt-dlp if not available
if ! command -v yt-dlp &> /dev/null; then
    echo "🎵 Installing yt-dlp..."
    pip install yt-dlp
fi

# Create downloads directory
echo "📁 Ensuring download directory exists..."
mkdir -p ~/all_music/downloads

echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Pan-Pup server on port 3000..."
echo "🌐 Access at: http://localhost:3000"
echo "📁 Downloads go to: ~/all_music/downloads"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 server.py