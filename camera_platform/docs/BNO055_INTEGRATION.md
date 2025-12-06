# BNO055 9-DOF Absolute Orientation IMU Integration Guide

## Hardware: Adafruit BNO055 Absolute Orientation Sensor

**Product:** https://www.adafruit.com/product/2472

### Specifications

| Feature | Specification |
|---------|--------------|
| **Sensor** | Bosch BNO055 9-DOF IMU |
| **Accelerometer** | ±2g/±4g/±8g/±16g (selectable) |
| **Gyroscope** | ±125°/±250°/±500°/±1000°/±2000°/s |
| **Magnetometer** | ±1300µT (X,Y), ±2500µT (Z) |
| **Processor** | ARM Cortex-M0 (sensor fusion) |
| **Interface** | I2C or UART |
| **I2C Address** | 0x28 (default) or 0x29 (alternate) |
| **Supply Voltage** | 3.3V or 5V |
| **Current Draw** | 12.3mA typical |
| **Update Rate** | 100 Hz |
| **Orientation Accuracy** | ±1° (absolute) |
| **Dimensions** | 0.9" x 0.7" (23mm x 18mm) |
| **Weight** | 2g |

### Key Features

✅ **9-DOF Sensor Fusion** - Accelerometer + Gyroscope + Magnetometer
✅ **Absolute Orientation** - No drift, self-correcting
✅ **Built-in Processing** - ARM Cortex-M0 does sensor fusion
✅ **Multiple Output Formats** - Quaternions, Euler angles, vectors
✅ **Automatic Calibration** - Self-calibrating system
✅ **Temperature Compensation** - Built-in temperature sensor
✅ **Low Latency** - <10ms processing time
✅ **Mounting Holes** - Easy mechanical attachment

### Why BNO055 Over ADXL345

| Advantage | Benefit for Camera Platform |
|-----------|----------------------------|
| **Absolute Orientation** | No drift during long time-lapses |
| **Sensor Fusion** | Less CPU load on Raspberry Pi |
| **Magnetometer** | True heading/compass capability |
| **Auto-Calibration** | Easier setup and maintenance |
| **Better Accuracy** | ±1° vs ±0.5° orientation |
| **Self-Correcting** | Reliable long-term operation |

**Cost Difference:** +$20 ($34.95 vs $14.95)
**Verdict:** **Worth it!** Professional-grade results for minimal extra cost.

---

## Wiring Diagram

### I2C Connection (Recommended)

```
BNO055 Breakout → Raspberry Pi 5
─────────────────────────────────────
VIN (3.3V or 5V)  → Pin 1  (3.3V Power)
GND               → Pin 6  (Ground)
SDA               → Pin 3  (GPIO 2 - I2C SDA)
SCL               → Pin 5  (GPIO 3 - I2C SCL)
RST               → Pin 11 (GPIO 17) [Optional]
PS0               → GND (for I2C mode)
PS1               → 3.3V (for I2C mode)
INT               → Pin 13 (GPIO 27) [Optional]
```

### Detailed Pin Functions

| Pin | Function | Connection |
|-----|----------|------------|
| **VIN** | Power Supply | 3.3V (Pin 1) or 5V (Pin 2) |
| **GND** | Ground | GND (Pin 6) |
| **SDA** | I2C Data | GPIO 2 (Pin 3) |
| **SCL** | I2C Clock | GPIO 3 (Pin 5) |
| **RST** | Reset | GPIO 17 (optional, or 3.3V) |
| **PS0** | Protocol Select 0 | GND for I2C |
| **PS1** | Protocol Select 1 | 3.3V for I2C |
| **INT** | Interrupt | GPIO 27 (optional) |
| **ADR** | I2C Address Select | GND = 0x28, 3.3V = 0x29 |

### Physical Mounting

**Recommended Location:** Mount on camera platform near camera

**Orientation:**
```
     ┌─────────────┐
     │   BNO055    │
     │             │
     │      ↑ +Y   │  ← Forward (camera direction)
     │      │      │
     │  +X ←┼→     │  ← Right
     │      │      │
     │      ↓      │
     │    +Z down  │  ← Down (into board)
     └─────────────┘
```

**Important:** BNO055 Z-axis points DOWN (opposite of ADXL345)

**Mounting Options:**
1. **Screw Mount** - Use mounting holes (M2.5 screws) - Recommended
2. **Adhesive Mount** - Double-sided foam tape
3. **3D Printed Bracket** - Custom mount for camera platform

**Critical:**
- Mount rigidly to minimize vibration
- Keep away from magnetic interference (motors, speakers)
- Align axes with camera/platform orientation
- Allow clearance for calibration movements

---

## Software Configuration

