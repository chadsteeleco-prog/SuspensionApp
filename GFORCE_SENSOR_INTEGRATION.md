# G-Force Sensor Integration - Spatial Awareness Enhancement

## Overview

Adding a 3-axis G-force sensor to the camera platform provides real-time spatial awareness, enabling advanced stabilization, motion compensation, and synchronized data collection with the suspension testing app.

---

## Hardware Addition

### Adafruit ADXL345 Triple-Axis Accelerometer

**Product Link:** https://www.adafruit.com/product/1231

**Specifications:**
- **Sensor:** ADXL345 (Analog Devices)
- **Range:** ±2g, ±4g, ±8g, ±16g (selectable)
- **Resolution:** 13-bit (up to 4mg/LSB)
- **Interface:** I2C or SPI
- **I2C Address:** 0x53 (default) or 0x1D (alternate)
- **Supply Voltage:** 2.0V - 3.6V (3.3V recommended)
- **Logic Voltage:** 3.3V or 5V compatible
- **Current Draw:** 40µA @ 2.5V (measurement mode)
- **Update Rate:** Up to 3200 Hz
- **Dimensions:** 0.8" x 0.6" (20mm x 15mm)
- **Weight:** 1.5g

**Key Features:**
- High resolution 13-bit measurement
- Selectable range for different applications
- Ultra-low power consumption
- Built-in 32-level FIFO buffer
- Interrupt pins for activity detection
- Level shifter for 3.3V/5V compatibility
- Mounting holes for secure attachment

**Why ADXL345:**
✅ Industry-standard sensor with excellent documentation
✅ Open-source, non-proprietary
✅ Wide availability and low cost (~$15)
✅ Proven reliability in robotics applications
✅ Extensive Python library support
✅ Perfect range (±8g) for camera platform

---

## Updated Hardware Stack

```
┌─────────────────────────────────────┐
│  Camera (OwlSight 64MP)             │
│  + G-Force Sensor (mounted nearby)  │  ← Top
└─────────────────────────────────────┘
              ↓ CSI + I2C
┌─────────────────────────────────────┐
│  Raspberry Pi 5 (8GB)               │
│  Powered by UPS                     │
└─────────────────────────────────────┘
         ↓ PCIe          ↓ I2C
┌──────────────┐  ┌──────────────┐
│  AI HAT+     │  │ PWM Servo    │
│  (UPS Power) │  │ Driver HAT   │
└──────────────┘  └──────────────┘
                         ↓ PWM
              ┌──────────────────────┐
              │  Stewart Platform    │
              │  (Battery Power)     │
              └──────────────────────┘
```

---

## Power Architecture Update

### Dual Power System

**System 1: UPS Power (Computing)**
```
UPS Battery Pack
    ↓
5V Regulated Output
    ├─→ Raspberry Pi 5 (5V 5A)
    ├─→ AI HAT+ (5V 2A)
    └─→ G-Force Sensor (3.3V via RPi)
```

**System 2: Battery Power (Servos)**
```
Servo Battery Pack (6V LiPo/NiMH)
    ↓
6V Output (20A capacity)
    ├─→ PWM Servo HAT V+ Terminal
    └─→ 6× 80KG Servos
```

**Benefits:**
- ✅ Isolated power domains (noise reduction)
- ✅ UPS provides clean power for computing
- ✅ Battery handles high servo current spikes
- ✅ Independent shutdown/maintenance
- ✅ Improved reliability

---

## G-Force Sensor Connection

### I2C Connection (Recommended)

**Pin Connections:**
```
ADXL345 Breakout → Raspberry Pi 5
─────────────────────────────────────
VCC (3.3V)        → Pin 1  (3.3V Power)
GND               → Pin 6  (Ground)
SDA               → Pin 3  (GPIO 2 - I2C SDA)
SCL               → Pin 5  (GPIO 3 - I2C SCL)
SDO               → GND (for 0x53 address)
CS                → 3.3V (for I2C mode)
INT1              → Pin 11 (GPIO 17) [Optional]
INT2              → Pin 13 (GPIO 27) [Optional]
```

**I2C Bus Sharing:**
- PWM Servo HAT: Address 0x40
- ADXL345 Sensor: Address 0x53 (SDO→GND) or 0x1D (SDO→3.3V)
- Both devices can coexist on same I2C bus

