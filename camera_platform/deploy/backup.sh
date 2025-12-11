#!/bin/bash
#
# Backup Script
# Creates backup of configuration and data from Raspberry Pi
#
# Usage: ./backup.sh <pi-hostname-or-ip> [username]
#

set -e

PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PROJECT_NAME="camera_platform"
REMOTE_DIR="/home/${PI_USER}/${PROJECT_NAME}"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "Camera Platform Backup"
echo "=========================================="
echo ""
echo "Source: ${PI_USER}@${PI_HOST}"
echo "Backup: ${BACKUP_DIR}"
echo ""

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup configuration
echo "[1/4] Backing up configuration..."
rsync -avz ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/config/ ${BACKUP_DIR}/config/

# Backup data
echo "[2/4] Backing up data..."
rsync -avz ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/data/ ${BACKUP_DIR}/data/

# Backup logs
echo "[3/4] Backing up logs..."
rsync -avz ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/logs/ ${BACKUP_DIR}/logs/

# Create backup info file
echo "[4/4] Creating backup info..."
cat > ${BACKUP_DIR}/backup_info.txt <<EOF
Backup Information
==================
Date: $(date)
Source: ${PI_USER}@${PI_HOST}
Remote Directory: ${REMOTE_DIR}
Backup Directory: ${BACKUP_DIR}

Contents:
- Configuration files
- Captured images and videos
- System logs
- Calibration data
EOF

echo ""
echo "=========================================="
echo "Backup Complete!"
echo "=========================================="
echo ""
echo "Backup location: ${BACKUP_DIR}"
echo ""
ls -lh ${BACKUP_DIR}
echo ""