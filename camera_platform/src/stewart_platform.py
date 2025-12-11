"""
Stewart Platform Controller
Provides 6-DOF motion control for camera platform using inverse kinematics.
"""

import numpy as np
import yaml
import time
import logging
from typing import Tuple, List, Optional
from adafruit_servokit import ServoKit
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlatformGeometry:
    """Stewart platform geometric parameters"""
    base_radius: float          # mm - base mounting circle radius
    platform_radius: float      # mm - platform mounting circle radius
    servo_arm_length: float     # mm - servo horn length
    rod_length: float          # mm - connecting rod length
    home_height: float         # mm - platform height at neutral
    servo_angles: List[float]  # degrees - servo mounting angles
    platform_angles: List[float]  # degrees - platform attachment angles


@dataclass
class MotionLimits:
    """Motion limits for safety"""
    x_min: float = -30.0
    x_max: float = 30.0
    y_min: float = -30.0
    y_max: float = 30.0
    z_min: float = -20.0
    z_max: float = 40.0
    roll_min: float = -25.0
    roll_max: float = 25.0
    pitch_min: float = -25.0
    pitch_max: float = 25.0
    yaw_min: float = -30.0
    yaw_max: float = 30.0
    max_translation_speed: float = 50.0  # mm/s
    max_rotation_speed: float = 30.0     # deg/s


