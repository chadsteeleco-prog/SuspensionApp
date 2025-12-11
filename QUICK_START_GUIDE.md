# Quick Start Guide - Camera Platform

**Welcome!** This guide will help you get your camera platform up and running quickly once your hardware arrives.

---

## 📦 What You Have

- ✅ Raspberry Pi 5 (8GB RAM) with Active Cooler
- ✅ Arducam OwlSight 64MP Camera
- ✅ GeeekPi AI HAT+ with Hailo-8 (26 TOPS)
- ✅ PWM Servo Driver HAT (16-channel)
- ✅ Stewart Platform with 6× 80KG servos

---

## 🚀 Quick Setup (30 Minutes)

### Step 1: Hardware Assembly (10 minutes)

```
Stack Order (bottom to top):
1. Raspberry Pi 5 (with active cooler installed)
2. AI HAT+ (connect via PCIe)
3. PWM Servo HAT (connect via GPIO)
4. Camera (connect via CSI cable)
```

**Important:**
- Ensure active cooler fan is connected to GPIO pins
- CSI cable contacts face toward HDMI ports
- All standoffs secure between layers

### Step 2: Power Setup (5 minutes)

**You Need:**
- 5V 5A USB-C power supply (for Raspberry Pi)
- 6V 20A power supply (for servos)

**Connections:**
```
5V Supply → Raspberry Pi 5 USB-C port
6V Supply → PWM HAT terminal block (V+ and GND)
```

**⚠️ CRITICAL:** Do NOT power servos from Raspberry Pi!

### Step 3: Servo Connections (10 minutes)

Connect 6 servos to PWM HAT:
```
Channel 0 → Servo 1 (Base, 0°)
Channel 1 → Servo 2 (Base, 60°)
Channel 2 → Servo 3 (Base, 120°)
Channel 3 → Servo 4 (Base, 180°)
Channel 4 → Servo 5 (Base, 240°)
Channel 5 → Servo 6 (Base, 300°)
```

Each servo has 3 wires:
- Signal (yellow/white) → PWM channel
- Power (red) → V+
- Ground (black/brown) → GND

### Step 4: First Boot (5 minutes)

1. Insert microSD card with Raspberry Pi OS
2. Connect monitor, keyboard, mouse (optional)
3. Turn ON 6V servo power
4. Turn ON 5V Raspberry Pi power
5. Wait for boot (green LED activity)

---

## 💻 Software Setup (20 Minutes)

### Quick Install Script

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Download and run setup script
cd ~
git clone https://github.com/chadsteeleco-prog/SuspensionApp.git
cd SuspensionApp/camera_platform

# Run automated setup
chmod +x setup.sh
./setup.sh
```

### Manual Setup (if needed)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv i2c-tools libcamera-apps

# Enable interfaces
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → Camera → Enable
# → Reboot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

---

## ✅ Verification Tests (10 Minutes)

### Test 1: I2C Communication
```bash
sudo i2cdetect -y 1
```
**Expected:** Device at address `0x40` (PWM HAT)

### Test 2: Camera
```bash
libcamera-hello --list-cameras
```
**Expected:** Camera detected with 64MP sensor info

### Test 3: Hailo AI
```bash
hailortcli fw-control identify
```
**Expected:** Hailo-8 device information

### Test 4: Servo Movement
```bash
cd ~/SuspensionApp/camera_platform
source venv/bin/activate
python tests/test_servos.py
```
**Expected:** Each servo moves through test sequence

---

## 🎯 First Motion Test (5 Minutes)

```bash
cd ~/SuspensionApp/camera_platform
source venv/bin/activate
python src/stewart_platform.py
```

This will:
1. Initialize the platform
2. Move to home position
3. Test each axis (X, Y, Z, Roll, Pitch, Yaw)
4. Return to home

**Watch for:**
- Smooth servo movements
- No binding or unusual sounds
- Platform returns to level position

---

## 🌐 Start Web Interface

```bash
cd ~/SuspensionApp/camera_platform
source venv/bin/activate
python src/web_server.py
```

**Access at:** `http://raspberrypi.local:5000`

**Features:**
- Real-time platform control
- Camera preview and capture
- Motion presets
- AI tracking controls

---

## 📸 First Photo

### Via Python:
```python
from camera_control import CameraController

camera = CameraController()
camera.capture_image("first_photo.jpg", resolution=(1920, 1080))
print("Photo saved!")
```

### Via Web Interface:
1. Open `http://raspberrypi.local:5000`
2. Click "Camera" tab
3. Click "Capture Image"
4. View in "Gallery"

---

