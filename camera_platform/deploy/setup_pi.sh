#!/bin/bash
#
# Raspberry Pi Initial Setup Script
# Configures the Pi for camera platform operation
#

set -e

echo "=========================================="
echo "Raspberry Pi Setup Script"
echo "=========================================="

# Update system
echo "[1/6] Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Enable I2C and Camera
echo "[2/6] Enabling I2C and Camera interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0

# Install system dependencies
echo "[3/6] Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    i2c-tools \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera \
    python3-picamera2 \
    python3-opencv \
    git \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libfontconfig1-dev \
    libcairo2-dev \
    libgdk-pixbuf2.0-dev \
    libpango1.0-dev \
    libgtk2.0-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    python3-pyqt5 \
    python3-h5py \
    libqt5gui5 \
    libqt5webkit5 \
    libqt5test5

# Increase GPU memory
echo "[4/6] Configuring GPU memory..."
if ! grep -q "gpu_mem=256" /boot/config.txt; then
    echo "gpu_mem=256" | sudo tee -a /boot/config.txt
fi

# Configure I2C speed
echo "[5/6] Configuring I2C speed..."
if ! grep -q "dtparam=i2c_arm_baudrate=400000" /boot/config.txt; then
    echo "dtparam=i2c_arm_baudrate=400000" | sudo tee -a /boot/config.txt
fi

# Add user to required groups
echo "[6/6] Adding user to required groups..."
sudo usermod -a -G i2c,video,gpio,dialout $USER

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: A reboot is required for changes to take effect."
echo ""