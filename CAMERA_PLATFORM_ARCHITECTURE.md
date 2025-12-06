# Camera Platform with Stewart Platform - System Architecture

## Executive Summary

This document outlines the complete system architecture for a camera platform controlled by a Stewart platform (6-DOF parallel manipulator), integrated with a Raspberry Pi 5, high-resolution camera, AI accelerator, and servo control system.

## 1. Hardware Components Overview

### 1.1 Computing Platform
- **Raspberry Pi 5 (8GB RAM)**
  - Quad-core ARM Cortex-A76 @ 2.4GHz
  - 8GB LPDDR4X RAM
  - Dual 4Kp60 HDMI display outputs
  - 2× USB 3.0, 2× USB 2.0 ports
  - Gigabit Ethernet with PoE+ support
  - PCIe 2.0 x1 interface
  - 40-pin GPIO header
  - Active cooling included

### 1.2 Camera System
- **Arducam OwlSight 64MP Camera**
  - Sensor: 1/1.32" 64MP (9248×6944 pixels)
  - Auto-focus capability
  - Native libcamera support
  - High dynamic range
  - Suitable for high-resolution photography and video
  - CSI interface to Raspberry Pi

### 1.3 AI Processing
- **GeeekPi AI HAT+ with Hailo-8 Accelerator**
  - 26 TOPS AI performance
  - Hailo-8 neural network processor
  - PCIe Gen 3 interface
  - Metal case with active cooling
  - Supports TensorFlow, PyTorch, ONNX models
  - Real-time object detection, tracking, segmentation

### 1.4 Motion Control
- **PWM Servo Driver HAT**
  - 16-channel 12-bit PWM controller (PCA9685)
  - I2C interface (address: 0x40 default)
  - 40-1000Hz PWM frequency
  - 5V servo power rail (external power required)
  - Supports 6 servos for Stewart platform + 2 for camera controls

### 1.5 Stewart Platform
- **6-DOF Parallel Manipulator**
  - 6× 80KG RC hobby servos (high torque)
  - Degrees of freedom: X, Y, Z translation + Roll, Pitch, Yaw rotation
  - Typical workspace: ±30° rotation, ±50mm translation
  - Payload capacity: ~5kg (camera + mounting hardware)
  - Precision: ~0.1mm positioning accuracy

## 2. System Architecture

### 2.1 Hardware Stack (Bottom to Top)
```
┌─────────────────────────────────────────┐
│   Camera (OwlSight 64MP)                │
│   - Shutter Control (GPIO)              │
│   - Zoom Control (Servo Channel 15)     │
└─────────────────────────────────────────┘
                    ↓ CSI
┌─────────────────────────────────────────┐
│   Raspberry Pi 5 (8GB)                  │
│   - Main Controller                     │
│   - Image Processing                    │
│   - Motion Planning                     │
└─────────────────────────────────────────┘
         ↓ PCIe          ↓ I2C        ↓ GPIO
┌──────────────┐  ┌──────────────┐  ┌──────┐
│  AI HAT+     │  │ PWM Servo    │  │Camera│
│  (Hailo-8)   │  │ Driver HAT   │  │GPIO  │
│  26 TOPS     │  │ PCA9685      │  │      │
└──────────────┘  └──────────────┘  └──────┘
                         ↓ PWM
              ┌──────────────────────┐
              │  Stewart Platform    │
              │  6× 80KG Servos      │
              │  Channels 0-5        │
              └──────────────────────┘
```

### 2.2 Pin Assignments

#### GPIO Pin Usage (40-pin header)
```
Pin 1  (3.3V)     → Power for sensors
Pin 2  (5V)       → Power for HATs
Pin 3  (GPIO 2)   → I2C SDA (PWM HAT)
Pin 5  (GPIO 3)   → I2C SCL (PWM HAT)
Pin 6  (GND)      → Ground
Pin 9  (GND)      → Ground
Pin 14 (GND)      → Ground
Pin 17 (3.3V)     → Power
Pin 20 (GND)      → Ground

Pin 11 (GPIO 17)  → Camera Shutter Trigger
Pin 13 (GPIO 27)  → Status LED
Pin 15 (GPIO 22)  → Emergency Stop Input
Pin 16 (GPIO 23)  → Limit Switch 1
Pin 18 (GPIO 24)  → Limit Switch 2
```

