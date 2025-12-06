"""
G-Force Sensor Driver
Provides real-time acceleration and orientation data for spatial awareness.
"""

import smbus2
import time
import numpy as np
from typing import Tuple, Dict, List
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GForceSensor:
    """
    3-axis G-force sensor interface.
    
    Supports ADXL345 and similar I2C accelerometers.
    Provides acceleration, orientation, and motion data.
    """
    
    # ADXL345 Registers
    POWER_CTL = 0x2D
    DATA_FORMAT = 0x31
    DATAX0 = 0x32
    DEVICE_ID = 0x00
    
    # Configuration
    RANGE_2G = 0x00
    RANGE_4G = 0x01
    RANGE_8G = 0x02
    RANGE_16G = 0x03
    MEASURE_MODE = 0x08
    
    def __init__(self, bus_number: int = 1, address: int = 0x53, 
                 range_g: int = 8):
        """
        Initialize G-force sensor.
        
        Args:
            bus_number: I2C bus number (1 for Raspberry Pi)
            address: I2C device address (0x53 for ADXL345)
            range_g: Measurement range (2, 4, 8, or 16 G)
        """
        self.bus = smbus2.SMBus(bus_number)
        self.address = address
        self.range_g = range_g
        
        # Verify device
        if not self._verify_device():
            raise RuntimeError("G-force sensor not found at specified address")
        
        # Initialize sensor
        self._initialize()
        
        # Calibration offsets
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0
        
        # Set scale factor based on range
        self._set_scale_factor()
        
        # Data history for filtering
        self.history_size = 10
        self.x_history: List[float] = []
        self.y_history: List[float] = []
        self.z_history: List[float] = []
        
        logger.info(f"G-Force sensor initialized at 0x{address:02X}, range: ±{range_g}G")
    
    def _verify_device(self) -> bool:
        """Verify device is present and responding"""
        try:
            device_id = self.bus.read_byte_data(self.address, self.DEVICE_ID)
            # ADXL345 should return 0xE5
            return device_id == 0xE5
        except Exception as e:
            logger.error(f"Device verification failed: {e}")
            return False
    
    def _set_scale_factor(self):
        """Set scale factor based on range"""
        scale_factors = {
            2: 0.004,   # 4mg per LSB
            4: 0.008,   # 8mg per LSB
            8: 0.016,   # 16mg per LSB (actually 15.6mg)
            16: 0.031   # 31mg per LSB (actually 31.2mg)
        }
        self.scale = scale_factors.get(self.range_g, 0.004)
    
    def _initialize(self):
        """Configure sensor for measurement"""
        # Set range
        range_config = {
            2: self.RANGE_2G,
            4: self.RANGE_4G,
            8: self.RANGE_8G,
            16: self.RANGE_16G
        }
        range_value = range_config.get(self.range_g, self.RANGE_8G)
        
        self.bus.write_byte_data(self.address, self.DATA_FORMAT, range_value)
        
        # Enable measurement mode
        self.bus.write_byte_data(self.address, self.POWER_CTL, self.MEASURE_MODE)
        
        time.sleep(0.1)
    
    def read_raw(self) -> Tuple[int, int, int]:
        """
        Read raw acceleration values.
        
        Returns:
            Tuple of (x, y, z) raw values
        """
        try:
            # Read 6 bytes starting from DATAX0
            data = self.bus.read_i2c_block_data(self.address, self.DATAX0, 6)
            
            # Convert to signed 16-bit integers
            x = np.int16((data[1] << 8) | data[0])
            y = np.int16((data[3] << 8) | data[2])
            z = np.int16((data[5] << 8) | data[4])
            
            return (x, y, z)
        except Exception as e:
            logger.error(f"Failed to read sensor: {e}")
            return (0, 0, 0)
    
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
    
    def read_filtered(self) -> Tuple[float, float, float]:
        """
        Read filtered acceleration (moving average).
        
        Returns:
            Tuple of (x, y, z) filtered acceleration in G
        """
        x_g, y_g, z_g = self.read_g_force()
        
        # Add to history
        self.x_history.append(x_g)
        self.y_history.append(y_g)
        self.z_history.append(z_g)
        
        # Limit history size
        if len(self.x_history) > self.history_size:
            self.x_history.pop(0)
            self.y_history.pop(0)
            self.z_history.pop(0)
        
        # Return filtered values
        return (
            np.mean(self.x_history),
            np.mean(self.y_history),
            np.mean(self.z_history)
        )
    
    def read_orientation(self) -> Dict[str, float]:
        """
        Calculate orientation from acceleration.
        
        Returns:
            Dictionary with roll, pitch, and acceleration data
        """
        x_g, y_g, z_g = self.read_g_force()
        
        # Calculate roll and pitch (in degrees)
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
        """
        Calibrate sensor (must be level and stationary).
        
        Args:
            samples: Number of samples to average
        """
        logger.info("Calibrating G-force sensor...")
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
                logger.info(f"Calibration progress: {i+1}/{samples}")
        
        # Calculate offsets (Z should read 1G when level)
        self.offset_x = x_sum / samples
        self.offset_y = y_sum / samples
        self.offset_z = (z_sum / samples) - 1.0
        
        logger.info(f"Calibration complete:")
        logger.info(f"  X offset: {self.offset_x:.3f}G")
        logger.info(f"  Y offset: {self.offset_y:.3f}G")
        logger.info(f"  Z offset: {self.offset_z:.3f}G")
        
        # Save calibration
        self.save_calibration()
    
    def save_calibration(self, filename: str = "config/gforce_calibration.json"):
        """Save calibration data to file"""
        calibration = {
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'offset_z': self.offset_z,
            'range_g': self.range_g,
            'timestamp': time.time()
        }
        
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(calibration, f, indent=2)
        
        logger.info(f"Calibration saved to {filename}")
    
    def load_calibration(self, filename: str = "config/gforce_calibration.json"):
        """Load calibration data from file"""
        try:
            with open(filename, 'r') as f:
                calibration = json.load(f)
            
            self.offset_x = calibration['offset_x']
            self.offset_y = calibration['offset_y']
            self.offset_z = calibration['offset_z']
            
            logger.info(f"Calibration loaded from {filename}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load calibration: {e}")
            return False
    
    def get_magnitude(self) -> float:
        """Calculate total acceleration magnitude"""
        x_g, y_g, z_g = self.read_g_force()
        return np.sqrt(x_g**2 + y_g**2 + z_g**2)
    
    def detect_motion(self, threshold: float = 0.1) -> bool:
        """
        Detect if sensor is moving.
        
        Args:
            threshold: Motion detection threshold in G
        
        Returns:
            True if motion detected
        """
        magnitude = self.get_magnitude()
        # Motion detected if magnitude differs from 1G by more than threshold
        return abs(magnitude - 1.0) > threshold


