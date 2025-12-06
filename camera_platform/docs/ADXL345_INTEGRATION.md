# ADXL345 Accelerometer Integration Guide

## Hardware: Adafruit ADXL345 Triple-Axis Accelerometer

**Product:** https://www.adafruit.com/product/1231

### Specifications

| Feature | Specification |
|---------|--------------|
| **Sensor** | ADXL345 (Analog Devices) |
| **Range** | ±2g, ±4g, ±8g, ±16g (selectable) |
| **Resolution** | 13-bit (up to 4mg/LSB) |
| **Interface** | I2C or SPI |
| **I2C Address** | 0x53 (default) or 0x1D (alternate) |
| **Supply Voltage** | 2.0V - 3.6V (3.3V recommended) |
| **Logic Voltage** | 3.3V or 5V compatible |
| **Current Draw** | 40µA @ 2.5V (measurement mode) |
| **Update Rate** | Up to 3200 Hz |
| **Dimensions** | 0.8" x 0.6" (20mm x 15mm) |
| **Weight** | 1.5g |

### Key Features

✅ **High Resolution** - 13-bit measurement, 4mg/LSB sensitivity
✅ **Selectable Range** - ±2g to ±16g for different applications
✅ **Low Power** - Only 40µA in measurement mode
✅ **Built-in FIFO** - 32-level buffer for data storage
✅ **Interrupt Pins** - Activity/inactivity detection
✅ **Temperature Sensor** - Built-in temperature measurement
✅ **Level Shifter** - Works with 3.3V or 5V logic
✅ **Mounting Holes** - Easy mechanical attachment

---

## Wiring Diagram

### I2C Connection (Recommended)

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

### Detailed Pin Functions

| Pin | Function | Connection |
|-----|----------|------------|
| **VCC** | Power Supply | 3.3V (Pin 1) |
| **GND** | Ground | GND (Pin 6) |
| **SDA** | I2C Data | GPIO 2 (Pin 3) |
| **SCL** | I2C Clock | GPIO 3 (Pin 5) |
| **SDO** | I2C Address Select | GND = 0x53, 3.3V = 0x1D |
| **CS** | Chip Select | 3.3V for I2C mode |
| **INT1** | Interrupt 1 | GPIO 17 (optional) |
| **INT2** | Interrupt 2 | GPIO 27 (optional) |

### Physical Mounting

**Recommended Location:** Mount on camera platform near camera

**Orientation:**
```
     ┌─────────────┐
     │   ADXL345   │
     │             │
     │      ↑ +Y   │  ← Forward (camera direction)
     │      │      │
     │  +X ←┼→     │  ← Right
     │      │      │
     │      ↓      │
     │    +Z out   │  ← Up (perpendicular to board)
     └─────────────┘
```

**Mounting Options:**
1. **Adhesive Mount** - Double-sided foam tape
2. **Screw Mount** - Use mounting holes (M2.5 screws)
3. **3D Printed Bracket** - Custom mount for camera platform

**Important:**
- Mount rigidly to minimize vibration
- Align axes with camera/platform orientation
- Keep away from heat sources
- Protect from mechanical shock

---

## Software Configuration

### I2C Address Selection

The ADXL345 supports two I2C addresses:

| SDO Pin | I2C Address | Hex |
|---------|-------------|-----|
| GND | 83 (decimal) | 0x53 |
| 3.3V | 29 (decimal) | 0x1D |

**Default Configuration:** SDO → GND (Address 0x53)

### Range Selection

Choose range based on expected acceleration:

| Range | Resolution | Use Case |
|-------|-----------|----------|
| ±2g | 3.9 mg/LSB | Precision orientation, slow motion |
| ±4g | 7.8 mg/LSB | General purpose, moderate motion |
| ±8g | 15.6 mg/LSB | **Recommended for camera platform** |
| ±16g | 31.2 mg/LSB | High-speed motion, impact detection |

**Recommended:** ±8g for camera platform (good balance of range and resolution)

---

## Python Driver Implementation