## 🎬 First Motion Sequence

### Via Python:
```python
from stewart_platform import StewartPlatform
import time

platform = StewartPlatform()

# Pan left to right
for yaw in range(-20, 21, 5):
    platform.move_to(0, 0, 0, 0, 0, yaw, duration=1.0)
    time.sleep(1.5)

platform.home()
```

### Via Web Interface:
1. Open control panel
2. Select "Presets" → "Pan Sequence"
3. Click "Execute"

---

## 🤖 First AI Detection

```python
from ai_processor import ObjectDetector
from camera_control import CameraController
import cv2

# Initialize
detector = ObjectDetector("~/hailo_models/yolov5s.hef")
camera = CameraController()

# Capture and detect
frame = camera.capture_array()
annotated, detections = detector.detect_and_draw(frame)

# Save result
cv2.imwrite("detection_result.jpg", annotated)

print(f"Detected {len(detections)} objects:")
for det in detections:
    print(f"  - {det.class_name}: {det.confidence:.2f}")
```

---

## 🔧 Calibration (Required Before Use)

### 1. Servo Calibration (10 minutes)
```bash
python src/calibration/servo_calibration.py
```
Follow prompts to find neutral positions.

### 2. Platform Geometry (15 minutes)
```bash
python src/calibration/platform_calibration.py
```
Measure and input your platform dimensions.

### 3. Camera Focus (5 minutes)
```bash
python src/calibration/camera_calibration.py
```
Test focus positions and save optimal settings.

---

## 📋 Pre-Flight Checklist

Before each use:
- [ ] All power supplies connected and ON
- [ ] All servos responding (test with web interface)
- [ ] Camera preview working
- [ ] Emergency stop button accessible
- [ ] Platform has clear range of motion
- [ ] No loose wires or obstructions

---

## 🆘 Troubleshooting

### Servos Not Moving
1. Check 6V power supply is ON
2. Verify I2C connection: `sudo i2cdetect -y 1`
3. Check servo wiring (signal, power, ground)
4. Test individual servo: `python tests/test_single_servo.py 0`

### Camera Not Detected
1. Check CSI cable connection (contacts toward HDMI)
2. Enable camera: `sudo raspi-config`
3. Reboot: `sudo reboot`
4. Test: `libcamera-hello`

### Platform Moves Erratically
1. Recalibrate servos
2. Check for mechanical binding
3. Verify platform geometry configuration
4. Reduce motion speed in settings

### AI Not Working
1. Verify Hailo device: `hailortcli fw-control identify`
2. Check model file exists: `ls ~/hailo_models/`
3. Reinstall Hailo runtime
4. Check PCIe connection

---

## 📚 Next Steps

1. **Complete Calibration** - Essential for accurate motion
2. **Test All Features** - Camera, motion, AI tracking
3. **Create Presets** - Save your favorite positions
4. **Explore Applications** - Time-lapse, 360°, tracking
5. **Read Full Documentation** - See CAMERA_PLATFORM_ARCHITECTURE.md

---

## 🎓 Learning Resources

### Example Projects
- **Product Photography:** 360° rotation with auto-capture
- **Time-Lapse:** Smooth motion over time
- **Object Tracking:** Auto-follow moving subjects
- **Multi-Angle Capture:** Automated angle sequences

### Code Examples
See `camera_platform/examples/` directory:
- `360_rotation.py` - Product photography
- `motion_timelapse.py` - Moving time-lapse
- `auto_tracking.py` - AI-powered tracking
- `panorama.py` - Multi-shot panorama

---

## 💡 Tips & Tricks

1. **Start Slow:** Use longer durations (2-3s) for initial testing
2. **Home Often:** Return to home position between tests
3. **Save Presets:** Save positions you use frequently
4. **Monitor Temperature:** Check servo temperatures during extended use
5. **Backup Config:** Save calibration data regularly

---

## 🔗 Useful Links

- **Full Documentation:** [CAMERA_PLATFORM_ARCHITECTURE.md](CAMERA_PLATFORM_ARCHITECTURE.md)
- **Hardware Guide:** [HARDWARE_INTEGRATION_GUIDE.md](HARDWARE_INTEGRATION_GUIDE.md)
- **Implementation Plan:** [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- **GitHub Repo:** https://github.com/chadsteeleco-prog/SuspensionApp

---

## 🎉 You're Ready!

Your camera platform is now set up and ready to use. Start with simple movements and gradually explore more advanced features.

**Have fun creating amazing shots!**

---

**Questions?** Check the troubleshooting section or review the full documentation.

**Document Version:** 1.0  
**Last Updated:** 2024