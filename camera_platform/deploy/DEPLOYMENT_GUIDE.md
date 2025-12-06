# Complete Deployment Guide - Raspberry Pi Camera Platform

This guide walks you through deploying the camera platform to your Raspberry Pi, from initial setup to running system.

---

## 📋 Prerequisites Checklist

### Hardware
- [ ] Raspberry Pi 5 (8GB) with power supply
- [ ] MicroSD card (64GB+ recommended) with Raspberry Pi OS
- [ ] Network connection (Ethernet or WiFi)
- [ ] All camera platform hardware assembled
- [ ] Computer for deployment (Mac, Linux, or Windows with WSL)

### Software on Your Computer
- [ ] SSH client installed
- [ ] rsync installed (usually pre-installed on Mac/Linux)
- [ ] Git installed
- [ ] Terminal/command line access

### Raspberry Pi Setup
- [ ] Raspberry Pi OS (64-bit) installed and booted
- [ ] SSH enabled
- [ ] Network configured (can ping from your computer)
- [ ] Default user created (usually `pi` or `ubuntu`)

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Raspberry Pi (First Time Only)

#### 1.1 Enable SSH on Raspberry Pi

**Option A: Using Raspberry Pi Imager (Recommended)**
1. Download Raspberry Pi Imager
2. Select "Raspberry Pi OS (64-bit)"
3. Click gear icon for advanced options
4. Enable SSH
5. Set username and password
6. Configure WiFi (optional)
7. Write to SD card

**Option B: Enable SSH After Boot**
```bash
# On Raspberry Pi
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### 1.2 Find Raspberry Pi IP Address

**On Raspberry Pi:**
```bash
hostname -I
```

**From Your Computer:**
```bash
# Scan network (replace with your network range)
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry Pi"

# Or try hostname
ping raspberrypi.local
```

#### 1.3 Test SSH Connection

```bash
# Replace with your Pi's IP or hostname
ssh pi@raspberrypi.local

# Or use IP address
ssh pi@192.168.1.100
```

**Default credentials:**
- Username: `pi`
- Password: `raspberry` (change this immediately!)

---

### Step 2: Clone Repository on Your Computer

```bash
# Clone the repository
git clone https://github.com/chadsteeleco-prog/SuspensionApp.git
cd SuspensionApp

# Checkout camera platform branch
git checkout camera-platform-design

# Navigate to deployment directory
cd camera_platform/deploy
```

---

### Step 3: Setup SSH Key Authentication (Recommended)

This allows passwordless deployment and is much more convenient.

```bash
# Make scripts executable
chmod +x *.sh

# Setup SSH key
./setup_ssh_key.sh raspberrypi.local pi

# Follow prompts and enter Pi password when asked
```

**What this does:**
- Generates SSH key pair (if not exists)
- Copies public key to Raspberry Pi
- Tests connection

**After this step, you won't need to enter password for deployment!**

---

### Step 4: Deploy Camera Platform

```bash
# Full deployment (takes 15-20 minutes)
./deploy.sh raspberrypi.local pi
```

**What happens during deployment:**

1. **Tests SSH connection** - Verifies connectivity
2. **Creates remote directory** - `/home/pi/camera_platform`
3. **Syncs project files** - Copies all code and config
4. **Runs setup script** - Configures Raspberry Pi
   - Updates system packages
   - Enables I2C and Camera
   - Installs system dependencies
   - Configures GPU memory
5. **Installs Python dependencies** - Sets up virtual environment
   - Creates venv
   - Installs all Python packages
   - Verifies installations
6. **Configures systemd service** - Sets up auto-start
   - Creates service file
   - Enables auto-start on boot
7. **Verifies installation** - Tests configuration

**Progress indicators:**
```
[1/8] Testing SSH connection...
✓ SSH connection successful

[2/8] Creating remote directory...
✓ Directory created

[3/8] Syncing project files...
✓ Files synced

[4/8] Copying deployment scripts...
✓ Scripts copied

[5/8] Running setup script on Pi...
✓ Setup complete

[6/8] Installing dependencies...
✓ Dependencies installed

[7/8] Setting up systemd service...
✓ Systemd service configured

[8/8] Testing configuration...
✓ Configuration verified
```

---

### Step 5: Install Hailo AI Runtime (Optional)

If you have the AI HAT+ with Hailo-8:

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Navigate to project
cd camera_platform/deploy

# Run Hailo installation
chmod +x install_hailo.sh
./install_hailo.sh
```

