# Hardware Integration Guide - Camera Platform

## Table of Contents
1. [Hardware Assembly](#hardware-assembly)
2. [Wiring Diagrams](#wiring-diagrams)
3. [Power System Setup](#power-system-setup)
4. [Software Installation](#software-installation)
5. [Calibration Procedures](#calibration-procedures)
6. [Testing & Validation](#testing--validation)

---

## 1. Hardware Assembly

### 1.1 Component Stacking Order (Bottom to Top)

```
┌─────────────────────────────────────┐
│  Camera (OwlSight 64MP)             │  ← Top
│  Mounted on Stewart Platform        │
└─────────────────────────────────────┘
              ↓ CSI Cable
┌─────────────────────────────────────┐
│  Raspberry Pi 5 (8GB)               │
│  with Active Cooler                 │
└─────────────────────────────────────┘
              ↓ PCIe
┌─────────────────────────────────────┐
│  GeeekPi AI HAT+ (Hailo-8)          │
│  with Metal Case & Active Cooler    │
└─────────────────────────────────────┘
              ↓ GPIO Passthrough
┌─────────────────────────────────────┐
│  PWM Servo Driver HAT               │  ← Bottom
│  (PCA9685 16-Channel)               │
└─────────────────────────────────────┘
```

### 1.2 Assembly Steps

#### Step 1: Prepare Raspberry Pi 5
1. **Install Active Cooler:**
   - Remove protective film from thermal pad
   - Align cooler with mounting holes
   - Secure with provided screws
   - Connect fan to 5V and GND pins

2. **Insert microSD Card:**
   - Use 64GB+ Class 10 or better
   - Pre-load with Raspberry Pi OS (64-bit)

#### Step 2: Install AI HAT+
1. **Prepare PCIe Connection:**
   - Locate PCIe slot on Raspberry Pi 5
   - Remove protective cover from AI HAT+ connector

2. **Mount AI HAT+:**
   - Align PCIe connector carefully
   - Press firmly but gently until seated
   - Secure with standoffs (included)
   - Connect active cooler fan

3. **Verify GPIO Passthrough:**
   - Ensure 40-pin header extends through HAT
   - Check alignment before proceeding

#### Step 3: Install PWM Servo HAT
1. **Stack on AI HAT+:**
   - Align 40-pin header with GPIO passthrough
   - Press down firmly until fully seated
   - Verify all pins are connected

2. **Secure with Standoffs:**
   - Use M2.5 standoffs between layers
   - Ensure stable mechanical connection

#### Step 4: Connect Camera
1. **CSI Cable Connection:**
   - Locate CSI connector on Raspberry Pi 5 (labeled "CAMERA")
   - Lift connector latch gently
   - Insert cable with contacts facing toward HDMI ports
   - Press latch down to secure

2. **Camera Mounting:**
   - Mount camera on Stewart platform top plate
   - Ensure cable has slack for platform movement
   - Use cable management to prevent snagging

#### Step 5: Stewart Platform Connection
1. **Servo Wiring:**
   - Connect 6 servos to PWM channels 0-5
   - Wire order: Signal (yellow/white), Power (red), Ground (black/brown)
   - Label each servo (1-6) for identification

2. **Servo Power:**
   - Connect external 6V power supply to servo HAT terminal
   - **DO NOT power servos from Raspberry Pi**
   - Verify polarity: Red (+), Black (-)

---

## 2. Wiring Diagrams

### 2.1 Complete System Wiring

```
                    ┌─────────────────────────────────┐
                    │   Raspberry Pi 5 (40-pin GPIO)  │
                    └─────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ↓                     ↓                     ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  AI HAT+     │    │  PWM Servo   │    │  Camera      │
│  (PCIe)      │    │  HAT (I2C)   │    │  (CSI)       │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                    ↓               ↓
            ┌──────────────┐  ┌──────────────┐
            │  Servos 0-5  │  │  Servos 14-15│
            │  (Stewart)   │  │  (Camera)    │
            └──────────────┘  └──────────────┘
```

### 2.2 Detailed Pin Connections

#### Raspberry Pi 5 GPIO Header (40-pin)
```
     3.3V  (1) (2)  5V      ← Power for HATs
  GPIO  2  (3) (4)  5V      ← I2C SDA (PWM HAT)
  GPIO  3  (5) (6)  GND     ← I2C SCL (PWM HAT)
  GPIO  4  (7) (8)  GPIO 14
      GND  (9) (10) GPIO 15
GPIO 17 (11) (12) GPIO 18   ← Shutter Trigger
GPIO 27 (13) (14) GND       ← Status LED
GPIO 22 (15) (16) GPIO 23   ← E-Stop Input
     3.3V (17) (18) GPIO 24 ← Limit Switch 1
GPIO 10 (19) (20) GND       ← Limit Switch 2
 GPIO 9 (21) (22) GPIO 25
GPIO 11 (23) (24) GPIO 8
     GND (25) (26) GPIO 7
 GPIO 0 (27) (28) GPIO 1
 GPIO 5 (29) (30) GND
 GPIO 6 (31) (32) GPIO 12
GPIO 13 (33) (34) GND
GPIO 19 (35) (36) GPIO 16
GPIO 26 (37) (38) GPIO 20
     GND (39) (40) GPIO 21
```

#### PWM Servo HAT Connections
```
Terminal Block:
┌─────────────────────────────────┐
│  V+  (6V Servo Power - External)│
│  GND (Common Ground)            │
└─────────────────────────────────┘

Servo Channels (3-pin headers):
Channel  0: Stewart Servo 1 (Base 0°)
Channel  1: Stewart Servo 2 (Base 60°)
Channel  2: Stewart Servo 3 (Base 120°)
Channel  3: Stewart Servo 4 (Base 180°)
Channel  4: Stewart Servo 5 (Base 240°)
Channel  5: Stewart Servo 6 (Base 300°)
Channel  6-13: Reserved
Channel 14: Camera Focus (optional)
Channel 15: Camera Zoom

Each channel: [Signal | V+ | GND]
```

#### Camera Shutter Trigger Circuit
```
GPIO 17 ──┬──[1kΩ]──┬── Shutter Signal
          │         │
          │      [LED]── Indicator
          │         │
          └─────────┴── GND
```

### 2.3 Emergency Stop Circuit

```
                    ┌─── 3.3V (Pin 17)
                    │
                  [10kΩ] Pull-up
                    │
GPIO 22 ────────────┼──── E-Stop Switch ──── GND
                    │
                 [0.1µF] Debounce capacitor
                    │
                   GND
```

---

## 3. Power System Setup

### 3.1 Power Requirements Summary

| Component | Voltage | Current | Power | Notes |
|-----------|---------|---------|-------|-------|
| Raspberry Pi 5 | 5V | 5A | 25W | USB-C PD |
| AI HAT+ | 5V | 2A | 10W | Via GPIO |
| PWM HAT (Logic) | 5V | 0.5A | 2.5W | Via GPIO |
| Servos (6×) | 6V | 15A peak | 90W | External supply |
| Camera | 5V | 0.5A | 2.5W | Via CSI |
| **Total** | - | - | **130W** | Peak load |

### 3.2 Power Supply Options

#### Option 1: Dual Power Supply (Recommended)
```
┌──────────────────────────────────────────┐
│  5V 10A Power Supply (50W)               │
│  - Raspberry Pi 5: 5V 5A (USB-C PD)      │
│  - AI HAT+: Via GPIO                     │
│  - PWM HAT: Via GPIO                     │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  6V 20A Power Supply (120W)              │
│  - Servo System: 6V 15A peak             │
│  - Connected to PWM HAT terminal block   │
└──────────────────────────────────────────┘
```

**Wiring:**
```
5V Supply (+) ──→ Raspberry Pi 5 USB-C
5V Supply (-) ──→ Common Ground

6V Supply (+) ──→ PWM HAT V+ Terminal
6V Supply (-) ──→ PWM HAT GND Terminal
                  └──→ Common Ground
```

#### Option 2: Single High-Power Supply
```
┌──────────────────────────────────────────┐
│  12V 15A Power Supply (180W)             │
│  ↓                                       │
│  ├─→ 5V 10A Buck Converter → RPi5       │
│  └─→ 6V 20A Buck Converter → Servos     │
└──────────────────────────────────────────┘
```

### 3.3 Power Distribution Board (Recommended)

```
┌─────────────────────────────────────────────┐
│         Power Distribution Board            │
├─────────────────────────────────────────────┤
│                                             │
│  Input: 12V 15A                             │
│    ↓                                        │
│  ┌──────────────┐      ┌──────────────┐    │
│  │ 5V Buck      │      │ 6V Buck      │    │
│  │ 10A          │      │ 20A          │    │
│  └──────────────┘      └──────────────┘    │
│         ↓                      ↓            │
│    ┌─────────┐          ┌──────────┐       │
│    │ RPi5    │          │ Servos   │       │
│    │ USB-C   │          │ Terminal │       │
│    └─────────┘          └──────────┘       │
│                                             │
│  Common Ground Bus ═════════════════════    │
│                                             │
│  Fuses: 5V@10A, 6V@20A                      │
│  LED Indicators: Power, Fault               │
└─────────────────────────────────────────────┘
```

### 3.4 Power-On Sequence

**Correct Startup Order:**
1. Connect all power supplies (OFF)
2. Verify all connections
3. Turn ON 6V servo supply
4. Wait 2 seconds
5. Turn ON 5V Raspberry Pi supply
6. System boots automatically

**Shutdown Order:**
1. Software shutdown: `sudo shutdown -h now`
2. Wait for RPi5 to power down (green LED off)
3. Turn OFF 5V supply
4. Turn OFF 6V servo supply

### 3.5 Power Safety Features

**Overcurrent Protection:**
- Use fuses on all power rails
- 5V rail: 10A fast-blow fuse
- 6V rail: 20A fast-blow fuse

**Reverse Polarity Protection:**
- Add diodes on power inputs
- Use keyed connectors where possible

**Voltage Monitoring:**
```python
# Monitor supply voltages via ADC (optional)
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Voltage divider: 10kΩ + 2.2kΩ for 6V → 1.08V
chan = AnalogIn(ads, ADS.P0)

def read_servo_voltage():
    return chan.voltage * (12.2 / 2.2)  # Scale back up

# Monitor in background thread
if read_servo_voltage() < 5.5:
    logging.warning("Servo voltage low!")
```

---

## 4. Software Installation

### 4.1 Operating System Setup

#### Step 1: Flash Raspberry Pi OS
```bash
# Use Raspberry Pi Imager
# Select: Raspberry Pi OS (64-bit) - Full version
# Enable SSH in advanced options
# Set hostname: camera-platform
# Set username/password
```

#### Step 2: Initial Boot Configuration
```bash
# SSH into Raspberry Pi
ssh pi@camera-platform.local

# Update system
sudo apt update
sudo apt upgrade -y

# Enable interfaces
sudo raspi-config
# → Interface Options → I2C → Enable
# → Interface Options → Camera → Enable
# → Performance Options → GPU Memory → 256MB
# → Reboot
```

### 4.2 Install Core Dependencies

```bash
# System libraries
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    i2c-tools \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera \
    python3-picamera2 \
    python3-opencv \
    python3-numpy \
    python3-scipy \
    python3-matplotlib

# Verify I2C
sudo i2cdetect -y 1
# Should show device at 0x40 (PCA9685)
```

### 4.3 Install Python Libraries

```bash
# Create virtual environment
cd ~
python3 -m venv camera_platform_env
source camera_platform_env/bin/activate

# Install Python packages
pip install --upgrade pip

# Core libraries
pip install \
    adafruit-circuitpython-pca9685 \
    adafruit-circuitpython-servokit \
    RPi.GPIO \
    picamera2 \
    opencv-python \
    numpy \
    scipy \
    matplotlib

# Web framework
pip install \
    flask \
    flask-cors \
    flask-socketio \
    python-socketio

# Utilities
pip install \
    pyyaml \
    python-dotenv \
    loguru
```

### 4.4 Install Hailo AI Software

```bash
# Install Hailo runtime
wget https://hailo.ai/downloads/hailo-rpi5-runtime.deb
sudo dpkg -i hailo-rpi5-runtime.deb
sudo apt install -f

# Install Hailo Python API
pip install hailort

# Verify installation
hailortcli fw-control identify
# Should show Hailo-8 device info

# Download example models
mkdir -p ~/hailo_models
cd ~/hailo_models
wget https://hailo.ai/downloads/yolov5s.hef
wget https://hailo.ai/downloads/yolov8s.hef
```

### 4.5 Clone Project Repository

```bash
# Clone from GitHub
cd ~
git clone https://github.com/chadsteeleco-prog/SuspensionApp.git
cd SuspensionApp

# Create camera platform directory
mkdir -p camera_platform
cd camera_platform

# Initialize project structure
mkdir -p {src,config,logs,data,models,tests}
```

---

## 5. Calibration Procedures

### 5.1 Servo Calibration

#### Step 1: Find Servo Pulse Width Range
```python
# servo_calibration.py
from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

def calibrate_servo(channel):
    """Find min/max pulse widths for servo"""
    print(f"Calibrating servo on channel {channel}")
    
    # Test range
    for pulse_width in range(500, 2500, 100):
        kit.servo[channel].set_pulse_width_range(pulse_width, pulse_width)
        kit.servo[channel].angle = 90
        time.sleep(0.5)
        
        response = input(f"Pulse width {pulse_width}µs - OK? (y/n/q): ")
        if response == 'q':
            break
        elif response == 'y':
            print(f"Servo responds at {pulse_width}µs")
    
    # Find neutral position
    kit.servo[channel].set_pulse_width_range(1000, 2000)
    kit.servo[channel].angle = 90
    
    print("Adjust to neutral position:")
    for angle in range(0, 180, 5):
        kit.servo[channel].angle = angle
        time.sleep(0.2)

# Calibrate all Stewart platform servos
for i in range(6):
    calibrate_servo(i)
    input(f"Servo {i} calibrated. Press Enter for next...")
```

#### Step 2: Record Calibration Values
```yaml
# config/servo_calibration.yaml
servos:
  - channel: 0
    min_pulse: 1000
    max_pulse: 2000
    neutral_angle: 90
    direction: 1  # 1 or -1
    
  - channel: 1
    min_pulse: 1000
    max_pulse: 2000
    neutral_angle: 90
    direction: 1
    
  # ... repeat for all 6 servos
```

### 5.2 Stewart Platform Geometry Calibration

#### Step 1: Measure Physical Dimensions
```python
# measure_platform.py
import numpy as np

# Measure these values on your actual platform
measurements = {
    'base_radius': 150.0,      # mm - measure from center to servo pivot
    'platform_radius': 80.0,   # mm - measure from center to rod attachment
    'servo_arm_length': 25.0,  # mm - servo horn length
    'rod_length': 200.0,       # mm - connecting rod length
    'home_height': 180.0,      # mm - platform height at neutral
}

# Measure servo mounting angles (degrees from X-axis)
servo_angles = []
for i in range(6):
    angle = float(input(f"Enter angle for servo {i} (degrees): "))
    servo_angles.append(angle)

# Save to config
import yaml
with open('config/platform_geometry.yaml', 'w') as f:
    yaml.dump({
        'measurements': measurements,
        'servo_angles': servo_angles
    }, f)
```

#### Step 2: Verify Kinematics
```python
# test_kinematics.py
from stewart_platform import StewartPlatform

platform = StewartPlatform('config/platform_geometry.yaml')

# Test home position
print("Moving to home position...")
platform.move_to(0, 0, 0, 0, 0, 0)
input("Verify platform is level. Press Enter...")

# Test each axis
test_poses = [
    (10, 0, 0, 0, 0, 0),   # +X translation
    (-10, 0, 0, 0, 0, 0),  # -X translation
    (0, 10, 0, 0, 0, 0),   # +Y translation
    (0, -10, 0, 0, 0, 0),  # -Y translation
    (0, 0, 10, 0, 0, 0),   # +Z translation
    (0, 0, 0, 10, 0, 0),   # +Roll
    (0, 0, 0, 0, 10, 0),   # +Pitch
    (0, 0, 0, 0, 0, 10),   # +Yaw
]

for pose in test_poses:
    print(f"Testing pose: {pose}")
    platform.move_to(*pose)
    input("Verify position. Press Enter for next...")
    platform.move_to(0, 0, 0, 0, 0, 0)  # Return home
```

### 5.3 Camera Calibration

#### Step 1: Focus Calibration
```python
# camera_focus_calibration.py
from picamera2 import Picamera2
import time

picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)
picam2.start()

# Test focus positions
focus_positions = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

for focus in focus_positions:
    picam2.set_controls({"AfMode": 0, "LensPosition": focus})
    time.sleep(1)
    picam2.capture_file(f"focus_test_{focus:.1f}.jpg")
    print(f"Captured at focus position {focus}")

picam2.stop()
print("Review images to determine optimal focus range")
```

#### Step 2: Exposure Calibration
```python
# camera_exposure_calibration.py
from picamera2 import Picamera2

picam2 = Picamera2()

# Test different exposure times
exposure_times = [1000, 5000, 10000, 20000, 50000]  # microseconds

for exp_time in exposure_times:
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    
    picam2.set_controls({"ExposureTime": exp_time, "AnalogueGain": 1.0})
    time.sleep(2)
    
    picam2.capture_file(f"exposure_test_{exp_time}us.jpg")
    print(f"Captured with {exp_time}µs exposure")
    
    picam2.stop()
```

### 5.4 AI Model Calibration

#### Step 1: Test Model Performance
```python
# test_hailo_model.py
from hailo_platform import HEF, VDevice
import cv2
import time

# Load model
hef = HEF("~/hailo_models/yolov5s.hef")
device = VDevice()
network_group = device.configure(hef)[0]

# Test with sample images
test_images = ["test1.jpg", "test2.jpg", "test3.jpg"]

for img_path in test_images:
    img = cv2.imread(img_path)
    
    start_time = time.time()
    # Run inference (simplified)
    # results = run_inference(img)
    inference_time = time.time() - start_time
    
    print(f"{img_path}: {inference_time*1000:.1f}ms")
```

---

## 6. Testing & Validation

### 6.1 Hardware Tests

#### Test 1: I2C Communication
```bash
# Verify PWM HAT is detected
sudo i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --  ← PCA9685
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- -- --
```

#### Test 2: Servo Movement
```python
# test_servos.py
from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

def test_servo(channel):
    """Test single servo movement"""
    print(f"Testing servo {channel}")
    
    # Sweep test
    for angle in [0, 45, 90, 135, 180, 90]:
        kit.servo[channel].angle = angle
        print(f"  Angle: {angle}°")
        time.sleep(1)
    
    print(f"Servo {channel} test complete")

# Test all Stewart platform servos
for i in range(6):
    test_servo(i)
    input("Press Enter to test next servo...")
```

#### Test 3: Camera Capture
```python
# test_camera.py
from picamera2 import Picamera2

picam2 = Picamera2()

# Test preview
print("Starting preview...")
config = picam2.create_preview_configuration()
picam2.configure(config)
picam2.start()
time.sleep(5)
picam2.stop()

# Test still capture
print("Capturing still image...")
config = picam2.create_still_configuration()
picam2.configure(config)
picam2.start()
picam2.capture_file("test_image.jpg")
picam2.stop()
print("Image saved as test_image.jpg")
```

#### Test 4: AI Accelerator
```bash
# Test Hailo device
hailortcli fw-control identify

# Expected output:
# Hailo-8 device found
# Device ID: ...
# Firmware version: ...
```

### 6.2 Integration Tests

#### Test 1: Coordinated Motion
```python
# test_coordinated_motion.py
from stewart_platform import StewartPlatform
from camera_control import CameraController
import time

platform = StewartPlatform()
camera = CameraController()

# Test sequence: Move platform and capture images
test_sequence = [
    (0, 0, 0, 0, 0, 0),      # Home
    (10, 0, 0, 0, 0, 0),     # +X
    (0, 10, 0, 0, 0, 0),     # +Y
    (0, 0, 0, 10, 0, 0),     # +Roll
    (0, 0, 0, 0, 10, 0),     # +Pitch
]

for i, pose in enumerate(test_sequence):
    print(f"Moving to pose {i}: {pose}")
    platform.move_to(*pose)
    time.sleep(2)  # Settle time
    
    camera.capture_image(f"test_pose_{i}.jpg")
    print(f"Captured image {i}")
    
    time.sleep(1)

platform.move_to(0, 0, 0, 0, 0, 0)  # Return home
print("Test complete")
```

#### Test 2: AI Tracking
```python
# test_ai_tracking.py
from ai_processor import ObjectTracker
from camera_control import CameraController
import cv2

tracker = ObjectTracker("~/hailo_models/yolov5s.hef")
camera = CameraController()

# Capture frame
frame = camera.capture_array()

# Detect objects
detections = tracker.detect_objects(frame)

# Draw bounding boxes
for det in detections:
    x, y, w, h = det['bbox']
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(frame, det['class'], (x, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Save result
cv2.imwrite("detection_test.jpg", frame)
print(f"Detected {len(detections)} objects")
```

### 6.3 Safety Tests

#### Test 1: Emergency Stop
```python
# test_emergency_stop.py
import RPi.GPIO as GPIO
from stewart_platform import StewartPlatform

platform = StewartPlatform()

# Setup E-stop
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def emergency_stop_callback(channel):
    print("EMERGENCY STOP TRIGGERED")
    platform.emergency_stop()

GPIO.add_event_detect(22, GPIO.FALLING, callback=emergency_stop_callback)

# Test motion
print("Starting motion test...")
print("Press E-stop button to test")

platform.move_to(10, 10, 0, 0, 0, 0)
time.sleep(5)

print("Test complete")
GPIO.cleanup()
```

#### Test 2: Limit Detection
```python
# test_limits.py
from stewart_platform import StewartPlatform

platform = StewartPlatform()

# Test exceeding limits
test_cases = [
    (50, 0, 0, 0, 0, 0),    # X too large
    (0, 0, 0, 40, 0, 0),    # Roll too large
    (0, 0, -30, 0, 0, 0),   # Z too low
]

for pose in test_cases:
    try:
        print(f"Testing pose: {pose}")
        platform.move_to(*pose)
        print("  ERROR: Should have been rejected!")
    except ValueError as e:
        print(f"  Correctly rejected: {e}")
```

### 6.4 Performance Tests

#### Test 1: Motion Accuracy
```python
# test_accuracy.py
from stewart_platform import StewartPlatform
import numpy as np

platform = StewartPlatform()

# Test repeatability
target_pose = (10, 10, 5, 5, 5, 5)
measurements = []

for i in range(10):
    platform.move_to(*target_pose)
    time.sleep(2)
    
    # Measure actual position (requires external measurement system)
    # actual_pose = measure_position()
    # measurements.append(actual_pose)
    
    platform.move_to(0, 0, 0, 0, 0, 0)
    time.sleep(2)

# Calculate repeatability
# std_dev = np.std(measurements, axis=0)
# print(f"Repeatability (std dev): {std_dev}")
```

#### Test 2: Speed Test
```python
# test_speed.py
from stewart_platform import StewartPlatform
import time

platform = StewartPlatform()

# Measure motion time
start_time = time.time()
platform.move_to(20, 20, 10, 10, 10, 10)
motion_time = time.time() - start_time

print(f"Motion time: {motion_time:.2f}s")

# Measure settling time
start_time = time.time()
while not platform.is_settled():
    time.sleep(0.01)
settling_time = time.time() - start_time

print(f"Settling time: {settling_time:.2f}s")
```

---

## 7. Troubleshooting

### 7.1 Common Issues

#### Issue: Servos not responding
**Symptoms:** No servo movement, no sound from servos

**Solutions:**
1. Check I2C connection: `sudo i2cdetect -y 1`
2. Verify servo power supply (6V connected)
3. Check PWM HAT LED indicators
4. Test with simple servo sweep script
5. Verify GPIO pins not conflicting

#### Issue: Camera not detected
**Symptoms:** `libcamera` errors, no camera in `/dev`

**Solutions:**
1. Check CSI cable connection (contacts facing HDMI)
2. Enable camera in `raspi-config`
3. Reboot after enabling
4. Test with: `libcamera-hello`
5. Check for firmware updates

#### Issue: AI HAT not detected
**Symptoms:** `hailortcli` shows no device

**Solutions:**
1. Verify PCIe connection is secure
2. Check active cooler is running
3. Reinstall Hailo runtime
4. Check kernel logs: `dmesg | grep hailo`
5. Verify PCIe is enabled in config.txt

#### Issue: Platform drifts or vibrates
**Symptoms:** Platform doesn't hold position, oscillates

**Solutions:**
1. Recalibrate servo neutral positions
2. Check for loose mechanical connections
3. Reduce motion speed
4. Increase settling time
5. Check servo power supply voltage

### 7.2 Diagnostic Commands

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Check camera
libcamera-hello --list-cameras

# Check Hailo device
hailortcli fw-control identify

# Check GPIO
gpio readall

# Monitor system resources
htop

# Check logs
journalctl -u camera-platform -f

# Test servo power
# Use multimeter on PWM HAT terminal block
```

---

## 8. Maintenance

### 8.1 Regular Maintenance Schedule

**Daily (if in use):**
- [ ] Visual inspection of all connections
- [ ] Check servo temperatures
- [ ] Verify camera focus

**Weekly:**
- [ ] Clean camera lens
- [ ] Check mechanical fasteners
- [ ] Test emergency stop
- [ ] Backup configuration files

**Monthly:**
- [ ] Recalibrate servos
- [ ] Update software
- [ ] Check power supply voltages
- [ ] Inspect cables for wear

**Quarterly:**
- [ ] Full system calibration
- [ ] Replace thermal paste on coolers
- [ ] Test all safety systems
- [ ] Performance benchmarking

### 8.2 Backup Procedures

```bash
# Backup configuration
cd ~/camera_platform
tar -czf backup_$(date +%Y%m%d).tar.gz config/ logs/

# Backup to remote server
scp backup_*.tar.gz user@backup-server:/backups/

# Backup SD card image (from another computer)
sudo dd if=/dev/sdX of=camera_platform_backup.img bs=4M status=progress
```

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Next Review:** After hardware arrival and initial testing