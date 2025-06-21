# 🐕 Pan-Pup Music Downloader

**Your Personal YouTube Music Library System**

Pan-Pup is a complete DIY music ecosystem that transforms any Raspberry Pi into a powerful music server. Download from YouTube, organize with file management, and stream anywhere with mobile apps.

## 🎵 What Pan-Pup Does

- **Parse YouTube playlists** - Handles single songs, albums, and massive playlists (600+ tracks tested!)
- **Smart downloading** - Select which tracks to download, batch processing
- **Auto-organization** - Downloads to organized folders for easy management
- **Web interface** - Beautiful, mobile-friendly UI with auto-clipboard detection
- **Multi-service integration** - Works with File Browser, Navidrome, and mobile streaming apps

## 🏗️ Complete System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🐕 Pan-Pup    │───▶│  📁 File Browser │───▶│  🎵 Navidrome   │
│  (Port 3000)    │    │   (Port 8081)    │    │   (Port 4533)   │
│  Download Music │    │ Organize & Manage│    │  Music Library  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │ 📱 Substream    │
                                               │  Mobile App     │
                                               └─────────────────┘
```

**Access via Cloudflare Tunnels:**
- `your-panpup.domain.com` → Pan-Pup Downloader
- `your-files.domain.com` → File Browser
- `your-music.domain.com` → Navidrome Library

## 🚀 Installation Options

**Choose your path:**

### 🎯 Option 1: Complete Automated Setup (Recommended)
**Perfect for: Users who want the full ecosystem with systemd services**

```bash
# Clone and run the ecosystem installer
git clone https://github.com/Fruitloop24/pan-pup.git
cd pan-pup
chmod +x install-ecosystem.sh
./install-ecosystem.sh
```

**This installs & configures:**
- ✅ File Browser (systemd service)
- ✅ Navidrome (systemd service) 
- ✅ Pan-Pup (systemd service ready)
- ✅ All directories and permissions

**Then start Pan-Pup:**
```bash
./startup.sh  # Manual start
# OR
sudo systemctl start panpup  # Service start
```

### 🎯 Option 2: Pan-Pup Only (Quick Start)
**Perfect for: Testing or users who already have File Browser/Navidrome**

```bash
# Clone and run Pan-Pup only
git clone https://github.com/Fruitloop24/pan-pup.git
cd pan-pup
chmod +x startup.sh
./startup.sh
```

Access at: `http://localhost:3000`

## 📋 Prerequisites

### System Requirements
- **Raspberry Pi 4** (2GB RAM minimum, 4GB+ recommended) or any Linux system
- **Raspberry Pi OS** (64-bit recommended) or Ubuntu/Debian
- **Python 3.8+**
- **Storage**: USB drive or SSD (500GB+ recommended for large music libraries)

### Required Packages
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install python3 python3-pip python3-venv git curl -y

# Install yt-dlp system-wide
pip3 install --break-system-packages yt-dlp
```

## 🛠️ Manual Installation Guide

**For advanced users who want full control over each component**

### 1. Install Pan-Pup

```bash
# Clone repository
git clone https://github.com/Fruitloop24/pan-pup.git
cd pan-pup

# Setup and start (automatic setup!)
chmod +x startup.sh
./startup.sh
```

### 2. Install File Browser (Manual)

```bash
# Download and install File Browser
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash

# Create systemd service
sudo nano /etc/systemd/system/filebrowser.service
```

**File Browser Service Configuration:**
```ini
[Unit]
Description=FileBrowser
After=network.target

[Service]
Type=simple
User=pi
Group=pi
ExecStart=/usr/local/bin/filebrowser -r /home/pi/all_music --address 0.0.0.0 --port 8081
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable filebrowser
sudo systemctl start filebrowser
```

### 3. Install Navidrome (Manual)

```bash
# Create navidrome user
sudo useradd -r -s /bin/false navidrome

# Download latest release
wget https://github.com/navidrome/navidrome/releases/latest/download/navidrome_linux_amd64.tar.gz

# Extract and install
sudo tar -xvzf navidrome_linux_amd64.tar.gz -C /opt/navidrome/
sudo chown -R navidrome:navidrome /opt/navidrome

# Create systemd service
sudo nano /etc/systemd/system/navidrome.service
```

**Navidrome Service Configuration:**
```ini
[Unit]
Description=Navidrome
After=network.target

[Service]
Type=simple
User=navidrome
Group=navidrome
ExecStart=/opt/navidrome/navidrome --musicfolder /home/pi/all_music --datafolder /var/lib/navidrome --address 0.0.0.0 --port 4533
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Create data folder
sudo mkdir -p /var/lib/navidrome
sudo chown navidrome:navidrome /var/lib/navidrome

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable navidrome
sudo systemctl start navidrome
```

### 4. Directory Structure Setup

```bash
# Create music directory structure
mkdir -p ~/all_music/downloads
mkdir -p ~/all_music/organized
chmod 755 ~/all_music
```

## 🌐 Cloudflare Tunnel Setup

### 1. Install cloudflared

```bash
# Download and install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```

### 2. Create Tunnel

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create my-music-server

