# Camera Platform Implementation Roadmap

## Overview

This roadmap outlines the step-by-step implementation plan for the camera platform with Stewart platform control system. The project is divided into 4 phases, each building upon the previous one.

---

## Phase 1: Basic Hardware Setup & Control (Week 1)

**Goal:** Get basic hardware communication working and verify all components.

### Day 1-2: Hardware Assembly & Power Setup
- [ ] Assemble Raspberry Pi 5 with active cooler
- [ ] Stack AI HAT+ on Raspberry Pi 5
- [ ] Stack PWM Servo HAT on AI HAT+
- [ ] Connect camera via CSI cable
- [ ] Set up dual power supply system (5V for RPi, 6V for servos)
- [ ] Verify power distribution and voltages
- [ ] Test all cooling fans

**Deliverables:**
- Fully assembled hardware stack
- Power system operational
- All components powered and cooled

### Day 3-4: Software Installation & Basic Testing
- [ ] Flash Raspberry Pi OS (64-bit) to SD card
- [ ] Complete initial OS setup and updates
- [ ] Enable I2C and Camera interfaces
- [ ] Install Python dependencies
- [ ] Install Hailo AI runtime
- [ ] Verify I2C communication with PWM HAT
- [ ] Test camera with libcamera-hello
- [ ] Verify Hailo device detection

**Deliverables:**
- Raspberry Pi OS configured
- All software dependencies installed
- Hardware communication verified

**Testing Commands:**
```bash
# Verify I2C
sudo i2cdetect -y 1

# Test camera
libcamera-hello --list-cameras

# Test Hailo
hailortcli fw-control identify
```

### Day 5-7: Servo Control & Basic Motion
- [ ] Connect 6 servos to PWM HAT channels 0-5
- [ ] Test individual servo movement
- [ ] Calibrate servo pulse width ranges
- [ ] Find neutral positions for all servos
- [ ] Test coordinated servo movement
- [ ] Implement emergency stop circuit
- [ ] Test safety features

**Deliverables:**
- All 6 servos responding correctly
- Servo calibration data recorded
- Emergency stop functional

**Test Script:**
```python
from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

# Test each servo
for i in range(6):
    print(f"Testing servo {i}")
    kit.servo[i].angle = 90  # Neutral
    time.sleep(1)
    kit.servo[i].angle = 45
    time.sleep(1)
    kit.servo[i].angle = 135
    time.sleep(1)
    kit.servo[i].angle = 90
    time.sleep(1)
```

---

## Phase 2: Kinematics & Motion Planning (Week 2)

**Goal:** Implement Stewart platform kinematics and smooth motion control.

### Day 8-10: Platform Geometry & Calibration
- [ ] Measure actual platform dimensions
- [ ] Record servo mounting angles
- [ ] Record platform attachment angles
- [ ] Create platform_geometry.yaml configuration
- [ ] Implement inverse kinematics algorithm
- [ ] Test kinematics with simple poses
- [ ] Verify reachability calculations

**Deliverables:**
- Accurate platform geometry measurements
- Working inverse kinematics implementation
- Kinematics validation tests passing

**Calibration Procedure:**
```python
# Measure and record:
# 1. Base radius (center to servo pivot)
# 2. Platform radius (center to rod attachment)
# 3. Servo arm length
# 4. Rod length
# 5. Home height
# 6. Servo angles (0°, 60°, 120°, 180°, 240°, 300°)
```

### Day 11-12: Motion Planning & Safety
- [ ] Implement motion limits checking
- [ ] Add velocity and acceleration limits
- [ ] Implement smooth motion interpolation
- [ ] Add collision detection
- [ ] Test limit enforcement
- [ ] Verify emergency stop behavior
- [ ] Test motion sequences

**Deliverables:**
- Safe motion planning system
- Smooth trajectory generation
- All safety features operational

**Test Sequence:**
```python
platform = StewartPlatform()

# Test each axis independently
test_poses = [
    (10, 0, 0, 0, 0, 0),   # +X
    (0, 10, 0, 0, 0, 0),   # +Y
    (0, 0, 10, 0, 0, 0),   # +Z
    (0, 0, 0, 10, 0, 0),   # +Roll
    (0, 0, 0, 0, 10, 0),   # +Pitch
    (0, 0, 0, 0, 0, 10),   # +Yaw
]

for pose in test_poses:
    platform.move_to(*pose, duration=2.0)
    time.sleep(3)
    platform.home()
    time.sleep(2)
```

