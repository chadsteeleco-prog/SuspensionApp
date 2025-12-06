#!/bin/bash
#
# Quick Update Script
# Updates code on Raspberry Pi without full reinstall
#
# Usage: ./update.sh <pi-hostname-or-ip> [username]
#

set -e

PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PROJECT_NAME="camera_platform"
REMOTE_DIR="/home/${PI_USER}/${PROJECT_NAME}"

echo "=========================================="
echo "Camera Platform Quick Update"
echo "=========================================="
echo ""
echo "Target: ${PI_USER}@${PI_HOST}"
echo ""

# Sync only source files
echo "[1/3] Syncing source files..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude 'data/' \
    --exclude 'logs/' \
    ../src/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/src/

echo "[2/3] Syncing configuration files..."
rsync -avz --progress \
    ../config/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/config/

# Restart service
echo "[3/3] Restarting service..."
ssh ${PI_USER}@${PI_HOST} "sudo systemctl restart camera-platform"

echo ""
echo "=========================================="
echo "Update Complete!"
echo "=========================================="
echo ""
echo "Service restarted. Check status:"
echo "  ssh ${PI_USER}@${PI_HOST} 'sudo systemctl status camera-platform'"
echo ""