#### PWM Servo Channels (PCA9685)
```
Channel 0  → Stewart Platform Servo 1 (Base, 0°)
Channel 1  → Stewart Platform Servo 2 (Base, 60°)
Channel 2  → Stewart Platform Servo 3 (Base, 120°)
Channel 3  → Stewart Platform Servo 4 (Base, 180°)
Channel 4  → Stewart Platform Servo 5 (Base, 240°)
Channel 5  → Stewart Platform Servo 6 (Base, 300°)
Channel 14 → Camera Focus Control (if motorized)
Channel 15 → Camera Zoom Control
```

### 2.3 Power Distribution
```
┌─────────────────────────────────────────┐
│  Main Power Supply                      │
│  - 5V 10A for Raspberry Pi + HATs       │
│  - 6V 20A for Servo System              │
└─────────────────────────────────────────┘
         ↓                    ↓
┌──────────────────┐  ┌──────────────────┐
│  5V Rail         │  │  6V Servo Rail   │
│  - RPi5: 5V 5A   │  │  - 6× 80KG Servo │
│  - AI HAT: 5V 2A │  │  - Peak: 6V 15A  │
│  - PWM HAT: 5V 1A│  │  - Avg: 6V 5A    │
└──────────────────┘  └──────────────────┘
```

**Power Requirements:**
- Raspberry Pi 5: 5V 5A (27W USB-C PD)
- AI HAT+: 5V 2A (via GPIO, with cooling)
- PWM HAT: 5V 0.5A (logic only)
- Servos (6× 80KG): 6V 15A peak (2.5A each under load)
- Camera: Powered via CSI (minimal)
- **Total: 5V 7.5A + 6V 15A = ~130W peak**

## 3. Software Architecture

### 3.1 System Layers
```
┌─────────────────────────────────────────────────┐
│  Application Layer                              │
│  - Web UI (Flask/FastAPI)                       │
│  - REST API                                     │
│  - CLI Tools                                    │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Control Layer                                  │
│  - Motion Planning                              │
│  - Camera Control                               │
│  - AI Processing Pipeline                       │
│  - Safety & Limits                              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Hardware Abstraction Layer                     │
│  - Stewart Platform Driver                      │
│  - Camera Driver (libcamera)                    │
│  - Servo Controller (PCA9685)                   │
│  - AI Accelerator (Hailo SDK)                   │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Operating System (Raspberry Pi OS 64-bit)      │
│  - Linux Kernel 6.1+                            │
│  - Device Drivers                               │
│  - I2C, GPIO, CSI interfaces                    │
└─────────────────────────────────────────────────┘
```

### 3.2 Software Components

#### Core Modules
1. **Stewart Platform Controller** (`stewart_platform.py`)
   - Forward kinematics (platform pose → servo angles)
   - Inverse kinematics (servo angles → platform pose)
   - Smooth trajectory generation
   - Velocity and acceleration limits
   - Collision detection

2. **Camera Controller** (`camera_control.py`)
   - libcamera integration
   - Auto-focus control
   - Exposure settings
   - Shutter trigger (GPIO)
   - Zoom control (servo)
   - Image capture and storage

3. **AI Processing Pipeline** (`ai_processor.py`)
   - Hailo-8 model loading
   - Real-time object detection
   - Tracking and following
   - Scene analysis
   - Auto-framing

4. **Motion Planner** (`motion_planner.py`)
   - Path planning algorithms
   - Smooth motion profiles
   - Multi-point sequences
   - Time-lapse positioning
   - Tracking mode