### Day 13-14: Camera Integration
- [ ] Test camera capture at various resolutions
- [ ] Implement auto-focus control
- [ ] Test exposure settings
- [ ] Implement GPIO shutter trigger
- [ ] Connect zoom servo (channel 15)
- [ ] Test zoom control
- [ ] Implement time-lapse capture
- [ ] Test video recording

**Deliverables:**
- Full camera control operational
- All capture modes working
- Zoom control functional

**Camera Tests:**
```python
camera = CameraController()

# Test resolutions
camera.capture_image(resolution=(1920, 1080))
camera.capture_image(resolution=(4624, 3472))
camera.capture_image(resolution=(9248, 6944))

# Test time-lapse
camera.capture_timelapse(interval=2.0, count=10)

# Test video
camera.record_video(duration=10, resolution=(1920, 1080))
```

---

## Phase 3: AI Integration & Auto-Tracking (Week 3)

**Goal:** Implement AI-powered object detection and automatic camera tracking.

### Day 15-17: AI Model Setup
- [ ] Download YOLOv5/v8 HEF models
- [ ] Test model loading on Hailo-8
- [ ] Implement object detection pipeline
- [ ] Test detection on sample images
- [ ] Measure inference performance
- [ ] Optimize preprocessing/postprocessing
- [ ] Test with live camera feed

**Deliverables:**
- AI models running on Hailo-8
- Object detection working
- Real-time performance achieved (30+ FPS)

**Performance Targets:**
- YOLOv5s: 60 FPS @ 640×640
- YOLOv8m: 30 FPS @ 640×640
- Latency: <10ms

### Day 18-19: Object Tracking
- [ ] Implement multi-object tracker
- [ ] Test tracking with moving objects
- [ ] Implement track ID assignment
- [ ] Add velocity estimation
- [ ] Test tracking persistence
- [ ] Handle occlusions
- [ ] Optimize tracking parameters

**Deliverables:**
- Robust object tracking system
- Track persistence across frames
- Velocity estimation working

### Day 20-21: Auto-Framing System
- [ ] Integrate detector with platform controller
- [ ] Implement PID controller for tracking
- [ ] Test auto-framing with stationary target
- [ ] Test with moving target
- [ ] Tune PID parameters
- [ ] Add target selection logic
- [ ] Test multi-target scenarios

**Deliverables:**
- Auto-framing system operational
- Smooth target tracking
- Configurable tracking behavior

**Auto-Framing Test:**
```python
detector = ObjectDetector("~/hailo_models/yolov5s.hef")
tracker = ObjectTracker()
auto_framing = AutoFraming(detector, tracker, platform, camera)

# Track a person
auto_framing.start_tracking("person")

# System will automatically adjust platform to keep person centered
# Run for 60 seconds
time.sleep(60)

auto_framing.stop_tracking()
```

---

## Phase 4: Web Interface & Applications (Week 4)

**Goal:** Create user-friendly web interface and implement practical applications.

### Day 22-24: Web Interface Development
- [ ] Set up Flask web server
- [ ] Create REST API endpoints
- [ ] Implement WebSocket for real-time updates
- [ ] Create HTML/CSS/JS frontend
- [ ] Add live camera preview
- [ ] Implement motion control UI
- [ ] Add preset positions
- [ ] Create configuration interface

**Deliverables:**
- Functional web interface
- Real-time control panel
- Live camera feed
- Configuration management

**API Endpoints:**
```
GET  /api/status
POST /api/platform/move
POST /api/platform/home
POST /api/camera/capture
POST /api/camera/start-recording
POST /api/camera/stop-recording
POST /api/ai/start-tracking
POST /api/ai/stop-tracking
```

### Day 25-26: Application Modes
- [ ] Implement 360° rotation sequence
- [ ] Create multi-angle capture mode
- [ ] Add panorama stitching
- [ ] Implement motion time-lapse
- [ ] Create tracking time-lapse
- [ ] Add preset motion sequences
- [ ] Test all application modes

**Deliverables:**
- Multiple application modes
- Automated capture sequences
- Motion presets library

**Application Examples:**
```python
# 360° Product Photography
for angle in range(0, 360, 30):
    platform.move_to(0, 0, 0, 0, 0, angle)
    time.sleep(2)
    camera.capture_image(f"product_{angle:03d}.jpg")

# Motion Time-Lapse
for i in range(100):
    # Slowly pan across scene
    yaw = -30 + (i / 100) * 60
    platform.move_to(0, 0, 0, 0, 0, yaw)
    camera.capture_image(f"timelapse_{i:04d}.jpg")
    time.sleep(5)
```