class StewartPlatform:
    """
    Stewart Platform 6-DOF motion controller.
    
    Provides inverse kinematics, motion planning, and safety features
    for controlling a 6-servo Stewart platform.
    """
    
    def __init__(self, config_path: str = "config/platform_geometry.yaml"):
        """
        Initialize Stewart platform controller.
        
        Args:
            config_path: Path to geometry configuration file
        """
        # Load configuration
        self.geometry = self._load_config(config_path)
        self.limits = MotionLimits()
        
        # Initialize servo controller
        self.kit = ServoKit(channels=16)
        self._setup_servos()
        
        # Current state
        self.current_pose = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.target_pose = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.is_moving = False
        self.emergency_stopped = False
        
        # Motion parameters
        self.settling_time = 0.5  # seconds
        self.update_rate = 50     # Hz
        
        logger.info("Stewart Platform initialized")
    
    def _load_config(self, config_path: str) -> PlatformGeometry:
        """Load platform geometry from YAML config"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            measurements = config['measurements']
            servo_angles = config.get('servo_angles', [0, 60, 120, 180, 240, 300])
            platform_angles = config.get('platform_angles', [30, 90, 150, 210, 270, 330])
            
            return PlatformGeometry(
                base_radius=measurements['base_radius'],
                platform_radius=measurements['platform_radius'],
                servo_arm_length=measurements['servo_arm_length'],
                rod_length=measurements['rod_length'],
                home_height=measurements['home_height'],
                servo_angles=servo_angles,
                platform_angles=platform_angles
            )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return default values
            return PlatformGeometry(
                base_radius=150.0,
                platform_radius=80.0,
                servo_arm_length=25.0,
                rod_length=200.0,
                home_height=180.0,
                servo_angles=[0, 60, 120, 180, 240, 300],
                platform_angles=[30, 90, 150, 210, 270, 330]
            )
    
    def _setup_servos(self):
        """Configure servo parameters"""
        for i in range(6):
            # Set pulse width range (adjust based on your servos)
            self.kit.servo[i].set_pulse_width_range(1000, 2000)
            # Set to neutral position
            self.kit.servo[i].angle = 90
        
        logger.info("Servos configured")
    
    def _rotation_matrix(self, roll: float, pitch: float, yaw: float) -> np.ndarray:
        """
        Calculate 3D rotation matrix from Euler angles.
        
        Args:
            roll: Rotation around X-axis (radians)
            pitch: Rotation around Y-axis (radians)
            yaw: Rotation around Z-axis (radians)
        
        Returns:
            3x3 rotation matrix
        """
        # Roll (X-axis rotation)
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(roll), -np.sin(roll)],
            [0, np.sin(roll), np.cos(roll)]
        ])
        
        # Pitch (Y-axis rotation)
        Ry = np.array([
            [np.cos(pitch), 0, np.sin(pitch)],
            [0, 1, 0],
            [-np.sin(pitch), 0, np.cos(pitch)]
        ])
        
        # Yaw (Z-axis rotation)
        Rz = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation: Rz * Ry * Rx
        return Rz @ Ry @ Rx
    
    def _base_servo_position(self, servo_index: int) -> np.ndarray:
        """
        Calculate base servo pivot position.
        
        Args:
            servo_index: Servo number (0-5)
        
        Returns:
            3D position vector [x, y, z]
        """
        angle_rad = np.radians(self.geometry.servo_angles[servo_index])
        x = self.geometry.base_radius * np.cos(angle_rad)
        y = self.geometry.base_radius * np.sin(angle_rad)
        z = 0.0
        
        return np.array([x, y, z])
    
    def _platform_attachment_position(self, servo_index: int) -> np.ndarray:
        """
        Calculate platform attachment position (in platform frame).
        
        Args:
            servo_index: Servo number (0-5)
        
        Returns:
            3D position vector [x, y, z]
        """
        angle_rad = np.radians(self.geometry.platform_angles[servo_index])
        x = self.geometry.platform_radius * np.cos(angle_rad)
        y = self.geometry.platform_radius * np.sin(angle_rad)
        z = 0.0
        
        return np.array([x, y, z])
    
    def _solve_servo_angle(self, vec: np.ndarray, arm_length: float, rod_length: float) -> float:
        """
        Solve for servo angle given vector from servo to platform attachment.
        
        Uses law of cosines to find servo angle.
        
        Args:
            vec: Vector from servo pivot to platform attachment
            arm_length: Servo arm length
            rod_length: Connecting rod length
        
        Returns:
            Servo angle in degrees
        """
        # Distance from servo pivot to attachment point
        L = np.linalg.norm(vec)
        
        # Check if reachable
        if L > (arm_length + rod_length) or L < abs(arm_length - rod_length):
            raise ValueError(f"Position unreachable: distance {L:.2f}mm")
        
        # Law of cosines: L² = arm² + rod² - 2*arm*rod*cos(angle)
        # Solve for angle between arm and rod
        cos_angle = (arm_length**2 + rod_length**2 - L**2) / (2 * arm_length * rod_length)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Numerical stability
        
        # Angle in servo frame
        # This is simplified - actual implementation needs to account for
        # servo orientation and attachment geometry
        angle_rad = np.arccos(cos_angle)
        
        # Convert to servo angle (0-180 degrees)
        # This mapping depends on your specific servo and linkage geometry
        servo_angle = 90 + np.degrees(angle_rad - np.pi/2)
        
        return np.clip(servo_angle, 0, 180)
    
    def inverse_kinematics(self, x: float, y: float, z: float, 
                          roll: float, pitch: float, yaw: float) -> List[float]:
        """
        Calculate servo angles for desired platform pose.
        
        Args:
            x, y, z: Translation in mm
            roll, pitch, yaw: Rotation in degrees
        
        Returns:
            List of 6 servo angles in degrees
        """
        # Convert angles to radians
        roll_rad = np.radians(roll)
        pitch_rad = np.radians(pitch)
        yaw_rad = np.radians(yaw)
        
        # Rotation matrix
        R = self._rotation_matrix(roll_rad, pitch_rad, yaw_rad)
        
        # Platform center position in base frame
        platform_center = np.array([x, y, z + self.geometry.home_height])
        
        servo_angles = []
        
        for i in range(6):
            # Base servo position
            servo_pos = self._base_servo_position(i)
            
            # Platform attachment position (in platform frame)
            attach_local = self._platform_attachment_position(i)
            
            # Transform to base frame
            attach_global = platform_center + R @ attach_local
            
            # Vector from servo to attachment
            vec = attach_global - servo_pos
            
            # Solve for servo angle
            try:
                angle = self._solve_servo_angle(
                    vec, 
                    self.geometry.servo_arm_length, 
                    self.geometry.rod_length
                )
                servo_angles.append(angle)
            except ValueError as e:
                logger.error(f"Servo {i} kinematics failed: {e}")
                raise
        
        return servo_angles
    
    def check_limits(self, x: float, y: float, z: float,
                    roll: float, pitch: float, yaw: float) -> bool:
        """
        Check if pose is within safety limits.
        
        Args:
            x, y, z: Translation in mm
            roll, pitch, yaw: Rotation in degrees
        
        Returns:
            True if within limits, raises ValueError otherwise
        """
        if not (self.limits.x_min <= x <= self.limits.x_max):
            raise ValueError(f"X translation {x}mm out of range [{self.limits.x_min}, {self.limits.x_max}]")
        
        if not (self.limits.y_min <= y <= self.limits.y_max):
            raise ValueError(f"Y translation {y}mm out of range [{self.limits.y_min}, {self.limits.y_max}]")
        
        if not (self.limits.z_min <= z <= self.limits.z_max):
            raise ValueError(f"Z translation {z}mm out of range [{self.limits.z_min}, {self.limits.z_max}]")
        
        if not (self.limits.roll_min <= roll <= self.limits.roll_max):
            raise ValueError(f"Roll {roll}° out of range [{self.limits.roll_min}, {self.limits.roll_max}]")
        
        if not (self.limits.pitch_min <= pitch <= self.limits.pitch_max):
            raise ValueError(f"Pitch {pitch}° out of range [{self.limits.pitch_min}, {self.limits.pitch_max}]")
        
        if not (self.limits.yaw_min <= yaw <= self.limits.yaw_max):
            raise ValueError(f"Yaw {yaw}° out of range [{self.limits.yaw_min}, {self.limits.yaw_max}]")
        
        return True
    
    def move_to(self, x: float, y: float, z: float,
               roll: float, pitch: float, yaw: float,
               duration: float = 1.0):
        """
        Move platform to specified pose.
        
        Args:
            x, y, z: Translation in mm
            roll, pitch, yaw: Rotation in degrees
            duration: Time to complete motion (seconds)
        """
        if self.emergency_stopped:
            logger.error("Cannot move: emergency stop active")
            return
        
        # Check limits
        try:
            self.check_limits(x, y, z, roll, pitch, yaw)
        except ValueError as e:
            logger.error(f"Motion rejected: {e}")
            raise
        
        # Calculate target servo angles
        try:
            target_angles = self.inverse_kinematics(x, y, z, roll, pitch, yaw)
        except ValueError as e:
            logger.error(f"Inverse kinematics failed: {e}")
            raise
        
        # Get current servo angles
        current_angles = [self.kit.servo[i].angle for i in range(6)]
        
        # Smooth motion with interpolation
        steps = int(duration * self.update_rate)
        
        for step in range(steps + 1):
            if self.emergency_stopped:
                logger.warning("Motion interrupted by emergency stop")
                return
            
            # Linear interpolation
            t = step / steps
            
            for i in range(6):
                angle = current_angles[i] + t * (target_angles[i] - current_angles[i])
                self.kit.servo[i].angle = angle
            
            time.sleep(1.0 / self.update_rate)
        
        # Update current pose
        self.current_pose = np.array([x, y, z, roll, pitch, yaw])
        self.is_moving = False
        
        logger.info(f"Moved to pose: x={x}, y={y}, z={z}, roll={roll}, pitch={pitch}, yaw={yaw}")
    
    def move_relative(self, dx: float = 0, dy: float = 0, dz: float = 0,
                     droll: float = 0, dpitch: float = 0, dyaw: float = 0,
                     duration: float = 1.0):
        """
        Move platform relative to current position.
        
        Args:
            dx, dy, dz: Translation delta in mm
            droll, dpitch, dyaw: Rotation delta in degrees
            duration: Time to complete motion (seconds)
        """
        target_pose = self.current_pose + np.array([dx, dy, dz, droll, dpitch, dyaw])
        self.move_to(*target_pose, duration=duration)
    
    def home(self, duration: float = 2.0):
        """Move platform to home position (all zeros)"""
        logger.info("Moving to home position")
        self.move_to(0, 0, 0, 0, 0, 0, duration=duration)
    
    def emergency_stop(self):
        """Emergency stop - disable all servos"""
        logger.critical("EMERGENCY STOP ACTIVATED")
        self.emergency_stopped = True
        self.is_moving = False
        
        # Disable all servos (set to neutral)
        for i in range(6):
            self.kit.servo[i].angle = 90
        
        logger.info("All servos disabled")
    
    def reset_emergency_stop(self):
        """Reset emergency stop condition"""
        logger.info("Resetting emergency stop")
        self.emergency_stopped = False
        self.home()
    
    def is_settled(self) -> bool:
        """Check if platform has settled at target position"""
        return not self.is_moving
    
    def get_current_pose(self) -> Tuple[float, float, float, float, float, float]:
        """Get current platform pose"""
        return tuple(self.current_pose)
    
    def shutdown(self):
        """Safely shutdown platform"""
        logger.info("Shutting down Stewart platform")
        self.home(duration=2.0)
        time.sleep(2.0)
        
        # Set all servos to neutral
        for i in range(6):
            self.kit.servo[i].angle = 90


if __name__ == "__main__":
    # Test script
    print("Stewart Platform Test")
    print("=" * 50)
    
    # Initialize platform
    platform = StewartPlatform()
    
    # Move to home
    print("\nMoving to home position...")
    platform.home()
    time.sleep(2)
    
    # Test movements
    test_poses = [
        (10, 0, 0, 0, 0, 0, "X translation"),
        (0, 10, 0, 0, 0, 0, "Y translation"),
        (0, 0, 10, 0, 0, 0, "Z translation"),
        (0, 0, 0, 10, 0, 0, "Roll"),
        (0, 0, 0, 0, 10, 0, "Pitch"),
        (0, 0, 0, 0, 0, 10, "Yaw"),
    ]
    
    for x, y, z, roll, pitch, yaw, description in test_poses:
        print(f"\nTesting {description}...")
        try:
            platform.move_to(x, y, z, roll, pitch, yaw, duration=1.5)
            time.sleep(2)
            platform.home()
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
    
    # Shutdown
    print("\nShutting down...")
    platform.shutdown()
    print("Test complete!")