5. **Safety System** (`safety_monitor.py`)
   - Limit switch monitoring
   - Emergency stop handling
   - Servo current monitoring
   - Temperature monitoring
   - Fault detection and recovery

6. **Web Interface** (`web_server.py`)
   - Real-time control panel
   - Live camera preview
   - Motion presets
   - Configuration management
   - Status monitoring

### 3.3 Communication Protocols

#### I2C Bus (PWM Servo HAT)
```python
# I2C Address: 0x40 (default PCA9685)
# Frequency: 50Hz for servos
# Resolution: 12-bit (0-4095)

# Servo pulse width: 1000-2000µs
# Neutral: 1500µs (90°)
# Min: 1000µs (0°)
# Max: 2000µs (180°)
```

#### CSI Interface (Camera)
```python
# libcamera pipeline
# Resolution: Up to 9248×6944 (64MP)
# Frame rate: 30fps @ 1080p, 10fps @ full res
# Format: RAW, JPEG, H.264
```

#### PCIe (AI HAT+)
```python
# Hailo-8 interface
# Bandwidth: PCIe Gen 3 x1 (8 Gbps)
# Latency: <10ms inference
# Models: YOLOv5, YOLOv8, ResNet, MobileNet
```

## 4. Stewart Platform Kinematics

### 4.1 Coordinate Systems

**Base Frame (Fixed)**
```
       Y
       ↑
       |
       |
       └────→ X
      /
     /
    Z (up)
```

**Platform Frame (Moving)**
- Origin at platform center
- Same orientation as base when at home position
- 6-DOF: (x, y, z, roll, pitch, yaw)

### 4.2 Geometry Parameters
```python
# Platform dimensions (typical values, adjust for your build)
BASE_RADIUS = 150.0      # mm, base mounting circle radius
PLATFORM_RADIUS = 80.0   # mm, platform mounting circle radius
SERVO_ARM_LENGTH = 25.0  # mm, servo horn length
ROD_LENGTH = 200.0       # mm, connecting rod length
HOME_HEIGHT = 180.0      # mm, platform height at neutral

# Servo mounting angles (degrees, from X-axis)
SERVO_ANGLES = [0, 60, 120, 180, 240, 300]

# Platform attachment angles (offset from servo angles)
PLATFORM_ANGLES = [30, 90, 150, 210, 270, 330]
```

### 4.3 Inverse Kinematics Algorithm

**Goal:** Given desired platform pose (x, y, z, roll, pitch, yaw), calculate 6 servo angles.

**Steps:**
1. Calculate platform attachment points in base frame
2. Apply rotation matrix (roll, pitch, yaw)
3. Apply translation (x, y, z)
4. For each servo:
   - Calculate vector from servo to platform attachment
   - Solve triangle: servo arm + rod = attachment point
   - Calculate servo angle using law of cosines

**Python Implementation:**
```python
def inverse_kinematics(x, y, z, roll, pitch, yaw):
    """
    Calculate servo angles for desired platform pose.
    
    Args:
        x, y, z: Translation in mm
        roll, pitch, yaw: Rotation in radians
    
    Returns:
        List of 6 servo angles in degrees
    """
    # Rotation matrix
    R = rotation_matrix(roll, pitch, yaw)
    
    # Platform center position
    platform_center = np.array([x, y, z + HOME_HEIGHT])
    
    servo_angles = []
    
    for i in range(6):
        # Base servo position
        servo_pos = base_servo_position(i)
        
        # Platform attachment position (in platform frame)
        attach_local = platform_attachment_position(i)
        
        # Transform to base frame
        attach_global = platform_center + R @ attach_local
        
        # Vector from servo to attachment
        vec = attach_global - servo_pos
        
        # Solve for servo angle
        angle = solve_servo_angle(vec, SERVO_ARM_LENGTH, ROD_LENGTH)
        
        servo_angles.append(angle)
    
    return servo_angles
```

### 4.4 Forward Kinematics

