#!/bin/bash
#
# Setup Systemd Service
# Configures camera platform to run on boot
#

set -e

PROJECT_DIR="/home/$USER/camera_platform"
SERVICE_NAME="camera-platform"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=========================================="
echo "Setting up Systemd Service"
echo "=========================================="

# Create systemd service file
echo "[1/3] Creating systemd service file..."
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Camera Platform with Stewart Platform Control
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/web_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "[2/3] Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "[3/3] Enabling service to start on boot..."
sudo systemctl enable $SERVICE_NAME

echo ""
echo "=========================================="
echo "Systemd Service Configured!"
echo "=========================================="
echo ""
echo "Service name: $SERVICE_NAME"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    journalctl -u $SERVICE_NAME -f"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo ""
echo "The service will start automatically on boot."
echo ""