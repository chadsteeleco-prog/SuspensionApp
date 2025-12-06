# Sensor Comparison: ADXL345 vs BNO055

## Quick Recommendation

**For Camera Platform: BNO055** ⭐

The extra $20 investment provides professional-grade results with absolute orientation, no drift, and automatic calibration.

---

## Detailed Comparison

### Hardware Specifications

| Feature | ADXL345 | BNO055 | Winner |
|---------|---------|---------|--------|
| **Sensors** | 3-axis accelerometer | 9-axis (accel + gyro + mag) | **BNO055** 🏆 |
| **Processor** | None (external processing) | ARM Cortex-M0 | **BNO055** 🏆 |
| **Accelerometer Range** | ±2/4/8/16g | ±2/4/8/16g | Tie |
| **Gyroscope** | None | ±125 to ±2000°/s | **BNO055** 🏆 |
| **Magnetometer** | None | ±1300µT | **BNO055** 🏆 |
| **Resolution** | 13-bit (4mg/LSB) | 14-bit | **BNO055** 🏆 |
| **Update Rate** | 3200 Hz | 100 Hz | ADXL345 |
| **Power Consumption** | 40µA | 12.3mA | ADXL345 |
| **Size** | 20×15mm | 23×18mm | ADXL345 |
| **Weight** | 1.5g | 2g | ADXL345 |
| **Cost** | $14.95 | $34.95 | ADXL345 |

### Software Features

| Feature | ADXL345 | BNO055 | Winner |
|---------|---------|---------|--------|
| **Output Format** | Raw acceleration | Quaternions, Euler angles, vectors | **BNO055** 🏆 |
| **Sensor Fusion** | External (you code it) | Built-in (automatic) | **BNO055** 🏆 |
| **Calibration** | Manual offset adjustment | Automatic self-calibration | **BNO055** 🏆 |
| **Drift** | Accumulates over time | Self-correcting (no drift) | **BNO055** 🏆 |
| **Orientation Accuracy** | ±0.5° (relative) | ±1° (absolute) | **BNO055** 🏆 |
| **CPU Load** | High (sensor fusion on Pi) | Low (fusion on-chip) | **BNO055** 🏆 |
| **Setup Complexity** | Simple | Moderate | ADXL345 |
| **Library Support** | Excellent | Excellent | Tie |

### Camera Platform Use Cases

| Use Case | ADXL345 | BNO055 | Winner |
|----------|---------|---------|--------|
| **Motion Stabilization** | Basic (tilt only) | Advanced (full 3D) | **BNO055** 🏆 |
| **Time-Lapse** | Drift over time | No drift | **BNO055** 🏆 |
| **Auto-Framing** | Limited accuracy | High accuracy | **BNO055** 🏆 |
| **Outdoor Use** | No compass | True heading | **BNO055** 🏆 |
| **Long Duration** | Drift accumulates | Stable | **BNO055** 🏆 |
| **High-Speed Sampling** | 3200 Hz capable | 100 Hz max | ADXL345 |
| **Battery Life** | Excellent | Good | ADXL345 |
| **Quick Prototyping** | Very easy | Easy | ADXL345 |

---

## Detailed Analysis

### 1. Orientation Accuracy

**ADXL345:**
- Measures tilt relative to gravity
- No absolute reference
- Drift accumulates over time
- Requires external sensor fusion
- ±0.5° accuracy (short term)

**BNO055:**
- Absolute orientation in 3D space
- Magnetometer provides absolute reference
- Self-correcting (no drift)
- Built-in sensor fusion
- ±1° accuracy (absolute, long term)

**Winner: BNO055** - Absolute orientation is critical for camera platform

### 2. Sensor Fusion

**ADXL345:**
```python
# You must implement sensor fusion
def calculate_orientation(accel_data):
    # Complex math required
    roll = atan2(accel_y, accel_z)
    pitch = atan2(-accel_x, sqrt(accel_y^2 + accel_z^2))
    # No yaw without magnetometer
    # Drift correction needed
    # Kalman filter implementation
    return roll, pitch
```

**BNO055:**
```python
# Sensor fusion done automatically
orientation = sensor.read_euler()
# Returns: heading, roll, pitch
# All fusion handled by on-chip processor
# No drift, no complex math needed
```

**Winner: BNO055** - Saves development time and CPU resources

### 3. Calibration

**ADXL345:**
- Manual calibration required
- Must be perfectly level
- Offsets stored in software
- Recalibration needed periodically
- Temperature drift possible

**BNO055:**
- Automatic self-calibration
- Move sensor in figure-8 pattern
- Calibration stored on-chip
- Maintains calibration over time
- Temperature compensated

**Winner: BNO055** - Much easier to use

### 4. Drift Over Time

**ADXL345:**
```
Time:     0min   30min   60min   120min
Accuracy: ±0.5°  ±1.0°   ±2.0°   ±5.0°
```
Drift accumulates, especially without gyroscope

**BNO055:**
```
Time:     0min   30min   60min   120min
Accuracy: ±1.0°  ±1.0°   ±1.0°   ±1.0°
```
No drift - magnetometer provides absolute reference

**Winner: BNO055** - Critical for time-lapse photography

### 5. CPU Load

**ADXL345:**
- Raw data processing on Raspberry Pi
- Sensor fusion algorithms needed
- Kalman filtering required
- ~10-20% CPU usage for fusion
- Impacts other tasks

**BNO055:**
- All processing on-chip
- Raspberry Pi just reads results
- <1% CPU usage
- More resources for AI and camera

**Winner: BNO055** - Frees up CPU for other tasks

### 6. Power Consumption

**ADXL345:**
- 40µA measurement mode
- Ultra-low power
- Excellent for battery operation
- Can run for months on coin cell