class MotionStabilizer:
    """
    Motion stabilization using G-force sensor feedback.
    
    Compensates for platform vibration and movement.
    """
    
    def __init__(self, sensor: GForceSensor, stewart_platform):
        """
        Initialize motion stabilizer.
        
        Args:
            sensor: G-force sensor instance
            stewart_platform: Stewart platform controller
        """
        self.sensor = sensor
        self.platform = stewart_platform
        
        # Stabilization parameters
        self.enable_stabilization = False
        self.compensation_gain = 0.5
        self.update_rate = 100  # Hz
        
        # PID controller parameters
        self.kp = 0.5  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.05  # Derivative gain
        
        # PID state
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.roll_previous = 0.0
        self.pitch_previous = 0.0
        
        logger.info("Motion stabilizer initialized")
    
    def update(self, dt: float = 0.01):
        """
        Update stabilization compensation.
        
        Args:
            dt: Time step in seconds
        
        Call this in a loop for continuous stabilization.
        """
        if not self.enable_stabilization:
            return
        
        # Read current orientation
        orientation = self.sensor.read_orientation()
        roll = orientation['roll']
        pitch = orientation['pitch']
        
        # PID control for roll
        roll_error = -roll  # Negative to correct
        self.roll_integral += roll_error * dt
        roll_derivative = (roll_error - self.roll_previous) / dt
        roll_compensation = (
            self.kp * roll_error +
            self.ki * self.roll_integral +
            self.kd * roll_derivative
        )
        self.roll_previous = roll_error
        
        # PID control for pitch
        pitch_error = -pitch  # Negative to correct
        self.pitch_integral += pitch_error * dt
        pitch_derivative = (pitch_error - self.pitch_previous) / dt
        pitch_compensation = (
            self.kp * pitch_error +
            self.ki * self.pitch_integral +
            self.kd * pitch_derivative
        )
        self.pitch_previous = pitch_error
        
        # Apply compensation
        try:
            self.platform.move_relative(
                droll=roll_compensation,
                dpitch=pitch_compensation,
                duration=dt
            )
        except Exception as e:
            logger.warning(f"Stabilization adjustment failed: {e}")
    
    def enable(self):
        """Enable stabilization"""
        self.enable_stabilization = True
        # Reset PID state
        self.roll_integral = 0.0
        self.pitch_integral = 0.0
        self.roll_previous = 0.0
        self.pitch_previous = 0.0
        logger.info("Motion stabilization enabled")
    
    def disable(self):
        """Disable stabilization"""
        self.enable_stabilization = False
        logger.info("Motion stabilization disabled")
    
    def set_gains(self, kp: float, ki: float, kd: float):
        """Set PID controller gains"""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        logger.info(f"PID gains updated: Kp={kp}, Ki={ki}, Kd={kd}")


