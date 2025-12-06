#!/bin/bash
#
# Setup SSH Key Authentication
# Simplifies deployment by setting up passwordless SSH
#
# Usage: ./setup_ssh_key.sh <pi-hostname-or-ip> [username]
#

PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"

echo "=========================================="
echo "SSH Key Setup"
echo "=========================================="
echo ""
echo "Target: ${PI_USER}@${PI_HOST}"
echo ""

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "No SSH key found. Generating new key..."
    ssh-keygen -t ed25519 -C "camera-platform-deployment" -f ~/.ssh/id_ed25519 -N ""
    echo "✓ SSH key generated"
else
    echo "✓ SSH key already exists"
fi

# Copy key to Pi
echo ""
echo "Copying SSH key to Raspberry Pi..."
echo "You will be prompted for the Pi's password."
echo ""

if [ -f ~/.ssh/id_ed25519.pub ]; then
    ssh-copy-id -i ~/.ssh/id_ed25519.pub ${PI_USER}@${PI_HOST}
elif [ -f ~/.ssh/id_rsa.pub ]; then
    ssh-copy-id -i ~/.ssh/id_rsa.pub ${PI_USER}@${PI_HOST}
fi

# Test connection
echo ""
echo "Testing SSH connection..."
if ssh -o BatchMode=yes ${PI_USER}@${PI_HOST} exit 2>/dev/null; then
    echo "✓ SSH key authentication successful!"
    echo ""
    echo "You can now deploy without entering a password:"
    echo "  ./deploy.sh ${PI_HOST} ${PI_USER}"
else
    echo "✗ SSH key authentication failed"
    echo "Please check your configuration and try again."
    exit 1
fi