**Note:** You'll need to download the Hailo runtime package from:
https://hailo.ai/developer-zone/software-downloads/

Place it in `~/Downloads/` before running the script.

---

### Step 6: Reboot Raspberry Pi

```bash
# From your computer
ssh pi@raspberrypi.local 'sudo reboot'

# Or on the Pi directly
sudo reboot
```

**Wait 1-2 minutes for reboot to complete.**

---

### Step 7: Verify Installation

#### 7.1 Check Service Status

```bash
ssh pi@raspberrypi.local 'sudo systemctl status camera-platform'
```

**Expected output:**
```
● camera-platform.service - Camera Platform with Stewart Platform Control
   Loaded: loaded (/etc/systemd/system/camera-platform.service; enabled)
   Active: active (running) since ...
```

#### 7.2 View Logs

```bash
# Live logs
ssh pi@raspberrypi.local 'journalctl -u camera-platform -f'

# Last 50 lines
ssh pi@raspberrypi.local 'journalctl -u camera-platform -n 50'
```

#### 7.3 Test Web Interface

Open browser and navigate to:
```
http://raspberrypi.local:5000
```

Or use IP address:
```
http://192.168.1.100:5000
```

**You should see the camera platform control panel!**

---

### Step 8: Hardware Verification

#### 8.1 Check I2C Devices

```bash
ssh pi@raspberrypi.local 'sudo i2cdetect -y 1'
```

**Expected output:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --  ← PWM HAT
50: -- -- -- 53 -- -- -- -- -- -- -- -- -- -- -- --  ← G-Force Sensor
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

#### 8.2 Check Camera

```bash
ssh pi@raspberrypi.local 'libcamera-hello --list-cameras'
```

**Expected output:**
```
Available cameras
-----------------
0 : imx708 [4608x2592] (/base/soc/i2c0mux/i2c@1/imx708@1a)
    Modes: ...
```

#### 8.3 Check Hailo Device (if installed)

```bash
ssh pi@raspberrypi.local 'hailortcli fw-control identify'
```

**Expected output:**
```
Hailo-8 device found
Device ID: ...
Firmware version: ...
```

---

## 🔄 Updating the System

### Quick Code Update

When you make changes to the code:

```bash
cd camera_platform/deploy
./update.sh raspberrypi.local pi
```

**This will:**
1. Sync source files
2. Sync configuration
3. Restart service

**Much faster than full deployment!**

### Full Redeployment

If you need to reinstall everything:

```bash
./deploy.sh raspberrypi.local pi
```

---

## 💾 Backing Up Data

### Create Backup

```bash
cd camera_platform/deploy
./backup.sh raspberrypi.local pi
```

**Backs up:**
- Configuration files
- Captured images and videos
- System logs
- Calibration data

**Backup location:**
```
./backups/YYYYMMDD_HHMMSS/
```

### Restore from Backup

```bash
# Copy backup to Pi
rsync -avz backups/20240101_120000/ pi@raspberrypi.local:/home/pi/camera_platform/

# Restart service
ssh pi@raspberrypi.local 'sudo systemctl restart camera-platform'
```

---

## 🔧 Common Operations

### Start/Stop Service

```bash
# Stop service
ssh pi@raspberrypi.local 'sudo systemctl stop camera-platform'

# Start service
ssh pi@raspberrypi.local 'sudo systemctl start camera-platform'

# Restart service
ssh pi@raspberrypi.local 'sudo systemctl restart camera-platform'

# Check status
ssh pi@raspberrypi.local 'sudo systemctl status camera-platform'
```

### View Logs

```bash
# Live logs (follow)
ssh pi@raspberrypi.local 'journalctl -u camera-platform -f'

# Last 100 lines
ssh pi@raspberrypi.local 'journalctl -u camera-platform -n 100'

# Logs since boot
ssh pi@raspberrypi.local 'journalctl -u camera-platform -b'

# Logs with errors only
ssh pi@raspberrypi.local 'journalctl -u camera-platform -p err'
```

### Manual Testing

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Navigate to project
cd camera_platform

# Activate virtual environment
source venv/bin/activate

# Run manually
python src/web_server.py
```

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
ssh pi@raspberrypi.local 'journalctl -u camera-platform -n 100'
```