class VibrationMonitor:
    """
    Monitor and analyze platform vibration.
    """
    
    def __init__(self, sensor: GForceSensor):
        self.sensor = sensor
        self.samples: List[float] = []
        self.timestamps: List[float] = []
    
    def start_monitoring(self, duration: float = 10.0, sample_rate: float = 100.0):
        """
        Monitor vibration for specified duration.
        
        Args:
            duration: Monitoring duration in seconds
            sample_rate: Sampling rate in Hz
        """
        logger.info(f"Starting vibration monitoring for {duration}s...")
        
        self.samples = []
        self.timestamps = []
        
        start_time = time.time()
        sample_interval = 1.0 / sample_rate
        
        while time.time() - start_time < duration:
            timestamp = time.time() - start_time
            magnitude = self.sensor.get_magnitude()
            
            self.samples.append(magnitude)
            self.timestamps.append(timestamp)
            
            time.sleep(sample_interval)
        
        logger.info("Vibration monitoring complete")
    
    def analyze(self) -> Dict[str, float]:
        """
        Analyze collected vibration data.
        
        Returns:
            Dictionary with vibration statistics
        """
        if not self.samples:
            return {}
        
        samples_array = np.array(self.samples)
        
        # Calculate statistics
        mean_g = np.mean(samples_array)
        std_g = np.std(samples_array)
        max_g = np.max(samples_array)
        min_g = np.min(samples_array)
        rms_g = np.sqrt(np.mean(samples_array**2))
        
        # Frequency analysis (FFT)
        fft = np.fft.fft(samples_array - mean_g)
        frequencies = np.fft.fftfreq(len(samples_array), 
                                     self.timestamps[1] - self.timestamps[0])
        
        # Find dominant frequency
        positive_freq_idx = frequencies > 0
        dominant_freq_idx = np.argmax(np.abs(fft[positive_freq_idx]))
        dominant_freq = frequencies[positive_freq_idx][dominant_freq_idx]
        
        results = {
            'mean_g': mean_g,
            'std_g': std_g,
            'max_g': max_g,
            'min_g': min_g,
            'rms_g': rms_g,
            'dominant_frequency_hz': dominant_freq,
            'sample_count': len(self.samples)
        }
        
        logger.info("Vibration Analysis:")
        logger.info(f"  Mean: {mean_g:.3f}G")
        logger.info(f"  Std Dev: {std_g:.3f}G")
        logger.info(f"  Max: {max_g:.3f}G")
        logger.info(f"  RMS: {rms_g:.3f}G")
        logger.info(f"  Dominant Frequency: {dominant_freq:.1f}Hz")
        
        return results
    
    def save_data(self, filename: str = "data/vibration_data.csv"):
        """Save vibration data to CSV file"""
        import csv
        
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Magnitude_G'])
            
            for t, mag in zip(self.timestamps, self.samples):
                writer.writerow([t, mag])
        
        logger.info(f"Vibration data saved to {filename}")


if __name__ == "__main__":
    # Test script
    print("G-Force Sensor Test")
    print("=" * 60)
    
    try:
        # Initialize sensor
        print("\nInitializing sensor...")
        sensor = GForceSensor(range_g=8)
        
        # Try to load existing calibration
        if not sensor.load_calibration():
            # Calibrate if no saved calibration
            print("\nNo calibration found. Starting calibration...")
            print("Place sensor on level surface and keep it still.")
            input("Press Enter to start calibration...")
            sensor.calibrate()
        
        # Read data
        print("\nReading G-force data (10 samples):")
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
        
        # Test motion detection
        print("\n" + "=" * 60)
        print("Motion Detection Test")
        print("Move the sensor to test motion detection...")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        try:
            while True:
                if sensor.detect_motion(threshold=0.1):
                    print("MOTION DETECTED!", end='\r')
                else:
                    print("Stationary      ", end='\r')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n")
        
        print("\nTest complete!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the sensor is connected and I2C is enabled.")