**Address Selection:**
- Connect SDO to GND for address 0x53 (recommended)
- Connect SDO to 3.3V for address 0x1D (if 0x53 conflicts)

### Mounting Location

**Option 1: Camera Mount (Recommended)**
- Mount sensor directly on camera platform
- Measures actual camera movement
- Best for image stabilization

**Option 2: Base Mount**
- Mount on Stewart platform base
- Measures platform motion
- Good for motion validation

**Option 3: Dual Sensor Setup**
- One on camera, one on base
- Differential measurement
- Most accurate motion tracking

---

## Software Integration

### Python Driver Implementation

```python
"""
G-Force Sensor Driver
Provides real-time acceleration and orientation data.
"""

import smbus2
import time
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class GForceSensor:
    """
    3-axis G-force sensor interface.
    
    Supports ADXL345 and similar I2C accelerometers.
    """
    
    # ADXL345 Registers
    POWER_CTL = 0x2D
    DATA_FORMAT = 0x31
    DATAX0 = 0x32
    
    # Configuration
    RANGE_8G = 0x02
    MEASURE_MODE = 0x08
    
    def __init__(self, bus_number: int = 1, address: int = 0x53):
        """
        Initialize G-force sensor.
        
        Args:
            bus_number: I2C bus number (1 for Raspberry Pi)
            address: I2C device address (0x53 for ADXL345)
        """
        self.bus = smbus2.SMBus(bus_number)
        self.address = address
        
        # Initialize sensor
        self._initialize()
        
        # Calibration offsets
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0
        
        # Scale factor (for ±8G range)
        self.scale = 0.004  # 4mg per LSB
        
        logger.info(f"G-Force sensor initialized at 0x{address:02X}")
    
    def _initialize(self):
        """Configure sensor for measurement"""
        # Set range to ±8G
        self.bus.write_byte_data(self.address, self.DATA_FORMAT, self.RANGE_8G)
        
        # Enable measurement mode
        self.bus.write_byte_data(self.address, self.POWER_CTL, self.MEASURE_MODE)
        
        time.sleep(0.1)
    
    def read_raw(self) -> Tuple[int, int, int]:
        """Read raw acceleration values"""
        # Read 6 bytes starting from DATAX0
        data = self.bus.read_i2c_block_data(self.address, self.DATAX0, 6)
        
        # Convert to signed 16-bit integers
        x = np.int16((data[1] << 8) | data[0])
        y = np.int16((data[3] << 8) | data[2])
        z = np.int16((data[5] << 8) | data[4])
        
        return (x, y, z)
    
    def read_g_force(self) -> Tuple[float, float, float]:
        """
        Read acceleration in G-forces.
        
        Returns:
            Tuple of (x, y, z) acceleration in G
        """
        x_raw, y_raw, z_raw = self.read_raw()
        
        # Convert to G-forces and apply calibration
        x_g = (x_raw * self.scale) - self.offset_x
        y_g = (y_raw * self.scale) - self.offset_y
        z_g = (z_raw * self.scale) - self.offset_z
        
        return (x_g, y_g, z_g)
    
    def read_orientation(self) -> Dict[str, float]:
        """
        Calculate orientation from acceleration.
        
        Returns:
            Dictionary with roll and pitch in degrees
        """
        x_g, y_g, z_g = self.read_g_force()
        
        # Calculate roll and pitch
        roll = np.arctan2(y_g, z_g) * 180 / np.pi
        pitch = np.arctan2(-x_g, np.sqrt(y_g**2 + z_g**2)) * 180 / np.pi
        
        return {
            'roll': roll,
            'pitch': pitch,
            'x_g': x_g,
            'y_g': y_g,
            'z_g': z_g
        }
    
    def calibrate(self, samples: int = 100):
        """
        Calibrate sensor (must be level and stationary).
        
        Args:
            samples: Number of samples to average
        """
        logger.info("Calibrating G-force sensor...")
        
        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        
        for _ in range(samples):
            x_raw, y_raw, z_raw = self.read_raw()
            x_sum += x_raw * self.scale
            y_sum += y_raw * self.scale
            z_sum += z_raw * self.scale
            time.sleep(0.01)
        
        # Calculate offsets (Z should read 1G when level)
        self.offset_x = x_sum / samples
        self.offset_y = y_sum / samples
        self.offset_z = (z_sum / samples) - 1.0
        
        logger.info(f"Calibration complete: X={self.offset_x:.3f}G, "
                   f"Y={self.offset_y:.3f}G, Z={self.offset_z:.3f}G")
    
    def get_magnitude(self) -> float:
        """Calculate total acceleration magnitude"""
        x_g, y_g, z_g = self.read_g_force()
        return np.sqrt(x_g**2 + y_g**2 + z_g**2)


class MotionStabilizer:
    """
    Motion stabilization using G-force sensor feedback.
    
    Compensates for platform vibration and movement.
    """
    
    def __init__(self, sensor: GForceSensor, stewart_platform):
        self.sensor = sensor
        self.platform = stewart_platform
        
        # Stabilization parameters
        self.enable_stabilization = False
        self.compensation_gain = 0.5
        
        # Motion history for filtering
        self.history_size = 10
        self.x_history = []
        self.y_history = []
        self.z_history = []
        
        logger.info("Motion stabilizer initialized")
    
    def update(self):
        """
        Update stabilization compensation.
        
        Call this in a loop for continuous stabilization.
        """
        if not self.enable_stabilization:
            return
        
        # Read current acceleration
        x_g, y_g, z_g = self.sensor.read_g_force()
        
        # Add to history
        self.x_history.append(x_g)
        self.y_history.append(y_g)
        self.z_history.append(z_g)
        
        # Keep history size limited
        if len(self.x_history) > self.history_size:
            self.x_history.pop(0)
            self.y_history.pop(0)
            self.z_history.pop(0)
        
        # Calculate filtered values
        x_filtered = np.mean(self.x_history)
        y_filtered = np.mean(self.y_history)
        
        # Calculate compensation (convert G to platform motion)
        # This is a simplified model - tune for your system
        roll_compensation = -y_filtered * self.compensation_gain
        pitch_compensation = x_filtered * self.compensation_gain
        
        # Apply compensation
        try:
            self.platform.move_relative(
                droll=roll_compensation,
                dpitch=pitch_compensation,
                duration=0.05
            )
        except Exception as e:
            logger.warning(f"Stabilization adjustment failed: {e}")
    
    def enable(self):
        """Enable stabilization"""
        self.enable_stabilization = True
        logger.info("Motion stabilization enabled")
    
    def disable(self):
        """Disable stabilization"""
        self.enable_stabilization = False
        logger.info("Motion stabilization disabled")


if __name__ == "__main__":
    # Test script
    print("G-Force Sensor Test")
    print("=" * 50)
    
    # Initialize sensor
    sensor = GForceSensor()
    
    # Calibrate
    print("\nCalibrating... (keep sensor level and still)")
    sensor.calibrate()
    
    # Read data
    print("\nReading G-force data (10 samples):")
    for i in range(10):
        orientation = sensor.read_orientation()
        print(f"Sample {i+1}: "
              f"X={orientation['x_g']:+.3f}G, "
              f"Y={orientation['y_g']:+.3f}G, "
              f"Z={orientation['z_g']:+.3f}G, "
              f"Roll={orientation['roll']:+.1f}°, "
              f"Pitch={orientation['pitch']:+.1f}°")
        time.sleep(0.5)
    
    print("\nTest complete!")
```