### I2C Address Selection

| ADR Pin | I2C Address | Hex |
|---------|-------------|-----|
| GND | 40 (decimal) | 0x28 |
| 3.3V | 41 (decimal) | 0x29 |

**Default Configuration:** ADR → GND (Address 0x28)

### Operation Modes

The BNO055 has multiple operation modes:

| Mode | Sensors Active | Fusion | Use Case |
|------|---------------|--------|----------|
| **CONFIG** | None | No | Configuration only |
| **ACCONLY** | Accelerometer | No | Basic tilt |
| **MAGONLY** | Magnetometer | No | Compass only |
| **GYROONLY** | Gyroscope | No | Rotation rate |
| **ACCMAG** | Accel + Mag | No | Tilt + compass |
| **ACCGYRO** | Accel + Gyro | No | Tilt + rotation |
| **MAGGYRO** | Mag + Gyro | No | Compass + rotation |
| **AMG** | All three | No | Raw data |
| **IMU** | Accel + Gyro | Yes | Relative orientation |
| **COMPASS** | Accel + Mag | Yes | Absolute heading |
| **M4G** | Accel + Mag | Yes | Rotation vector |
| **NDOF_FMC_OFF** | All three | Yes | Fast magnetometer cal |
| **NDOF** | All three | Yes | **Recommended - Full fusion** |

**Recommended:** NDOF mode for camera platform (full 9-DOF fusion)

---

## Python Driver Implementation

### Complete BNO055 Driver