**Goal:** Given 6 servo angles, calculate platform pose.

**Method:** Iterative numerical solution (Newton-Raphson)
- More complex than inverse kinematics
- Used for verification and calibration
- Not required for real-time control

## 5. Camera Control Integration

### 5.1 Camera Capabilities

**Arducam OwlSight 64MP Features:**
- Resolution: 9248×6944 pixels (64MP)
- Sensor size: 1/1.32" (11.3mm diagonal)
- Pixel size: 1.4µm
- Auto-focus: Phase detection
- Dynamic range: 12-bit RAW
- Video: 4K@30fps, 1080p@60fps

### 5.2 Control Interfaces

#### Shutter Control (GPIO)
```python
import RPi.GPIO as GPIO

SHUTTER_PIN = 17

def setup_shutter():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SHUTTER_PIN, GPIO.OUT)
    GPIO.output(SHUTTER_PIN, GPIO.LOW)

def trigger_shutter():
    """Trigger camera shutter via GPIO pulse"""
    GPIO.output(SHUTTER_PIN, GPIO.HIGH)
    time.sleep(0.1)  # 100ms pulse
    GPIO.output(SHUTTER_PIN, GPIO.LOW)
```

#### Zoom Control (Servo)
```python
from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)
ZOOM_CHANNEL = 15

def set_zoom(zoom_percent):
    """
    Set camera zoom level.
    
    Args:
        zoom_percent: 0-100, where 0 is wide, 100 is telephoto
    """
    angle = 0 + (zoom_percent / 100.0) * 180
    kit.servo[ZOOM_CHANNEL].angle = angle
```

#### Focus Control (libcamera)
```python
from picamera2 import Picamera2

picam2 = Picamera2()

def set_focus(focus_distance):
    """
    Set camera focus distance.
    
    Args:
        focus_distance: 0.0 (infinity) to 1.0 (macro)
    """
    picam2.set_controls({"AfMode": 0, "LensPosition": focus_distance})
```

### 5.3 Image Capture Modes

#### Single Shot
```python
def capture_image(filename, resolution=(9248, 6944)):
    """Capture single high-resolution image"""
    config = picam2.create_still_configuration(
        main={"size": resolution, "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)  # Allow auto-exposure
    picam2.capture_file(filename)
    picam2.stop()
```

#### Time-Lapse
```python
def capture_timelapse(interval, count, output_dir):
    """Capture time-lapse sequence"""
    for i in range(count):
        filename = f"{output_dir}/frame_{i:04d}.jpg"
        capture_image(filename)
        time.sleep(interval)
```

#### Video Recording
```python
def record_video(filename, duration, resolution=(1920, 1080)):
    """Record video with H.264 encoding"""
    config = picam2.create_video_configuration(
        main={"size": resolution, "format": "RGB888"}
    )
    encoder = H264Encoder(bitrate=10000000)
    picam2.configure(config)
    picam2.start_recording(encoder, filename)
    time.sleep(duration)
    picam2.stop_recording()
```

## 6. AI Processing Pipeline

### 6.1 Hailo-8 Integration

**Capabilities:**
- 26 TOPS performance
- Real-time inference at 30+ FPS
- Multiple models simultaneously
- Low latency (<10ms)

**Supported Models:**
- Object detection: YOLOv5, YOLOv8, SSD
- Classification: ResNet, MobileNet, EfficientNet
- Segmentation: DeepLabv3, U-Net
- Pose estimation: OpenPose, MediaPipe

### 6.2 Object Detection & Tracking

