#!/bin/bash
#
# Install Python Dependencies
# Sets up virtual environment and installs all required packages
#

set -e

PROJECT_DIR="/home/$USER/camera_platform"
VENV_DIR="$PROJECT_DIR/venv"

echo "=========================================="
echo "Installing Python Dependencies"
echo "=========================================="

cd $PROJECT_DIR

# Create virtual environment
echo "[1/4] Creating virtual environment..."
python3 -m venv $VENV_DIR

# Activate virtual environment
echo "[2/4] Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
echo "[3/4] Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "[4/4] Installing Python packages..."
pip install -r requirements.txt

# Install additional packages for Raspberry Pi
echo "Installing Raspberry Pi specific packages..."
pip install RPi.GPIO smbus2

# Verify installations
echo ""
echo "Verifying installations..."
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python3 -c "import cv2; print(f'OpenCV: {cv2.__version__}')"
python3 -c "import flask; print(f'Flask: {flask.__version__}')"
python3 -c "import picamera2; print('Picamera2: OK')"
python3 -c "import RPi.GPIO; print('RPi.GPIO: OK')"

echo ""
echo "=========================================="
echo "Dependencies Installed Successfully!"
echo "=========================================="
echo ""
echo "Virtual environment: $VENV_DIR"
echo "To activate: source $VENV_DIR/bin/activate"
echo ""