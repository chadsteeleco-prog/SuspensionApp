#!/bin/bash
#
# Camera Platform Deployment Script
# Deploys complete system to Raspberry Pi via SSH
#
# Usage: ./deploy.sh <pi-hostname-or-ip> [username]
#
# Example: ./deploy.sh raspberrypi.local pi
#          ./deploy.sh 192.168.1.100 ubuntu
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PROJECT_NAME="camera_platform"
REMOTE_DIR="/home/${PI_USER}/${PROJECT_NAME}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Camera Platform Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Target: ${GREEN}${PI_USER}@${PI_HOST}${NC}"
echo -e "Remote Directory: ${GREEN}${REMOTE_DIR}${NC}"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
    echo -e "${YELLOW}Warning: No SSH key found. You may be prompted for password multiple times.${NC}"
    echo -e "${YELLOW}Consider setting up SSH key authentication first.${NC}"
    echo ""
fi

# Test SSH connection
echo -e "${BLUE}[1/8]${NC} Testing SSH connection..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes ${PI_USER}@${PI_HOST} exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo -e "${YELLOW}Please ensure:${NC}"
    echo "  1. Raspberry Pi is powered on and connected to network"
    echo "  2. SSH is enabled on the Pi"
    echo "  3. Hostname/IP is correct"
    echo "  4. SSH key is set up or you have the password"
    exit 1
fi

# Create remote directory
echo -e "${BLUE}[2/8]${NC} Creating remote directory..."
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${REMOTE_DIR}"
echo -e "${GREEN}✓ Directory created${NC}"

# Sync project files
echo -e "${BLUE}[3/8]${NC} Syncing project files..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude 'venv' \
    --exclude 'node_modules' \
    --exclude '.DS_Store' \
    --exclude 'data/images/*' \
    --exclude 'data/videos/*' \
    --exclude 'logs/*' \
    ../ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/
echo -e "${GREEN}✓ Files synced${NC}"

# Copy deployment scripts
echo -e "${BLUE}[4/8]${NC} Copying deployment scripts..."
scp setup_pi.sh install_dependencies.sh setup_systemd.sh ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/deploy/
echo -e "${GREEN}✓ Scripts copied${NC}"

# Run setup script
echo -e "${BLUE}[5/8]${NC} Running setup script on Pi..."
ssh ${PI_USER}@${PI_HOST} "cd ${REMOTE_DIR}/deploy && chmod +x *.sh && ./setup_pi.sh"
echo -e "${GREEN}✓ Setup complete${NC}"

# Install dependencies
echo -e "${BLUE}[6/8]${NC} Installing dependencies..."
ssh ${PI_USER}@${PI_HOST} "cd ${REMOTE_DIR}/deploy && ./install_dependencies.sh"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup systemd service
echo -e "${BLUE}[7/8]${NC} Setting up systemd service..."
ssh ${PI_USER}@${PI_HOST} "cd ${REMOTE_DIR}/deploy && sudo ./setup_systemd.sh"
echo -e "${GREEN}✓ Systemd service configured${NC}"

# Test configuration
echo -e "${BLUE}[8/8]${NC} Testing configuration..."
ssh ${PI_USER}@${PI_HOST} "cd ${REMOTE_DIR} && python3 -c 'import sys; print(f&quot;Python {sys.version}&quot;)'"
echo -e "${GREEN}✓ Configuration verified${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Reboot the Raspberry Pi:"
echo -e "   ${BLUE}ssh ${PI_USER}@${PI_HOST} 'sudo reboot'${NC}"
echo ""
echo "2. After reboot, check service status:"
echo -e "   ${BLUE}ssh ${PI_USER}@${PI_HOST} 'sudo systemctl status camera-platform'${NC}"
echo ""
echo "3. Access web interface:"
echo -e "   ${BLUE}http://${PI_HOST}:5000${NC}"
echo ""
echo "4. View logs:"
echo -e "   ${BLUE}ssh ${PI_USER}@${PI_HOST} 'journalctl -u camera-platform -f'${NC}"
echo ""