# Note the tunnel ID from output
```

### 3. Configure Tunnel

Create `/etc/cloudflared/config.yml`:
```yaml
tunnel: YOUR-TUNNEL-ID-HERE
credentials-file: /etc/cloudflared/YOUR-TUNNEL-ID-HERE.json
ingress:
  - hostname: your-panpup.yourdomain.com
    service: http://localhost:3000
  - hostname: your-files.yourdomain.com  
    service: http://localhost:8081
  - hostname: your-music.yourdomain.com
    service: http://localhost:4533
  - service: http_status:404
```

### 4. Setup DNS and Service

```bash
# Add DNS records
cloudflared tunnel route dns YOUR-TUNNEL-ID your-panpup.yourdomain.com
cloudflared tunnel route dns YOUR-TUNNEL-ID your-files.yourdomain.com
cloudflared tunnel route dns YOUR-TUNNEL-ID your-music.yourdomain.com

# Install as service
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

## 🔒 Cloudflare Access Policies (Optional)

Protect your services with email-based authentication:

1. **Cloudflare Dashboard** → **Zero Trust** → **Access** → **Applications**
2. **Add Application** → **Self-hosted**
3. **Application Configuration:**
   - Application name: "My Music Server"
   - Subdomain: `your-panpup`, `your-files`
   - Domain: `yourdomain.com`
4. **Add Policy:**
   - Policy name: "Authorized Users"
   - Action: Allow
   - Include: Email addresses (add your trusted users)

**Note:** Mobile apps may have issues with Access Policies. Consider excluding Navidrome or using bypass rules for your home network.

## 🎯 Usage Guide

### Downloading Music

1. **Open Pan-Pup** in your browser
2. **Find music on YouTube** - single songs, albums, or playlists
3. **Copy the URL** - Pan-Pup auto-detects from clipboard
4. **Click Parse** - see all available tracks
5. **Select tracks** - choose which ones to download
6. **Click Download** - batch processing (recommended: 10-50 tracks at a time)

### File Organization

1. **Open File Browser** - access your downloads
2. **Create folders** by artist, album, genre, etc.
3. **Move/rename files** as needed
4. **Navidrome auto-scans** for new music

### Mobile Access

1. **Install Substream** (iOS/Android) or similar Subsonic-compatible app
2. **Configure server:**
   - Server: `your-music.yourdomain.com`
   - Username/Password: (created in Navidrome)
3. **Stream anywhere!**

## ⚡ Performance & Features

- **Tested Performance**: 700+ songs downloaded in 24 hours for 2 users
- **Smart Batching**: Download 10-50 tracks at a time to prevent timeouts
- **Auto-clipboard Detection**: Paste YouTube URLs and they auto-populate
- **Playlist Intelligence**: Handles massive playlists (600+ tracks tested)
- **Background Processing**: Run via nohup, screen, tmux, or systemd service
- **Mobile-Friendly**: Responsive design works on phones/tablets

## 🛠️ Running Pan-Pup as Background Service

**Note: Pan-Pup runs manually for security reasons (requires user context for downloads)**

### Option 1: Screen/Tmux (Recommended)
```bash
# Using screen
screen -S panpup
cd ~/pan-pup
./startup.sh
# Detach: Ctrl+A then D
# Reattach: screen -r panpup

# Using tmux
tmux new -s panpup
cd ~/pan-pup
./startup.sh
# Detach: Ctrl+B then D
# Reattach: tmux attach -t panpup
```

### Option 2: Background Process
```bash
# Start in background
cd ~/pan-pup
nohup ./startup.sh > panpup.log 2>&1 &

# Check logs
tail -f panpup.log

# Stop
pkill -f startup.sh
```

### Option 3: Systemd Service (If using automated installer)
```bash
# Start Pan-Pup service (created by install-ecosystem.sh)
sudo systemctl start panpup

# Check status
sudo systemctl status panpup
```

## 🔧 Troubleshooting

### Common Issues

**"yt-dlp not found"**
```bash
# Install yt-dlp globally
pip3 install --break-system-packages yt-dlp
# Or ensure virtual environment is activated
```

**Downloads timeout through Cloudflare**
- Use local IP for large downloads: `http://192.168.1.XXX:3000`
- Reduce batch size to 10-20 tracks
- Consider Cloudflare Pro plan for longer timeouts

**Mobile app can't connect**
- Check Access Policy settings
- Try bypassing Access Policy for Navidrome
- Verify Navidrome is accessible at `your-music.yourdomain.com`

**Service won't start**
```bash
# Check status
sudo systemctl status panpup
sudo systemctl status filebrowser
sudo systemctl status navidrome
sudo systemctl status cloudflared

# Check logs
sudo journalctl -u panpup -f
tail -f ~/pan-pup/panpup.log
```

### Port Reference
- **Pan-Pup:** 3000
- **File Browser:** 8081  
- **Navidrome:** 4533
- **Cloudflare Tunnel:** Automatic

### Log Locations
- **Pan-Pup:** `~/pan-pup/panpup.log` (if using nohup)
- **System services:** `sudo journalctl -u SERVICE_NAME`
- **Cloudflared:** `sudo journalctl -u cloudflared`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **yt-dlp** - Powerful YouTube downloader
- **Flask** - Web framework
- **File Browser** - File management interface
- **Navidrome** - Music server
- **Cloudflare** - Tunneling and security

---

**Made with ❤️ for music lovers who want to own their library**

*Transform any Raspberry Pi into a complete music ecosystem in under an hour!*