**BNO055:**
- 12.3mA typical
- 300× more power than ADXL345
- Still very reasonable
- ~1 day on 2500mAh battery

**Winner: ADXL345** - But BNO055 is still acceptable

### 7. Update Rate

**ADXL345:**
- Up to 3200 Hz
- Excellent for high-speed applications
- Vibration analysis
- Impact detection

**BNO055:**
- 100 Hz maximum
- Sufficient for camera platform
- More than adequate for stabilization
- Matches typical camera frame rates

**Winner: ADXL345** - But 100Hz is plenty for this application

---

## Cost-Benefit Analysis

### ADXL345 ($14.95)

**Pros:**
- ✅ Lower cost
- ✅ Ultra-low power
- ✅ High update rate
- ✅ Simple hardware
- ✅ Small size

**Cons:**
- ❌ No gyroscope
- ❌ No magnetometer
- ❌ Drift over time
- ❌ Manual calibration
- ❌ Complex software
- ❌ High CPU load
- ❌ Relative orientation only

**Best For:**
- Budget builds
- Battery-powered applications
- High-speed sampling needs
- Simple tilt sensing
- Learning projects

### BNO055 ($34.95)

**Pros:**
- ✅ 9-axis sensor
- ✅ Absolute orientation
- ✅ No drift
- ✅ Automatic calibration
- ✅ Built-in sensor fusion
- ✅ Low CPU load
- ✅ Quaternion output
- ✅ Magnetometer (compass)
- ✅ Professional results

**Cons:**
- ❌ Higher cost (+$20)
- ❌ Higher power consumption
- ❌ Lower update rate
- ❌ Slightly larger

**Best For:**
- Professional camera platforms
- Time-lapse photography
- Motion stabilization
- Outdoor use (compass)
- Long-duration operation
- Production systems

---

## Real-World Scenarios

### Scenario 1: 2-Hour Time-Lapse

**ADXL345:**
- Starts accurate
- Drifts 2-5° over 2 hours
- Platform orientation changes
- Images not aligned
- Post-processing needed

**BNO055:**
- Maintains ±1° accuracy
- No drift over time
- Perfect alignment
- No post-processing
- Professional results

**Winner: BNO055**

### Scenario 2: Motion Stabilization

**ADXL345:**
- Can detect tilt
- No rotation rate data
- Limited stabilization
- Lag in response
- Vibration issues

**BNO055:**
- Full 3D orientation
- Gyroscope for fast response
- Excellent stabilization
- Smooth motion
- Vibration filtered

**Winner: BNO055**

### Scenario 3: Outdoor Panorama

**ADXL345:**
- No compass heading
- Relative positioning only
- Difficult to align shots
- Manual orientation needed

**BNO055:**
- True compass heading
- Absolute positioning
- Perfect shot alignment
- Automatic orientation

**Winner: BNO055**

### Scenario 4: Battery-Powered Remote Camera

**ADXL345:**
- 40µA power draw
- Months of operation
- Excellent battery life

**BNO055:**
- 12.3mA power draw
- Days of operation
- Still acceptable

**Winner: ADXL345** (but BNO055 still viable with proper battery)

---

## Recommendation Matrix

| Your Priority | Recommended Sensor |
|---------------|-------------------|
| **Best Results** | BNO055 ⭐ |
| **Professional Use** | BNO055 ⭐ |
| **Time-Lapse** | BNO055 ⭐ |
| **Motion Stabilization** | BNO055 ⭐ |
| **Outdoor Use** | BNO055 ⭐ |
| **Long Duration** | BNO055 ⭐ |
| **Ease of Use** | BNO055 ⭐ |
| **Lowest Cost** | ADXL345 |
| **Battery Life** | ADXL345 |
| **High-Speed Sampling** | ADXL345 |
| **Learning/Prototyping** | ADXL345 |

---

## Final Verdict

### For Camera Platform: **BNO055** ⭐

**Why:**
1. **No Drift** - Critical for time-lapse and long operations
2. **Absolute Orientation** - Know exact position at all times
3. **Automatic Calibration** - Less maintenance, more reliable
4. **Better Stabilization** - Gyroscope enables smooth motion
5. **Compass Heading** - Useful for outdoor panoramas
6. **Less CPU Load** - More resources for AI and camera
7. **Professional Results** - Worth the extra $20

**The $20 difference is negligible compared to:**
- Time saved on software development
- Better results and reliability
- Professional-grade performance
- Future capabilities (compass, etc.)

### When to Choose ADXL345:

Only if:
- Budget is extremely tight (< $100 total)
- Battery life is critical (months on coin cell)
- High-speed sampling needed (>100Hz)
- Learning/educational project
- Simple tilt sensing sufficient

---

## Migration Path

**Start with ADXL345:**
- Good for prototyping
- Learn the basics
- Test your application
- Upgrade later if needed

**Upgrade to BNO055:**
- Drop-in replacement (similar I2C interface)
- Simpler code (less sensor fusion)
- Better results immediately
- Professional-grade system

**Both sensors supported in our codebase!**

---

## Conclusion

For a **professional camera platform** with Stewart platform control, the **BNO055 is the clear winner**. The extra $20 investment provides:

- ✅ Absolute orientation (no drift)
- ✅ Automatic calibration
- ✅ Better accuracy
- ✅ Easier software
- ✅ Professional results

The ADXL345 is excellent for budget builds and learning, but the BNO055 is the sensor used in professional drones, VR systems, and robotics for good reason - **it just works better**.

**Recommendation: Invest in the BNO055 ($34.95)** ⭐

---

**Last Updated:** 2024  
**Recommendation:** BNO055 for camera platform  
**Budget Alternative:** ADXL345 for learning/prototyping