```python
from hailo_platform import HEF, VDevice, InferVStreams, ConfigureParams

class ObjectTracker:
    def __init__(self, model_path):
        self.hef = HEF(model_path)
        self.device = VDevice()
        self.network_group = self.device.configure(self.hef)[0]
        
    def detect_objects(self, frame):
        """
        Detect objects in frame using Hailo-8.
        
        Returns:
            List of detections: [(x, y, w, h, class, confidence), ...]
        """
        # Preprocess frame
        input_data = self.preprocess(frame)
        
        # Run inference
        with InferVStreams(self.network_group) as infer_pipeline:
            output = infer_pipeline.infer({self.input_name: input_data})
        
        # Post-process results
        detections = self.postprocess(output)
        
        return detections
    
    def track_object(self, detections, target_class):
        """
        Track specific object class and return center coordinates.
        """
        for det in detections:
            if det['class'] == target_class:
                center_x = det['x'] + det['w'] / 2
                center_y = det['y'] + det['h'] / 2
                return (center_x, center_y)
        return None
```

### 6.3 Auto-Framing System

```python
class AutoFraming:
    def __init__(self, stewart_platform, camera, tracker):
        self.platform = stewart_platform
        self.camera = camera
        self.tracker = tracker
        
    def follow_object(self, target_class, duration):
        """
        Automatically track and frame object using Stewart platform.
        """
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Capture frame
            frame = self.camera.capture_array()
            
            # Detect objects
            detections = self.tracker.detect_objects(frame)
            
            # Find target
            target_pos = self.tracker.track_object(detections, target_class)
            
            if target_pos:
                # Calculate error from center
                frame_center = (frame.shape[1] / 2, frame.shape[0] / 2)
                error_x = target_pos[0] - frame_center[0]
                error_y = target_pos[1] - frame_center[1]
                
                # Convert to platform motion (PID control)
                pan = self.pid_pan.update(error_x)
                tilt = self.pid_tilt.update(error_y)
                
                # Move platform
                self.platform.move_relative(yaw=pan, pitch=tilt)
            
            time.sleep(0.033)  # 30 FPS
```

## 7. Safety & Limits

### 7.1 Software Limits

```python
# Motion limits (mm and degrees)
LIMITS = {
    'x': (-30, 30),
    'y': (-30, 30),
    'z': (-20, 40),
    'roll': (-25, 25),
    'pitch': (-25, 25),
    'yaw': (-30, 30)
}

# Velocity limits (mm/s and deg/s)
MAX_VELOCITY = {
    'translation': 50,  # mm/s
    'rotation': 30      # deg/s
}

# Acceleration limits (mm/s² and deg/s²)
MAX_ACCELERATION = {
    'translation': 100,  # mm/s²
    'rotation': 60       # deg/s²
}
```

### 7.2 Hardware Safety

```python
class SafetyMonitor:
    def __init__(self):
        self.emergency_stop = False
        self.setup_gpio()
        
    def setup_gpio(self):
        """Setup emergency stop and limit switches"""
        GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # E-stop
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Limit 1
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Limit 2
        
        # Interrupt handlers
        GPIO.add_event_detect(22, GPIO.FALLING, callback=self.emergency_stop_handler)
        
    def emergency_stop_handler(self, channel):
        """Handle emergency stop button press"""
        self.emergency_stop = True
        self.disable_all_servos()
        logging.critical("EMERGENCY STOP ACTIVATED")
        
    def check_limits(self, pose):
        """Verify pose is within safe limits"""
        for axis, (min_val, max_val) in LIMITS.items():
            if not (min_val <= pose[axis] <= max_val):
                raise ValueError(f"{axis} out of range: {pose[axis]}")
        return True
```

### 7.3 Servo Protection

```python
def monitor_servo_current():
    """Monitor servo current draw to detect stalls"""
    # Requires current sensor on servo power rail
    current = read_current_sensor()
    
    if current > MAX_SERVO_CURRENT:
        logging.warning(f"High servo current: {current}A")
        reduce_servo_speed()
        
    if current > CRITICAL_SERVO_CURRENT:
        logging.error("Critical servo current - stopping")
        emergency_stop()
```

## 8. Use Cases & Applications

### 8.1 Automated Photography

**Product Photography:**
- 360° rotation sequences
- Multi-angle shots
- Consistent lighting and framing
- Batch processing

