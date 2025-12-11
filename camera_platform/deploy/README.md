# Deployment Scripts for Raspberry Pi

This directory contains scripts for automated deployment and management of the camera platform on Raspberry Pi.

## Prerequisites

### On Your Computer
- SSH client installed
- rsync installed
- Network access to Raspberry Pi

### On Raspberry Pi
- Raspberry Pi OS (64-bit) or Ubuntu
- SSH enabled
- Network configured
- User account created (default: `pi`)

---

## Quick Start

### 1. Setup SSH Key Authentication (One-time)

```bash
cd deploy
chmod +x *.sh
./setup_ssh_key.sh raspberrypi.local pi
```

This sets up passwordless SSH access to your Pi.

### 2. Deploy Complete System

```bash
./deploy.sh raspberrypi.local pi
```

This will:
- Copy all project files to the Pi
- Install system dependencies
- Set up Python virtual environment
- Install Python packages
- Configure systemd service
- Enable auto-start on boot

**Duration:** ~15-20 minutes (depending on network speed)

### 3. Reboot Raspberry Pi

```bash
ssh pi@raspberrypi.local 'sudo reboot'
```

After reboot, the camera platform will start automatically!

---

## Scripts Overview

### `setup_ssh_key.sh`
**Purpose:** Set up SSH key authentication for passwordless deployment

**Usage:**
```bash
./setup_ssh_key.sh <hostname> [username]
```

**Example:**
```bash
./setup_ssh_key.sh raspberrypi.local pi
./setup_ssh_key.sh 192.168.1.100 ubuntu
```

**What it does:**
- Generates SSH key if not exists
- Copies public key to Raspberry Pi
- Tests connection

---

### `deploy.sh`
**Purpose:** Full deployment of camera platform to Raspberry Pi

**Usage:**
```bash
./deploy.sh <hostname> [username]
```

**Example:**
```bash
./deploy.sh raspberrypi.local pi
./deploy.sh 192.168.1.100 ubuntu
```

**What it does:**
1. Tests SSH connection
2. Creates remote directory
3. Syncs all project files
4. Runs setup script
5. Installs dependencies
6. Configures systemd service
7. Verifies installation

**Files synced:**
- Source code (`src/`)
- Configuration (`config/`)
- Documentation
- Requirements
- Deployment scripts

**Files excluded:**
- `.git/`
- `__pycache__/`
- `*.pyc`
- Virtual environments
- Data files (images/videos)
- Log files

---

### `setup_pi.sh`
**Purpose:** Configure Raspberry Pi system settings

**Runs on:** Raspberry Pi (called by deploy.sh)

**What it does:**
1. Updates system packages
2. Enables I2C interface
3. Enables camera interface
4. Installs system dependencies
5. Configures GPU memory (256MB)
6. Sets I2C speed (400kHz)
7. Adds user to required groups

**System packages installed:**
- Python development tools
- I2C tools
- libcamera and picamera2
- OpenCV dependencies
- Build tools
- Image/video libraries

---

### `install_dependencies.sh`
**Purpose:** Install Python dependencies in virtual environment

**Runs on:** Raspberry Pi (called by deploy.sh)

**What it does:**
1. Creates Python virtual environment
2. Upgrades pip
3. Installs all requirements
4. Installs Raspberry Pi specific packages
5. Verifies installations

**Python packages installed:**
- NumPy, SciPy
- OpenCV
- Flask, Flask-CORS, Flask-SocketIO
- Picamera2
- RPi.GPIO
- Adafruit libraries
- And more (see requirements.txt)

---

### `setup_systemd.sh`
**Purpose:** Configure camera platform as systemd service

**Runs on:** Raspberry Pi (called by deploy.sh)

**What it does:**
1. Creates systemd service file
2. Configures auto-start on boot
3. Sets up automatic restart on failure
4. Configures logging

**Service configuration:**
- Service name: `camera-platform`
- Auto-start: Yes
- Auto-restart: Yes (10s delay)
- Logging: journald

---

