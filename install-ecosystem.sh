#!/bin/bash

# Pan-Pup Complete Music Ecosystem Installer
# This installs File Browser, Navidrome, and sets up the complete system

echo "🎵 Installing Pan-Pup Complete Music Ecosystem..."
echo "This will install:"
echo "  - File Browser (Port 8081)"
echo "  - Navidrome (Port 4533)"
echo "  - Pan-Pup (Port 3000)"
echo ""

# Prompt for confirmation
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# Get username for paths
USERNAME=$(whoami)
MUSIC_DIR="/home/$USERNAME/all_music"

echo "📁 Setting up music directory structure..."
mkdir -p "$MUSIC_DIR/downloads"
mkdir -p "$MUSIC_DIR/organized"
chmod 755 "$MUSIC_DIR"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install curl wget python3 python3-pip python3-venv git -y

# Install File Browser
echo "📁 Installing File Browser..."
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash

# Create File Browser service
echo "🔧 Setting up File Browser service..."
sudo tee /etc/systemd/system/filebrowser.service > /dev/null << EOF
[Unit]
Description=FileBrowser
After=network.target

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
ExecStart=/usr/local/bin/filebrowser -r $MUSIC_DIR --address 0.0.0.0 --port 8081
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Install Navidrome
echo "🎵 Installing Navidrome..."

# Detect architecture
ARCH=$(uname -m)
if [[ $ARCH == "aarch64" ]]; then
    NAVIDROME_ARCH="arm64"
elif [[ $ARCH == "armv7l" ]]; then
    NAVIDROME_ARCH="armv7"
else
    NAVIDROME_ARCH="amd64"
fi

# Create navidrome user
sudo useradd -r -s /bin/false navidrome 2>/dev/null || true

# Create directories
sudo mkdir -p /opt/navidrome
sudo mkdir -p /var/lib/navidrome

# Download and install Navidrome
NAVIDROME_URL="https://github.com/navidrome/navidrome/releases/latest/download/navidrome_linux_${NAVIDROME_ARCH}.tar.gz"
echo "Downloading from: $NAVIDROME_URL"

wget -O /tmp/navidrome.tar.gz "$NAVIDROME_URL"
sudo tar -xvzf /tmp/navidrome.tar.gz -C /opt/navidrome/
sudo chown -R navidrome:navidrome /opt/navidrome
sudo chown -R navidrome:navidrome /var/lib/navidrome

# Create Navidrome service
echo "🔧 Setting up Navidrome service..."
sudo tee /etc/systemd/system/navidrome.service > /dev/null << EOF
[Unit]
Description=Navidrome
After=network.target

[Service]
Type=simple
User=navidrome
Group=navidrome
ExecStart=/opt/navidrome/navidrome --musicfolder $MUSIC_DIR --datafolder /var/lib/navidrome --address 0.0.0.0 --port 4533
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set up Pan-Pup service (optional)
echo "🐕 Setting up Pan-Pup service..."
sudo tee /etc/systemd/system/panpup.service > /dev/null << EOF
[Unit]
Description=Pan-Pup Music Downloader
After=network.target

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
WorkingDirectory=/home/$USERNAME/pan-pup
ExecStart=/bin/bash /home/$USERNAME/pan-pup/startup.sh
Environment=PATH=/home/$USERNAME/pan-pup/backend/venv/bin:/usr/local/bin:/usr/bin:/bin
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
echo "🔄 Enabling services..."
sudo systemctl daemon-reload

# Enable and start File Browser
sudo systemctl enable filebrowser
sudo systemctl start filebrowser

# Enable and start Navidrome
sudo systemctl enable navidrome
sudo systemctl start navidrome

# Enable Pan-Pup service (but don't start it - let user choose)
sudo systemctl enable panpup

# Clean up
rm -f /tmp/navidrome.tar.gz

echo ""
echo "✅ Installation complete!"
echo ""
echo "🌐 Services are running on:"
echo "  📁 File Browser:  http://localhost:8081"
echo "  🎵 Navidrome:     http://localhost:4533"
echo "  🐕 Pan-Pup:       http://localhost:3000 (start with ./startup.sh or sudo systemctl start panpup)"
echo ""
echo "📁 Music directory: $MUSIC_DIR"
echo ""
echo "🔧 Service management:"
echo "  sudo systemctl status filebrowser"
echo "  sudo systemctl status navidrome"
echo "  sudo systemctl status panpup"
echo ""
echo "🌍 For external access, set up Cloudflare tunnels (see README.md)"
echo ""
echo "🎉 Your complete music ecosystem is ready!"