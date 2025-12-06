#!/bin/bash
#
# Install Hailo AI Runtime
# Downloads and installs Hailo-8 drivers and SDK
#

set -e

echo "=========================================="
echo "Hailo AI Runtime Installation"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi 5
if ! grep -q "Raspberry Pi 5" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi 5"
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

echo "[1/5] Downloading Hailo runtime..."
# Note: Replace with actual Hailo download URL when available
# For now, this is a placeholder
HAILO_VERSION="4.17.0"
HAILO_DEB="hailort_${HAILO_VERSION}_arm64.deb"

# Check if file exists locally first
if [ -f "/home/$USER/Downloads/$HAILO_DEB" ]; then
    echo "Using local Hailo package..."
    cp "/home/$USER/Downloads/$HAILO_DEB" .
else
    echo "Please download Hailo runtime from:"
    echo "https://hailo.ai/developer-zone/software-downloads/"
    echo ""
    echo "Place the .deb file in ~/Downloads/ and run this script again."
    echo ""
    echo "Expected filename: $HAILO_DEB"
    exit 1
fi

echo "[2/5] Installing Hailo runtime..."
sudo dpkg -i $HAILO_DEB || sudo apt-get install -f -y

echo "[3/5] Installing Hailo Python package..."
pip install hailort

echo "[4/5] Verifying installation..."
if hailortcli fw-control identify 2>/dev/null; then
    echo "✓ Hailo device detected"
else
    echo "⚠ Hailo device not detected (this is normal if HAT not connected yet)"
fi

echo "[5/5] Downloading example models..."
MODELS_DIR="/home/$USER/camera_platform/models"
mkdir -p $MODELS_DIR

echo "Example models can be downloaded from:"
echo "https://hailo.ai/developer-zone/model-zoo/"
echo ""
echo "Recommended models for camera platform:"
echo "  - yolov5s.hef (fast, general purpose)"
echo "  - yolov8s.hef (improved accuracy)"
echo "  - yolov5m.hef (better accuracy, slower)"
echo ""
echo "Place .hef files in: $MODELS_DIR"

# Cleanup
cd /
rm -rf $TEMP_DIR

echo ""
echo "=========================================="
echo "Hailo Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Download model files (.hef) from Hailo Model Zoo"
echo "2. Place models in: $MODELS_DIR"
echo "3. Connect AI HAT+ to Raspberry Pi"
echo "4. Reboot: sudo reboot"
echo "5. Verify: hailortcli fw-control identify"
echo ""