### `update.sh`
**Purpose:** Quick update of code without full reinstall

**Usage:**
```bash
./update.sh <hostname> [username]
```

**Example:**
```bash
./update.sh raspberrypi.local pi
```

**What it does:**
1. Syncs source code
2. Syncs configuration files
3. Restarts service

**Use when:**
- You've made code changes
- You've updated configuration
- You want to deploy quickly

**Does NOT:**
- Reinstall system packages
- Recreate virtual environment
- Reinstall Python packages

---

### `backup.sh`
**Purpose:** Backup configuration and data from Raspberry Pi

**Usage:**
```bash
./backup.sh <hostname> [username]
```

**Example:**
```bash
./backup.sh raspberrypi.local pi
```

**What it backs up:**
- Configuration files
- Captured images and videos
- System logs
- Calibration data

**Backup location:**
```
./backups/YYYYMMDD_HHMMSS/
├── config/
├── data/
├── logs/
└── backup_info.txt
```

---

## Common Workflows

### Initial Deployment

```bash
# 1. Setup SSH key (one-time)
./setup_ssh_key.sh raspberrypi.local pi

# 2. Deploy system
./deploy.sh raspberrypi.local pi

# 3. Reboot Pi
ssh pi@raspberrypi.local 'sudo reboot'

# 4. Check status (after reboot)
ssh pi@raspberrypi.local 'sudo systemctl status camera-platform'

# 5. Access web interface
open http://raspberrypi.local:5000
```

### Update Code

```bash
# Quick update after code changes
./update.sh raspberrypi.local pi

# Check logs
ssh pi@raspberrypi.local 'journalctl -u camera-platform -f'
```

### Backup Data

```bash
# Create backup before major changes
./backup.sh raspberrypi.local pi

# Backups stored in ./backups/
ls -lh backups/
```

### Troubleshooting

```bash
# Check service status
ssh pi@raspberrypi.local 'sudo systemctl status camera-platform'

# View logs
ssh pi@raspberrypi.local 'journalctl -u camera-platform -n 100'

# Restart service
ssh pi@raspberrypi.local 'sudo systemctl restart camera-platform'

# Stop service
ssh pi@raspberrypi.local 'sudo systemctl stop camera-platform'

# Start service
ssh pi@raspberrypi.local 'sudo systemctl start camera-platform'
```

---

## Manual Service Management

### On Raspberry Pi

```bash
# Check status
sudo systemctl status camera-platform

# Start service
sudo systemctl start camera-platform

# Stop service
sudo systemctl stop camera-platform

# Restart service
sudo systemctl restart camera-platform

# View logs (live)
journalctl -u camera-platform -f

# View last 100 log lines
journalctl -u camera-platform -n 100

# Disable auto-start
sudo systemctl disable camera-platform

# Enable auto-start
sudo systemctl enable camera-platform
```

---

## Network Configuration

### Finding Your Raspberry Pi

```bash
# By hostname (if mDNS works)
ping raspberrypi.local

# Scan network for Raspberry Pi
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry Pi"

# Or use Raspberry Pi Imager to set hostname before first boot
```

### Setting Static IP (Optional)