### Day 27-28: Integration & Testing
- [ ] Test complete system integration
- [ ] Perform long-duration reliability tests
- [ ] Test all safety features
- [ ] Measure system performance
- [ ] Create user documentation
- [ ] Record demonstration videos
- [ ] Prepare deployment guide

**Deliverables:**
- Fully integrated system
- Performance benchmarks
- User documentation
- Demonstration materials

---

## Testing & Validation Checklist

### Hardware Tests
- [ ] All servos respond correctly
- [ ] Camera captures at all resolutions
- [ ] AI accelerator runs models
- [ ] Power system stable under load
- [ ] Cooling adequate for continuous operation
- [ ] Emergency stop works reliably

### Software Tests
- [ ] Inverse kinematics accurate
- [ ] Motion limits enforced
- [ ] Smooth motion trajectories
- [ ] Camera controls responsive
- [ ] AI detection accurate
- [ ] Tracking stable and smooth
- [ ] Web interface responsive

### Integration Tests
- [ ] Coordinated platform and camera motion
- [ ] Auto-framing tracks targets smoothly
- [ ] Time-lapse sequences complete successfully
- [ ] Video recording during motion
- [ ] Multiple application modes work
- [ ] System recovers from errors gracefully

### Performance Tests
- [ ] Motion accuracy: ±0.5mm, ±0.5°
- [ ] Motion speed: 50mm/s, 30°/s
- [ ] AI inference: 30+ FPS
- [ ] Camera capture: <2s for full resolution
- [ ] System latency: <100ms
- [ ] Continuous operation: 8+ hours

---

## Risk Mitigation

### Hardware Risks
**Risk:** Servo overheating during continuous operation  
**Mitigation:** Monitor servo temperatures, add cooling if needed, reduce duty cycle

**Risk:** Power supply insufficient for peak load  
**Mitigation:** Use oversized power supplies, add capacitors for peak current

**Risk:** Mechanical binding or collision  
**Mitigation:** Careful assembly, test full range of motion, implement soft limits

### Software Risks
**Risk:** Kinematics calculation errors  
**Mitigation:** Extensive testing, validation against known poses, gradual motion testing

**Risk:** AI model performance insufficient  
**Mitigation:** Test multiple models, optimize preprocessing, consider model quantization

**Risk:** System instability or crashes  
**Mitigation:** Robust error handling, watchdog timers, automatic recovery

---

## Success Criteria

### Phase 1 Success
- ✅ All hardware components operational
- ✅ Basic servo control working
- ✅ Camera captures images
- ✅ Safety systems functional

### Phase 2 Success
- ✅ Platform moves to commanded positions accurately
- ✅ Smooth motion trajectories
- ✅ All camera modes working
- ✅ System operates safely within limits

### Phase 3 Success
- ✅ AI detection running at 30+ FPS
- ✅ Object tracking stable
- ✅ Auto-framing keeps target centered
- ✅ System responds to moving targets

### Phase 4 Success
- ✅ Web interface fully functional
- ✅ Multiple application modes working
- ✅ System reliable for extended operation
- ✅ Documentation complete

---

## Post-Implementation

### Optimization
- Fine-tune PID parameters for smoother tracking
- Optimize AI model for better performance
- Improve motion planning algorithms
- Add advanced features (focus stacking, HDR, etc.)

### Documentation
- Create video tutorials
- Write troubleshooting guide
- Document common use cases
- Share example projects

### Integration with Suspension Testing
- Synchronize with suspension app data
- Implement multi-camera coordination
- Add automated test sequences
- Create analysis tools

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1 | Hardware setup, basic control |
| Phase 2 | Week 2 | Kinematics, motion planning, camera |
| Phase 3 | Week 3 | AI detection, tracking, auto-framing |
| Phase 4 | Week 4 | Web interface, applications |
| **Total** | **4 weeks** | **Complete system** |

---

## Next Steps (After Hardware Arrival)

1. **Immediate (Day 1):**
   - Unbox and inventory all components
   - Assemble hardware stack
   - Set up power system
   - Initial power-on test

2. **First Week:**
   - Follow Phase 1 roadmap
   - Document any issues or deviations
   - Adjust plans based on actual hardware

3. **Ongoing:**
   - Update this roadmap as needed
   - Track progress in todo.md
   - Document lessons learned
   - Share progress updates

---

**Document Version:** 1.0  
**Created:** 2024  
**Status:** Ready for implementation upon hardware arrival