```python
"""
BNO055 9-DOF Absolute Orientation IMU Driver
Optimized for Adafruit BNO055 breakout board
"""

import smbus2
import time
import struct
import numpy as np
from typing import Tuple, Dict, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BNO055:
    """
    BNO055 9-DOF Absolute Orientation IMU Driver
    
    Provides:
    - Absolute orientation (no drift)
    - Quaternion output
    - Euler angles (roll, pitch, yaw)
    - Linear acceleration
    - Gravity vector
    - Automatic calibration
    """
    
    # I2C Addresses
    ADDRESS_A = 0x28
    ADDRESS_B = 0x29
    
    # Register Map
    REG_CHIP_ID = 0x00
    REG_PAGE_ID = 0x07
    REG_ACCEL_DATA = 0x08
    REG_MAG_DATA = 0x0E
    REG_GYRO_DATA = 0x14
    REG_EULER_H = 0x1A
    REG_QUAT_W = 0x20
    REG_LINEAR_ACCEL = 0x28
    REG_GRAVITY = 0x2E
    REG_TEMP = 0x34
    REG_CALIB_STAT = 0x35
    REG_SYS_STATUS = 0x39
    REG_SYS_ERR = 0x3A
    REG_UNIT_SEL = 0x3B
    REG_OPR_MODE = 0x3D
    REG_PWR_MODE = 0x3E
    REG_SYS_TRIGGER = 0x3F
    REG_AXIS_MAP_CONFIG = 0x41
    REG_AXIS_MAP_SIGN = 0x42
    
    # Operation Modes
    MODE_CONFIG = 0x00
    MODE_ACCONLY = 0x01
    MODE_MAGONLY = 0x02
    MODE_GYROONLY = 0x03
    MODE_ACCMAG = 0x04
    MODE_ACCGYRO = 0x05
    MODE_MAGGYRO = 0x06
    MODE_AMG = 0x07
    MODE_IMU = 0x08
    MODE_COMPASS = 0x09
    MODE_M4G = 0x0A
    MODE_NDOF_FMC_OFF = 0x0B
    MODE_NDOF = 0x0C
    
    # Power Modes
    POWER_MODE_NORMAL = 0x00
    POWER_MODE_LOW = 0x01
    POWER_MODE_SUSPEND = 0x02
    
    def __init__(self, bus_number: int = 1, address: int = ADDRESS_A):
        """
        Initialize BNO055 IMU.
        
        Args:
            bus_number: I2C bus number (1 for Raspberry Pi)
            address: I2C device address (0x28 or 0x29)
        """
        self.bus = smbus2.SMBus(bus_number)
        self.address = address
        
        # Verify device
        if not self._verify_device():
            raise RuntimeError(f"BNO055 not found at address 0x{address:02X}")
        
        # Initialize sensor
        self._initialize()
        
        # Calibration status
        self.calibration_status = {'sys': 0, 'gyro': 0, 'accel': 0, 'mag': 0}
        
        logger.info(f"BNO055 initialized at 0x{address:02X}")
    
    def _verify_device(self) -> bool:
        """Verify BNO055 is present"""
        try:
            chip_id = self.bus.read_byte_data(self.address, self.REG_CHIP_ID)
            return chip_id == 0xA0
        except Exception as e:
            logger.error(f"Device verification failed: {e}")
            return False
    
    def _initialize(self):
        """Configure BNO055 for operation"""
        # Reset
        self.bus.write_byte_data(self.address, self.REG_SYS_TRIGGER, 0x20)
        time.sleep(0.7)  # Wait for reset
        
        # Set to config mode
        self._set_mode(self.MODE_CONFIG)
        
        # Set power mode to normal
        self.bus.write_byte_data(self.address, self.REG_PWR_MODE, self.POWER_MODE_NORMAL)
        
        # Set page 0
        self.bus.write_byte_data(self.address, self.REG_PAGE_ID, 0x00)
        
        # Set units (m/s², degrees, Celsius)
        self.bus.write_byte_data(self.address, self.REG_UNIT_SEL, 0x00)
        
        # Set to NDOF mode (full fusion)
        self._set_mode(self.MODE_NDOF)
        
        time.sleep(0.1)
    
    def _set_mode(self, mode: int):
        """Set operation mode"""
        self.bus.write_byte_data(self.address, self.REG_OPR_MODE, mode)
        time.sleep(0.03)  # Mode switch delay
    
    def _read_vector(self, reg: int, scale: float = 1.0) -> Tuple[float, float, float]:
        """Read 3-axis vector data"""
        try:
            data = self.bus.read_i2c_block_data(self.address, reg, 6)
            
            x = struct.unpack('<h', bytes(data[0:2]))[0] * scale
            y = struct.unpack('<h', bytes(data[2:4]))[0] * scale
            z = struct.unpack('<h', bytes(data[4:6]))[0] * scale
            
            return (x, y, z)
        except Exception as e:
            logger.error(f"Failed to read vector: {e}")
            return (0.0, 0.0, 0.0)
    
    def read_euler(self) -> Dict[str, float]:
        """
        Read Euler angles (orientation).
        
        Returns:
            Dictionary with heading, roll, pitch in degrees
        """
        heading, roll, pitch = self._read_vector(self.REG_EULER_H, 1/16.0)
        
        return {
            'heading': heading,  # 0-360°
            'roll': roll,        # -180 to +180°
            'pitch': pitch,      # -90 to +90°
            'yaw': heading       # Alias for heading
        }
    
    def read_quaternion(self) -> Tuple[float, float, float, float]:
        """
        Read quaternion (orientation as quaternion).
        
        Returns:
            Tuple of (w, x, y, z)
        """
        try:
            data = self.bus.read_i2c_block_data(self.address, self.REG_QUAT_W, 8)
            
            w = struct.unpack('<h', bytes(data[0:2]))[0] / 16384.0
            x = struct.unpack('<h', bytes(data[2:4]))[0] / 16384.0
            y = struct.unpack('<h', bytes(data[4:6]))[0] / 16384.0
            z = struct.unpack('<h', bytes(data[6:8]))[0] / 16384.0
            
            return (w, x, y, z)
        except Exception as e:
            logger.error(f"Failed to read quaternion: {e}")
            return (1.0, 0.0, 0.0, 0.0)
    
    def read_accelerometer(self) -> Tuple[float, float, float]:
        """Read raw accelerometer data (m/s²)"""
        return self._read_vector(self.REG_ACCEL_DATA, 1/100.0)
    
    def read_magnetometer(self) -> Tuple[float, float, float]:
        """Read raw magnetometer data (µT)"""
        return self._read_vector(self.REG_MAG_DATA, 1/16.0)
    
    def read_gyroscope(self) -> Tuple[float, float, float]:
        """Read raw gyroscope data (°/s)"""
        return self._read_vector(self.REG_GYRO_DATA, 1/16.0)
    
    def read_linear_acceleration(self) -> Tuple[float, float, float]:
        """Read linear acceleration (gravity removed, m/s²)"""
        return self._read_vector(self.REG_LINEAR_ACCEL, 1/100.0)
    
    def read_gravity(self) -> Tuple[float, float, float]:
        """Read gravity vector (m/s²)"""
        return self._read_vector(self.REG_GRAVITY, 1/100.0)
    
    def read_temperature(self) -> int:
        """Read temperature (°C)"""
        return self.bus.read_byte_data(self.address, self.REG_TEMP)
    
    def get_calibration_status(self) -> Dict[str, int]:
        """
        Get calibration status for all sensors.
        
        Returns:
            Dictionary with calibration status (0-3 for each sensor)
            3 = fully calibrated, 0 = not calibrated
        """
        try:
            calib = self.bus.read_byte_data(self.address, self.REG_CALIB_STAT)
            
            self.calibration_status = {
                'sys': (calib >> 6) & 0x03,
                'gyro': (calib >> 4) & 0x03,
                'accel': (calib >> 2) & 0x03,
                'mag': calib & 0x03
            }
            
            return self.calibration_status
        except Exception as e:
            logger.error(f"Failed to read calibration: {e}")
            return self.calibration_status
    
    def is_fully_calibrated(self) -> bool:
        """Check if all sensors are fully calibrated"""
        status = self.get_calibration_status()
        return all(v == 3 for v in status.values())
    
    def get_system_status(self) -> Tuple[int, int]:
        """
        Get system status and error.
        
        Returns:
            Tuple of (status, error)
        """
        status = self.bus.read_byte_data(self.address, self.REG_SYS_STATUS)
        error = self.bus.read_byte_data(self.address, self.REG_SYS_ERR)
        return (status, error)
    
    def read_orientation(self) -> Dict[str, float]:
        """
        Read complete orientation data.
        
        Returns:
            Dictionary with all orientation data
        """
        euler = self.read_euler()
        linear_accel = self.read_linear_acceleration()
        gravity = self.read_gravity()
        
        # Convert linear acceleration to G-forces
        x_g = linear_accel[0] / 9.81
        y_g = linear_accel[1] / 9.81
        z_g = linear_accel[2] / 9.81
        
        magnitude = np.sqrt(x_g**2 + y_g**2 + z_g**2)
        
        return {
            'heading': euler['heading'],
            'roll': euler['roll'],
            'pitch': euler['pitch'],
            'yaw': euler['yaw'],
            'x_g': x_g,
            'y_g': y_g,
            'z_g': z_g,
            'magnitude': magnitude,
            'gravity_x': gravity[0],
            'gravity_y': gravity[1],
            'gravity_z': gravity[2]
        }
    
    def save_calibration(self, filename: str = "config/bno055_calibration.json"):
        """Save calibration data to file"""
        # Get calibration offsets (requires switching to config mode)
        self._set_mode(self.MODE_CONFIG)
        
        # Read calibration data (22 bytes starting at 0x55)
        calib_data = self.bus.read_i2c_block_data(self.address, 0x55, 22)
        
        # Return to NDOF mode
        self._set_mode(self.MODE_NDOF)
        
        calibration = {
            'data': calib_data,
            'timestamp': time.time()
        }
        
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(calibration, f, indent=2)
        
        logger.info(f"Calibration saved to {filename}")
    
    def load_calibration(self, filename: str = "config/bno055_calibration.json"):
        """Load calibration data from file"""
        try:
            with open(filename, 'r') as f:
                calibration = json.load(f)
            
            # Switch to config mode
            self._set_mode(self.MODE_CONFIG)
            
            # Write calibration data
            calib_data = calibration['data']
            for i, byte in enumerate(calib_data):
                self.bus.write_byte_data(self.address, 0x55 + i, byte)
            
            # Return to NDOF mode
            self._set_mode(self.MODE_NDOF)
            
            logger.info(f"Calibration loaded from {filename}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load calibration: {e}")
            return False


if __name__ == "__main__":
    # Test script
    print("BNO055 9-DOF IMU Test")
    print("=" * 60)
    
    try:
        # Initialize sensor
        print("\nInitializing BNO055...")
        sensor = BNO055()
        
        # Check calibration
        print("\nCalibration Status:")
        print("Move sensor in figure-8 pattern to calibrate magnetometer")
        print("Rotate sensor on all axes to calibrate gyroscope")
        print("-" * 60)
        
        for i in range(20):
            status = sensor.get_calibration_status()
            print(f"Sys:{status['sys']} Gyro:{status['gyro']} "
                  f"Accel:{status['accel']} Mag:{status['mag']}", end='\r')
            time.sleep(0.5)
        
        print("\n")
        
        # Read data
        print("\nReading orientation data (10 samples):")
        print("-" * 60)
        for i in range(10):
            orientation = sensor.read_orientation()
            print(f"Sample {i+1:2d}: "
                  f"Heading={orientation['heading']:6.1f}°, "
                  f"Roll={orientation['roll']:+6.1f}°, "
                  f"Pitch={orientation['pitch']:+6.1f}°, "
                  f"Accel={orientation['magnitude']:.2f}G")
            time.sleep(0.5)
        
        # Save calibration if fully calibrated
        if sensor.is_fully_calibrated():
            print("\nSensor fully calibrated! Saving calibration...")
            sensor.save_calibration()
        
        print("\nTest complete!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure:")
        print("  1. BNO055 is connected correctly")
        print("  2. I2C is enabled (sudo raspi-config)")
        print("  3. PS0 connected to GND, PS1 to 3.3V")
        print("  4. ADR connected to GND (for 0x28 address)")