### Enhanced Driver with ADXL345-Specific Features

```python
"""
ADXL345 Accelerometer Driver
Optimized for Adafruit ADXL345 breakout board
"""

import smbus2
import time
import numpy as np
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ADXL345:
    """
    ADXL345 Triple-Axis Accelerometer Driver
    
    Supports all ADXL345 features including:
    - Configurable measurement range (±2g to ±16g)
    - High-resolution mode (13-bit)
    - FIFO buffer
    - Interrupt configuration
    - Activity/inactivity detection
    """
    
    # I2C Addresses
    ADDRESS_DEFAULT = 0x53
    ADDRESS_ALT = 0x1D
    
    # Register Map
    REG_DEVID = 0x00          # Device ID (should be 0xE5)
    REG_THRESH_TAP = 0x1D     # Tap threshold
    REG_OFSX = 0x1E           # X-axis offset
    REG_OFSY = 0x1F           # Y-axis offset
    REG_OFSZ = 0x20           # Z-axis offset
    REG_DUR = 0x21            # Tap duration
    REG_LATENT = 0x22         # Tap latency
    REG_WINDOW = 0x23         # Tap window
    REG_THRESH_ACT = 0x24     # Activity threshold
    REG_THRESH_INACT = 0x25   # Inactivity threshold
    REG_TIME_INACT = 0x26     # Inactivity time
    REG_ACT_INACT_CTL = 0x27  # Activity/inactivity control
    REG_THRESH_FF = 0x28      # Free-fall threshold
    REG_TIME_FF = 0x29        # Free-fall time
    REG_TAP_AXES = 0x2A       # Tap axes control
    REG_ACT_TAP_STATUS = 0x2B # Activity/tap status
    REG_BW_RATE = 0x2C        # Data rate and power mode
    REG_POWER_CTL = 0x2D      # Power control
    REG_INT_ENABLE = 0x2E     # Interrupt enable
    REG_INT_MAP = 0x2F        # Interrupt mapping
    REG_INT_SOURCE = 0x30     # Interrupt source
    REG_DATA_FORMAT = 0x31    # Data format
    REG_DATAX0 = 0x32         # X-axis data 0
    REG_DATAX1 = 0x33         # X-axis data 1
    REG_DATAY0 = 0x34         # Y-axis data 0
    REG_DATAY1 = 0x35         # Y-axis data 1
    REG_DATAZ0 = 0x36         # Z-axis data 0
    REG_DATAZ1 = 0x37         # Z-axis data 1
    REG_FIFO_CTL = 0x38       # FIFO control
    REG_FIFO_STATUS = 0x39    # FIFO status
    
    # Data Format Register Bits
    RANGE_2G = 0x00
    RANGE_4G = 0x01
    RANGE_8G = 0x02
    RANGE_16G = 0x03
    FULL_RES = 0x08           # Full resolution mode
    JUSTIFY = 0x04            # Left-justified mode
    
    # Power Control Register Bits
    MEASURE = 0x08            # Measurement mode
    SLEEP = 0x04              # Sleep mode
    WAKEUP_8HZ = 0x00         # 8 Hz wakeup
    WAKEUP_4HZ = 0x01         # 4 Hz wakeup
    WAKEUP_2HZ = 0x02         # 2 Hz wakeup
    WAKEUP_1HZ = 0x03         # 1 Hz wakeup
    
    # Data Rate Settings
    DATARATE_0_10_HZ = 0x00
    DATARATE_0_20_HZ = 0x01
    DATARATE_0_39_HZ = 0x02
    DATARATE_0_78_HZ = 0x03
    DATARATE_1_56_HZ = 0x04
    DATARATE_3_13_HZ = 0x05
    DATARATE_6_25_HZ = 0x06
    DATARATE_12_5_HZ = 0x07
    DATARATE_25_HZ = 0x08
    DATARATE_50_HZ = 0x09
    DATARATE_100_HZ = 0x0A    # Default
    DATARATE_200_HZ = 0x0B
    DATARATE_400_HZ = 0x0C
    DATARATE_800_HZ = 0x0D
    DATARATE_1600_HZ = 0x0E
    DATARATE_3200_HZ = 0x0F
    
    def __init__(self, bus_number: int = 1, address: int = ADDRESS_DEFAULT,
                 range_g: int = 8, data_rate: int = DATARATE_100_HZ):
        """
        Initialize ADXL345 accelerometer.
        
        Args:
            bus_number: I2C bus number (1 for Raspberry Pi)
            address: I2C device address (0x53 or 0x1D)
            range_g: Measurement range (2, 4, 8, or 16)
            data_rate: Data rate constant (DATARATE_xxx)
        """
        self.bus = smbus2.SMBus(bus_number)
        self.address = address
        self.range_g = range_g
        
        # Verify device
        if not self._verify_device():
            raise RuntimeError(f"ADXL345 not found at address 0x{address:02X}")
        
        # Initialize sensor
        self._initialize(range_g, data_rate)
        
        # Calibration offsets
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0
        
        # Set scale factor
        self._set_scale_factor()
        
        logger.info(f"ADXL345 initialized at 0x{address:02X}, range: ±{range_g}g")
    
    def _verify_device(self) -> bool:
        """Verify ADXL345 is present"""
        try:
            device_id = self.bus.read_byte_data(self.address, self.REG_DEVID)
            return device_id == 0xE5
        except Exception as e:
            logger.error(f"Device verification failed: {e}")
            return False
    
    def _initialize(self, range_g: int, data_rate: int):
        """Configure ADXL345 for measurement"""
        # Set data rate
        self.bus.write_byte_data(self.address, self.REG_BW_RATE, data_rate)
        
        # Set range and full resolution mode
        range_map = {2: self.RANGE_2G, 4: self.RANGE_4G, 
                    8: self.RANGE_8G, 16: self.RANGE_16G}
        range_bits = range_map.get(range_g, self.RANGE_8G)
        data_format = range_bits | self.FULL_RES
        self.bus.write_byte_data(self.address, self.REG_DATA_FORMAT, data_format)
        
        # Enable measurement mode
        self.bus.write_byte_data(self.address, self.REG_POWER_CTL, self.MEASURE)
        
        time.sleep(0.1)
    
    def _set_scale_factor(self):
        """Set scale factor based on range"""
        # In full resolution mode, scale is always 4mg/LSB
        self.scale = 0.004  # 4mg per LSB
    
    def read_raw(self) -> Tuple[int, int, int]:
        """Read raw acceleration values"""
        try:
            # Read 6 bytes starting from DATAX0
            data = self.bus.read_i2c_block_data(self.address, self.REG_DATAX0, 6)
            
            # Convert to signed 16-bit integers
            x = np.int16((data[1] << 8) | data[0])
            y = np.int16((data[3] << 8) | data[2])
            z = np.int16((data[5] << 8) | data[4])
            
            return (x, y, z)
        except Exception as e:
            logger.error(f"Failed to read sensor: {e}")
            return (0, 0, 0)
    
    def read_g_force(self) -> Tuple[float, float, float]:
        """Read acceleration in G-forces"""
        x_raw, y_raw, z_raw = self.read_raw()
        
        # Convert to G-forces and apply calibration
        x_g = (x_raw * self.scale) - self.offset_x
        y_g = (y_raw * self.scale) - self.offset_y
        z_g = (z_raw * self.scale) - self.offset_z
        
        return (x_g, y_g, z_g)
    
    def read_orientation(self) -> Dict[str, float]:
        """Calculate orientation from acceleration"""
        x_g, y_g, z_g = self.read_g_force()
        
        # Calculate roll and pitch
        roll = np.arctan2(y_g, z_g) * 180 / np.pi
        pitch = np.arctan2(-x_g, np.sqrt(y_g**2 + z_g**2)) * 180 / np.pi
        
        # Calculate magnitude
        magnitude = np.sqrt(x_g**2 + y_g**2 + z_g**2)
        
        return {
            'roll': roll,
            'pitch': pitch,
            'x_g': x_g,
            'y_g': y_g,
            'z_g': z_g,
            'magnitude': magnitude
        }
    
    def calibrate(self, samples: int = 100):
        """Calibrate sensor (must be level and stationary)"""
        logger.info("Calibrating ADXL345...")
        logger.info("Keep sensor level and stationary...")
        
        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        
        for i in range(samples):
            x_raw, y_raw, z_raw = self.read_raw()
            x_sum += x_raw * self.scale
            y_sum += y_raw * self.scale
            z_sum += z_raw * self.scale
            time.sleep(0.01)
            
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i+1}/{samples}")
        
        # Calculate offsets (Z should read 1G when level)
        self.offset_x = x_sum / samples
        self.offset_y = y_sum / samples
        self.offset_z = (z_sum / samples) - 1.0
        
        logger.info(f"Calibration complete:")
        logger.info(f"  X offset: {self.offset_x:.3f}G")
        logger.info(f"  Y offset: {self.offset_y:.3f}G")
        logger.info(f"  Z offset: {self.offset_z:.3f}G")
    
    def set_offsets(self, x: int, y: int, z: int):
        """
        Set hardware offset registers.
        
        Args:
            x, y, z: Offset values (-128 to +127, 15.6mg/LSB)
        """
        self.bus.write_byte_data(self.address, self.REG_OFSX, x & 0xFF)
        self.bus.write_byte_data(self.address, self.REG_OFSY, y & 0xFF)
        self.bus.write_byte_data(self.address, self.REG_OFSZ, z & 0xFF)
    
    def enable_fifo(self, mode: str = 'stream', samples: int = 16):
        """
        Enable FIFO buffer.
        
        Args:
            mode: 'bypass', 'fifo', 'stream', or 'trigger'
            samples: Number of samples to store (0-32)
        """
        mode_map = {
            'bypass': 0x00,
            'fifo': 0x40,
            'stream': 0x80,
            'trigger': 0xC0
        }
        
        mode_bits = mode_map.get(mode, 0x80)
        samples = min(max(samples, 0), 32)
        
        fifo_ctl = mode_bits | samples
        self.bus.write_byte_data(self.address, self.REG_FIFO_CTL, fifo_ctl)
    
    def read_fifo_count(self) -> int:
        """Read number of samples in FIFO"""
        status = self.bus.read_byte_data(self.address, self.REG_FIFO_STATUS)
        return status & 0x3F
    
    def get_magnitude(self) -> float:
        """Calculate total acceleration magnitude"""
        x_g, y_g, z_g = self.read_g_force()
        return np.sqrt(x_g**2 + y_g**2 + z_g**2)


if __name__ == "__main__":
    # Test script
    print("ADXL345 Accelerometer Test")
    print("=" * 60)
    
    try:
        # Initialize sensor
        print("\nInitializing ADXL345...")
        sensor = ADXL345(range_g=8, data_rate=ADXL345.DATARATE_100_HZ)
        
        # Calibrate
        print("\nCalibrating...")
        print("Place sensor on level surface and keep still.")
        input("Press Enter to start calibration...")
        sensor.calibrate()
        
        # Read data
        print("\nReading data (10 samples):")
        print("-" * 60)
        for i in range(10):
            orientation = sensor.read_orientation()
            print(f"Sample {i+1:2d}: "
                  f"X={orientation['x_g']:+.3f}G, "
                  f"Y={orientation['y_g']:+.3f}G, "
                  f"Z={orientation['z_g']:+.3f}G, "
                  f"Mag={orientation['magnitude']:.3f}G, "
                  f"Roll={orientation['roll']:+6.1f}°, "
                  f"Pitch={orientation['pitch']:+6.1f}°")
            time.sleep(0.5)
        
        print("\nTest complete!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure:")
        print("  1. ADXL345 is connected correctly")
        print("  2. I2C is enabled (sudo raspi-config)")
        print("  3. SDO pin is connected to GND (for 0x53 address)")