---

## Enhanced Features with G-Force Sensor

### 1. Motion Stabilization
```python
from gforce_sensor import GForceSensor, MotionStabilizer
from stewart_platform import StewartPlatform

# Initialize
sensor = GForceSensor()
platform = StewartPlatform()
stabilizer = MotionStabilizer(sensor, platform)

# Enable stabilization
stabilizer.enable()

# Stabilization runs in background
while True:
    stabilizer.update()
    time.sleep(0.01)  # 100Hz update rate
```

### 2. Vibration Monitoring
```python
def monitor_vibration(sensor, duration=10):
    """Monitor platform vibration"""
    samples = []
    
    for _ in range(int(duration * 100)):  # 100Hz
        magnitude = sensor.get_magnitude()
        samples.append(magnitude)
        time.sleep(0.01)
    
    # Calculate statistics
    mean_g = np.mean(samples)
    std_g = np.std(samples)
    max_g = np.max(samples)
    
    print(f"Vibration Analysis:")
    print(f"  Mean: {mean_g:.3f}G")
    print(f"  Std Dev: {std_g:.3f}G")
    print(f"  Max: {max_g:.3f}G")
    
    return samples
```

### 3. Motion Validation
```python
def validate_motion(sensor, platform, target_pose):
    """Verify platform reached target position"""
    # Command motion
    platform.move_to(*target_pose)
    
    # Wait for settling
    time.sleep(2)
    
    # Read actual orientation
    actual = sensor.read_orientation()
    
    # Compare with target
    roll_error = abs(actual['roll'] - target_pose[3])
    pitch_error = abs(actual['pitch'] - target_pose[4])
    
    print(f"Motion Validation:")
    print(f"  Roll Error: {roll_error:.2f}°")
    print(f"  Pitch Error: {pitch_error:.2f}°")
    
    return roll_error < 1.0 and pitch_error < 1.0
```