**Common issues:**
1. **Import errors** - Missing dependencies
   ```bash
   ssh pi@raspberrypi.local 'cd camera_platform && source venv/bin/activate && pip install -r requirements.txt'
   ```

2. **Permission errors** - Wrong file ownership
   ```bash
   ssh pi@raspberrypi.local 'sudo chown -R pi:pi /home/pi/camera_platform'
   ```

3. **Port already in use** - Another service using port 5000
   ```bash
   ssh pi@raspberrypi.local 'sudo lsof -i :5000'
   ```

### Cannot Connect to Web Interface

**Check service is running:**
```bash
ssh pi@raspberrypi.local 'sudo systemctl status camera-platform'
```

**Check firewall:**
```bash
ssh pi@raspberrypi.local 'sudo ufw status'
```

**Test from Pi itself:**
```bash
ssh pi@raspberrypi.local 'curl http://localhost:5000'
```

### I2C Devices Not Detected

**Enable I2C:**
```bash
ssh pi@raspberrypi.local 'sudo raspi-config nonint do_i2c 0'
ssh pi@raspberrypi.local 'sudo reboot'
```

**Check I2C is loaded:**
```bash
ssh pi@raspberrypi.local 'lsmod | grep i2c'
```

**Check user permissions:**
```bash
ssh pi@raspberrypi.local 'groups'
# Should include: i2c, gpio, video
```

### Camera Not Working

**Enable camera:**
```bash
ssh pi@raspberrypi.local 'sudo raspi-config nonint do_camera 0'
ssh pi@raspberrypi.local 'sudo reboot'
```

**Check GPU memory:**
```bash
ssh pi@raspberrypi.local 'vcgencmd get_mem gpu'
# Should be: gpu=256M
```

**Test camera:**
```bash
ssh pi@raspberrypi.local 'libcamera-hello --list-cameras'
```

---

## 📊 Monitoring

### System Resources

```bash
# CPU temperature
ssh pi@raspberrypi.local 'vcgencmd measure_temp'

# CPU usage
ssh pi@raspberrypi.local 'top -bn1 | head -20'

# Memory usage
ssh pi@raspberrypi.local 'free -h'

# Disk usage
ssh pi@raspberrypi.local 'df -h'
```

### Service Health

```bash
# Service uptime
ssh pi@raspberrypi.local 'systemctl show camera-platform -p ActiveEnterTimestamp'

# Service restarts
ssh pi@raspberrypi.local 'systemctl show camera-platform -p NRestarts'

# Memory usage
ssh pi@raspberrypi.local 'systemctl status camera-platform | grep Memory'
```

---

## 🔐 Security Best Practices

### Change Default Password

```bash
ssh pi@raspberrypi.local
passwd
# Enter new password
```

### Disable Password Authentication

After setting up SSH keys:

```bash
ssh pi@raspberrypi.local
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### Enable Firewall

```bash
ssh pi@raspberrypi.local
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5000/tcp
sudo ufw status
```

### Keep System Updated

```bash
ssh pi@raspberrypi.local 'sudo apt update && sudo apt upgrade -y'
```

---

## 🎯 Next Steps

After successful deployment:

1. **Calibrate Hardware**
   - Follow calibration procedures in documentation
   - Calibrate servos
   - Calibrate platform geometry
   - Calibrate camera focus

2. **Test Features**
   - Test basic motion control
   - Test camera capture
   - Test AI detection (if installed)
   - Test web interface

3. **Configure for Your Use Case**
   - Adjust motion limits
   - Configure camera settings
   - Set up motion presets
   - Configure AI models

4. **Integration**
   - Integrate with suspension testing app
   - Set up data synchronization
   - Configure automated workflows

---

## 📚 Additional Resources

- **Main Documentation:** `../README.md`
- **Architecture Guide:** `../../CAMERA_PLATFORM_ARCHITECTURE.md`
- **Hardware Guide:** `../../HARDWARE_INTEGRATION_GUIDE.md`
- **Quick Start:** `../../QUICK_START_GUIDE.md`
- **Deployment Scripts:** `./README.md`

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `journalctl -u camera-platform -f`
2. Review troubleshooting section above
3. Check GitHub issues
4. Review documentation

---

**Deployment Guide Version:** 1.0  
**Last Updated:** 2024  
**Tested On:** Raspberry Pi 5 with Raspberry Pi OS (64-bit)