On Raspberry Pi, edit `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart networking:
```bash
sudo systemctl restart dhcpcd
```

---

## Firewall Configuration

If you have a firewall enabled, open port 5000:

```bash
# On Raspberry Pi
sudo ufw allow 5000/tcp
sudo ufw reload
```

---

## Environment Variables

You can set environment variables in the systemd service file:

Edit `/etc/systemd/system/camera-platform.service`:

```ini
[Service]
Environment="FLASK_ENV=production"
Environment="LOG_LEVEL=INFO"
Environment="CAMERA_RESOLUTION=1920x1080"
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart camera-platform
```

---

## Troubleshooting

### SSH Connection Issues

**Problem:** Cannot connect via SSH

**Solutions:**
1. Check Pi is powered on and connected to network
2. Verify SSH is enabled: `sudo systemctl status ssh`
3. Check firewall: `sudo ufw status`
4. Try IP address instead of hostname
5. Check SSH service: `sudo systemctl restart ssh`

### Deployment Fails

**Problem:** deploy.sh fails during execution

**Solutions:**
1. Check SSH connection: `ssh pi@raspberrypi.local`
2. Verify disk space: `df -h`
3. Check permissions: `ls -la /home/pi/`
4. Review error messages in script output
5. Try manual steps from failed stage

### Service Won't Start

**Problem:** camera-platform service fails to start

**Solutions:**
1. Check logs: `journalctl -u camera-platform -n 100`
2. Verify Python environment: `source venv/bin/activate && python --version`
3. Test manually: `cd /home/pi/camera_platform && source venv/bin/activate && python src/web_server.py`
4. Check file permissions: `ls -la /home/pi/camera_platform/`
5. Verify dependencies: `pip list`

### I2C Not Working

**Problem:** Cannot detect I2C devices

**Solutions:**
1. Enable I2C: `sudo raspi-config nonint do_i2c 0`
2. Check I2C is loaded: `lsmod | grep i2c`
3. Test detection: `sudo i2cdetect -y 1`
4. Check user groups: `groups $USER` (should include i2c)
5. Reboot: `sudo reboot`

### Camera Not Detected

**Problem:** Camera not found

**Solutions:**
1. Enable camera: `sudo raspi-config nonint do_camera 0`
2. Check connection: `libcamera-hello --list-cameras`
3. Verify CSI cable connection
4. Check GPU memory: `vcgencmd get_mem gpu` (should be 256MB)
5. Reboot: `sudo reboot`

---

## Advanced Configuration

### Custom Service Configuration

Create `/home/pi/camera_platform/config/service.conf`:

```ini
[service]
port = 5000
host = 0.0.0.0
debug = false
log_level = INFO

[platform]
home_on_start = true
calibration_file = config/platform_geometry.yaml

[camera]
default_resolution = 1920x1080
auto_focus = true

[ai]
model_path = models/yolov5s.hef
confidence_threshold = 0.5
```

### Multiple Instances

To run multiple camera platforms:

1. Copy service file:
```bash
sudo cp /etc/systemd/system/camera-platform.service \
       /etc/systemd/system/camera-platform-2.service
```

2. Edit new service file to use different port and directory

3. Enable and start:
```bash
sudo systemctl enable camera-platform-2
sudo systemctl start camera-platform-2
```

---

## Security Considerations

### SSH Security

1. Use SSH keys instead of passwords
2. Disable password authentication:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```

3. Change default password:
   ```bash
   passwd
   ```

### Firewall

Enable and configure firewall:
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5000/tcp
sudo ufw status
```

### Updates

Keep system updated:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

---

## Performance Optimization

### Increase Swap (for compilation)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Overclock (Optional)

Edit `/boot/config.txt`:
```
over_voltage=6
arm_freq=2000
gpu_freq=750
```

**Warning:** May void warranty and reduce lifespan

---

## Monitoring

### System Resources

```bash
# CPU temperature
vcgencmd measure_temp

# CPU usage
htop

# Memory usage
free -h

# Disk usage
df -h

# Network usage
iftop
```

### Service Monitoring

```bash
# Service status
systemctl status camera-platform

# Resource usage
systemd-cgtop

# Failed services
systemctl --failed
```

---

## Uninstall

To completely remove the camera platform:

```bash
# Stop and disable service
sudo systemctl stop camera-platform
sudo systemctl disable camera-platform

# Remove service file
sudo rm /etc/systemd/system/camera-platform.service
sudo systemctl daemon-reload

# Remove project directory
rm -rf /home/pi/camera_platform

# Remove dependencies (optional)
sudo apt autoremove -y
```

---

## Support

For issues or questions:
1. Check logs: `journalctl -u camera-platform -f`
2. Review documentation in main README.md
3. Check GitHub issues
4. Consult troubleshooting section above

---

**Last Updated:** 2024  
**Version:** 1.0