### 4. Synchronized Data Collection
```python
class SynchronizedCapture:
    """Capture images with synchronized G-force data"""
    
    def __init__(self, camera, sensor):
        self.camera = camera
        self.sensor = sensor
    
    def capture_with_metadata(self, filename):
        """Capture image with G-force metadata"""
        # Read G-force at capture moment
        orientation = self.sensor.read_orientation()
        
        # Capture image
        image_path = self.camera.capture_image(filename)
        
        # Save metadata
        metadata = {
            'timestamp': time.time(),
            'x_g': orientation['x_g'],
            'y_g': orientation['y_g'],
            'z_g': orientation['z_g'],
            'roll': orientation['roll'],
            'pitch': orientation['pitch'],
            'image_path': image_path
        }
        
        # Save to JSON
        metadata_path = image_path.replace('.jpg', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return image_path, metadata
```

### 5. Integration with Suspension App
```python
class SuspensionTestSync:
    """Synchronize camera platform with suspension testing"""
    
    def __init__(self, camera, sensor, platform):
        self.camera = camera
        self.sensor = sensor
        self.platform = platform
        
        # Data buffers
        self.gforce_data = []
        self.timestamps = []
    
    def start_test(self, duration):
        """Start synchronized test recording"""
        start_time = time.time()
        
        # Start video recording
        self.camera.start_video_recording()
        
        # Collect G-force data
        while time.time() - start_time < duration:
            timestamp = time.time() - start_time
            orientation = self.sensor.read_orientation()
            
            self.timestamps.append(timestamp)
            self.gforce_data.append(orientation)
            
            time.sleep(0.01)  # 100Hz sampling
        
        # Stop recording
        self.camera.stop_video_recording()
        
        # Save G-force data
        self.save_gforce_data()
    
    def save_gforce_data(self):
        """Save G-force data to CSV"""
        import csv
        
        with open('gforce_data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'X_G', 'Y_G', 'Z_G', 'Roll', 'Pitch'])
            
            for t, data in zip(self.timestamps, self.gforce_data):
                writer.writerow([
                    t,
                    data['x_g'],
                    data['y_g'],
                    data['z_g'],
                    data['roll'],
                    data['pitch']
                ])
```

---

## Updated Web API

### New Endpoints

```python
@app.route('/api/sensor/gforce', methods=['GET'])
def get_gforce():
    """Get current G-force reading"""
    if sensor is None:
        return jsonify({'error': 'Sensor not available'}), 500
    
    orientation = sensor.read_orientation()
    return jsonify(orientation)

@app.route('/api/sensor/calibrate', methods=['POST'])
def calibrate_sensor():
    """Calibrate G-force sensor"""
    if sensor is None:
        return jsonify({'error': 'Sensor not available'}), 500
    
    try:
        sensor.calibrate()
        return jsonify({'status': 'calibrated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stabilization/enable', methods=['POST'])
def enable_stabilization():
    """Enable motion stabilization"""
    if stabilizer is None:
        return jsonify({'error': 'Stabilizer not available'}), 500
    
    stabilizer.enable()
    return jsonify({'status': 'enabled'})

@app.route('/api/stabilization/disable', methods=['POST'])
def disable_stabilization():
    """Disable motion stabilization"""
    if stabilizer is None:
        return jsonify({'error': 'Stabilizer not available'}), 500
    
    stabilizer.disable()
    return jsonify({'status': 'disabled'})
```