**Time-Lapse:**
- Smooth motion time-lapse
- Multi-axis movements
- Sunrise/sunset tracking
- Construction progress

### 8.2 Video Production

**Cinematic Shots:**
- Smooth pan and tilt
- Programmed camera moves
- Repeatable sequences
- Slow-motion compatible

**Live Streaming:**
- Auto-tracking speakers
- Dynamic framing
- Multi-camera coordination

### 8.3 Inspection & Monitoring

**Industrial Inspection:**
- Automated part inspection
- Defect detection with AI
- Consistent viewing angles
- Documentation

**Security & Surveillance:**
- Intelligent tracking
- Perimeter monitoring
- Event-triggered recording

### 8.4 Scientific & Research

**Microscopy:**
- Automated focus stacking
- Multi-position imaging
- Time-series capture

**Astronomy:**
- Star tracking
- Long-exposure stacking
- Planetary imaging

### 8.5 Integration with Suspension Testing

**Vehicle Testing:**
- Multi-angle suspension movement capture
- Synchronized with suspension app data
- High-speed video analysis
- Automated documentation

**Data Correlation:**
- Camera timestamps synced with G-force data
- Visual verification of sensor readings
- Automated report generation

## 9. Performance Specifications

### 9.1 Motion Performance

**Positioning:**
- Accuracy: ±0.5mm, ±0.5°
- Repeatability: ±0.2mm, ±0.2°
- Resolution: 0.1mm, 0.1°

**Speed:**
- Max translation: 50mm/s
- Max rotation: 30°/s
- Settling time: <0.5s

**Workspace:**
- X, Y: ±30mm
- Z: -20 to +40mm
- Roll, Pitch: ±25°
- Yaw: ±30°

### 9.2 Camera Performance

**Image Quality:**
- Resolution: 64MP (9248×6944)
- Bit depth: 12-bit RAW
- Dynamic range: >12 stops
- ISO range: 100-12800

**Capture Speed:**
- Full resolution: 2 fps
- 4K video: 30 fps
- 1080p video: 60 fps
- Burst mode: 10 fps @ 16MP

### 9.3 AI Performance

**Inference Speed:**
- YOLOv5s: 60 FPS @ 640×640
- YOLOv8m: 30 FPS @ 640×640
- ResNet50: 120 FPS
- Latency: <10ms

**Detection Accuracy:**
- mAP@0.5: >0.85 (COCO dataset)
- Tracking: 30 FPS with 10+ objects

## 10. Next Steps

### 10.1 Immediate Tasks
1. Verify Stewart platform geometry and servo configuration
2. Install Raspberry Pi OS and required software
3. Test PWM servo HAT communication
4. Calibrate camera and test libcamera
5. Verify AI HAT+ installation and run test models

### 10.2 Development Phases

**Phase 1: Basic Control (Week 1)**
- [ ] Servo control via PWM HAT
- [ ] Manual Stewart platform positioning
- [ ] Camera capture and preview
- [ ] Basic web interface

**Phase 2: Kinematics (Week 2)**
- [ ] Implement inverse kinematics
- [ ] Smooth motion planning
- [ ] Safety limits and monitoring
- [ ] Calibration procedures

**Phase 3: AI Integration (Week 3)**
- [ ] Hailo-8 model deployment
- [ ] Object detection pipeline
- [ ] Auto-tracking system
- [ ] Performance optimization

**Phase 4: Applications (Week 4)**
- [ ] Time-lapse sequences
- [ ] 360° photography
- [ ] Video recording modes
- [ ] Integration with suspension app

### 10.3 Testing & Validation
- [ ] Servo load testing
- [ ] Motion accuracy verification
- [ ] Camera focus and exposure calibration
- [ ] AI model accuracy testing
- [ ] Safety system validation
- [ ] Long-duration reliability testing

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Author:** SuperNinja AI Agent  
**Project:** Camera Platform with Stewart Platform Integration