---

## Hardware Shopping List Update

### Additional Components Needed

| Item | Quantity | Estimated Cost | Link |
|------|----------|----------------|------|
| **Adafruit ADXL345** | 1 | $14.95 | [Adafruit #1231](https://www.adafruit.com/product/1231) |
| **UPS Power Supply** (5V 10A) | 1 | $40-60 | Various |
| **Servo Battery Pack** (6V 20A LiPo/NiMH) | 1 | $30-50 | Various |
| **Battery Charger** | 1 | $20-30 | Various |
| **Power Cables & Connectors** | Set | $15-20 | Various |
| **Mounting Hardware** (M2.5 screws) | 1 | $5-10 | Various |

**Total Additional Cost:** ~$125-185

**Where to Buy:**
- **ADXL345:** Adafruit, SparkFun, Amazon, DigiKey
- **UPS:** Amazon, Adafruit (PowerBoost series)
- **Battery Pack:** HobbyKing, Amazon, local hobby stores
- **Charger:** Matched to battery chemistry (LiPo/NiMH)

---

## Benefits of G-Force Sensor Integration

### Immediate Benefits
✅ **Real-time spatial awareness** - Know exact platform orientation
✅ **Motion validation** - Verify commanded vs actual position
✅ **Vibration monitoring** - Detect and quantify vibrations
✅ **Data synchronization** - Correlate images with motion data

### Advanced Features
✅ **Active stabilization** - Compensate for external disturbances
✅ **Motion compensation** - Improve image quality during movement
✅ **Predictive control** - Anticipate and correct motion errors
✅ **Safety enhancement** - Detect abnormal accelerations

### Integration with Suspension App
✅ **Dual G-force measurement** - Phone + platform sensors
✅ **Multi-angle correlation** - Visual + sensor data fusion
✅ **Enhanced analysis** - 3D motion reconstruction
✅ **Comprehensive reports** - Combined visual and sensor data

---

## Installation & Calibration

### Hardware Installation
1. Mount sensor on camera platform (near camera)
2. Connect to Raspberry Pi I2C bus
3. Secure wiring to prevent interference
4. Verify I2C detection: `sudo i2cdetect -y 1`

### Software Installation
```bash
# Install Python I2C library
pip install smbus2

# Copy sensor driver
cp gforce_sensor.py ~/camera_platform/src/

# Test sensor
python ~/camera_platform/src/gforce_sensor.py
```

### Calibration Procedure
1. Place platform on level surface
2. Ensure platform is stationary
3. Run calibration: `python calibrate_gforce.py`
4. Verify readings: X≈0G, Y≈0G, Z≈1G

---

## Performance Impact

### Computational Overhead
- **CPU Usage:** <1% (I2C reads are fast)
- **Memory:** <1MB (minimal data buffering)
- **Latency:** <1ms per reading
- **Update Rate:** 100Hz typical

### System Integration
- **No impact** on camera performance
- **No impact** on AI processing
- **Minimal impact** on motion control (if stabilization disabled)
- **Slight improvement** in motion accuracy (with stabilization)

---

## Future Enhancements

### Advanced Stabilization
- Kalman filtering for sensor fusion
- Predictive motion compensation
- Adaptive gain control
- Multi-sensor fusion (camera + platform)

### Machine Learning
- Learn vibration patterns
- Predict optimal stabilization
- Anomaly detection
- Automated tuning

### Data Analytics
- Motion quality metrics
- Vibration frequency analysis
- Performance benchmarking
- Automated reporting

---

## Conclusion

Adding a G-force sensor significantly enhances the camera platform's capabilities:

1. **Spatial Awareness** - Know exact orientation at all times
2. **Motion Validation** - Verify platform accuracy
3. **Active Stabilization** - Compensate for disturbances
4. **Data Synchronization** - Correlate visual and motion data
5. **Suspension Integration** - Enhanced testing capabilities

**Recommendation:** Use **ADXL345** or **MPU-6050** for best value and performance.

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Status:** Ready for implementation with hardware arrival