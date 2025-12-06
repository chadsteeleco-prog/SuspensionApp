"""
Camera Control Module
Provides high-level interface for Arducam OwlSight 64MP camera control.
"""

import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from libcamera import controls
import RPi.GPIO as GPIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraController:
    """
    High-level camera controller for Arducam OwlSight 64MP.
    
    Provides:
    - Still image capture (up to 64MP)
    - Video recording (4K/1080p)
    - Auto-focus control
    - Exposure control
    - Shutter trigger via GPIO
    - Zoom control via servo
    """
    
    def __init__(self, output_dir: str = "data/images"):
        """
        Initialize camera controller.
        
        Args:
            output_dir: Directory for saving captured images/videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize camera
        self.picam2 = Picamera2()
        self.camera_info = self.picam2.camera_properties
        
        # GPIO for shutter trigger
        self.shutter_pin = 17
        self._setup_gpio()
        
        # Camera state
        self.is_recording = False
        self.current_config = None
        
        # Default settings
        self.default_settings = {
            'exposure_time': 10000,  # microseconds
            'analogue_gain': 1.0,
            'focus_position': 0.5,   # 0.0 = infinity, 1.0 = macro
            'awb_mode': controls.AwbModeEnum.Auto,
        }
        
        logger.info(f"Camera initialized: {self.camera_info.get('Model', 'Unknown')}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _setup_gpio(self):
        """Setup GPIO for shutter trigger"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.shutter_pin, GPIO.OUT)
        GPIO.output(self.shutter_pin, GPIO.LOW)
        logger.info(f"Shutter GPIO configured on pin {self.shutter_pin}")
    
    def trigger_shutter(self, pulse_duration: float = 0.1):
        """
        Trigger camera shutter via GPIO pulse.
        
        Args:
            pulse_duration: Duration of trigger pulse in seconds
        """
        GPIO.output(self.shutter_pin, GPIO.HIGH)
        time.sleep(pulse_duration)
        GPIO.output(self.shutter_pin, GPIO.LOW)
        logger.debug("Shutter triggered")
    
    def set_focus(self, focus_position: float):
        """
        Set camera focus position.
        
        Args:
            focus_position: 0.0 (infinity) to 1.0 (macro)
        """
        focus_position = max(0.0, min(1.0, focus_position))
        self.picam2.set_controls({
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": focus_position
        })
        logger.info(f"Focus set to {focus_position:.2f}")
    
    def set_exposure(self, exposure_time: int, gain: float = 1.0):
        """
        Set camera exposure parameters.
        
        Args:
            exposure_time: Exposure time in microseconds
            gain: Analogue gain (1.0 = no gain)
        """
        self.picam2.set_controls({
            "ExposureTime": exposure_time,
            "AnalogueGain": gain
        })
        logger.info(f"Exposure set to {exposure_time}µs, gain {gain}")
    
    def auto_focus(self, timeout: float = 5.0) -> bool:
        """
        Perform auto-focus operation.
        
        Args:
            timeout: Maximum time to wait for focus (seconds)
        
        Returns:
            True if focus successful, False otherwise
        """
        logger.info("Starting auto-focus...")
        
        self.picam2.set_controls({
            "AfMode": controls.AfModeEnum.Continuous,
            "AfTrigger": controls.AfTriggerEnum.Start
        })
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            metadata = self.picam2.capture_metadata()
            af_state = metadata.get("AfState", None)
            
            if af_state == controls.AfStateEnum.Focused:
                logger.info("Auto-focus successful")
                return True
            
            time.sleep(0.1)
        
        logger.warning("Auto-focus timeout")
        return False
    
    def capture_image(self, filename: Optional[str] = None,
                     resolution: Tuple[int, int] = (9248, 6944),
                     format: str = "jpg",
                     quality: int = 95) -> str:
        """
        Capture a still image.
        
        Args:
            filename: Output filename (auto-generated if None)
            resolution: Image resolution (width, height)
            format: Image format ('jpg', 'png', 'raw')
            quality: JPEG quality (1-100)
        
        Returns:
            Path to saved image
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.{format}"
        
        output_path = self.output_dir / filename
        
        # Configure for still capture
        config = self.picam2.create_still_configuration(
            main={"size": resolution, "format": "RGB888"}
        )
        
        self.picam2.configure(config)
        self.picam2.start()
        
        # Allow time for auto-exposure
        time.sleep(2)
        
        # Capture
        logger.info(f"Capturing image: {resolution[0]}×{resolution[1]}")
        self.picam2.capture_file(str(output_path), quality=quality)
        
        self.picam2.stop()
        
        logger.info(f"Image saved: {output_path}")
        return str(output_path)
    
    def capture_raw(self, filename: Optional[str] = None) -> str:
        """
        Capture RAW image (DNG format).
        
        Args:
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to saved RAW image
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_{timestamp}.dng"
        
        output_path = self.output_dir / filename
        
        # Configure for RAW capture
        config = self.picam2.create_still_configuration(raw={})
        self.picam2.configure(config)
        self.picam2.start()
        
        time.sleep(2)
        
        logger.info("Capturing RAW image")
        self.picam2.capture_file(str(output_path), format='dng')
        
        self.picam2.stop()
        
        logger.info(f"RAW image saved: {output_path}")
        return str(output_path)
    
    def start_preview(self, duration: float = 5.0):
        """
        Start camera preview for specified duration.
        
        Args:
            duration: Preview duration in seconds
        """
        logger.info(f"Starting preview for {duration}s")
        
        config = self.picam2.create_preview_configuration()
        self.picam2.configure(config)
        self.picam2.start()
        
        time.sleep(duration)
        
        self.picam2.stop()
        logger.info("Preview stopped")
    
    def start_video_recording(self, filename: Optional[str] = None,
                             resolution: Tuple[int, int] = (1920, 1080),
                             framerate: int = 30,
                             bitrate: int = 10000000):
        """
        Start video recording.
        
        Args:
            filename: Output filename (auto-generated if None)
            resolution: Video resolution (width, height)
            framerate: Frames per second
            bitrate: Video bitrate in bits/second
        """
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.h264"
        
        self.output_path = self.output_dir / filename
        
        # Configure for video
        config = self.picam2.create_video_configuration(
            main={"size": resolution, "format": "RGB888"}
        )
        
        self.picam2.configure(config)
        
        # Setup encoder
        encoder = H264Encoder(bitrate=bitrate)
        
        # Start recording
        self.picam2.start_recording(encoder, str(self.output_path))
        self.is_recording = True
        
        logger.info(f"Video recording started: {resolution[0]}×{resolution[1]} @ {framerate}fps")
        logger.info(f"Output: {self.output_path}")
    
    def stop_video_recording(self):
        """Stop video recording"""
        if not self.is_recording:
            logger.warning("Not recording")
            return
        
        self.picam2.stop_recording()
        self.is_recording = False
        
        logger.info(f"Video recording stopped: {self.output_path}")
    
    def record_video(self, duration: float,
                    filename: Optional[str] = None,
                    resolution: Tuple[int, int] = (1920, 1080),
                    framerate: int = 30) -> str:
        """
        Record video for specified duration.
        
        Args:
            duration: Recording duration in seconds
            filename: Output filename (auto-generated if None)
            resolution: Video resolution (width, height)
            framerate: Frames per second
        
        Returns:
            Path to saved video
        """
        self.start_video_recording(filename, resolution, framerate)
        time.sleep(duration)
        self.stop_video_recording()
        
        return str(self.output_path)
    
    def capture_timelapse(self, interval: float, count: int,
                         resolution: Tuple[int, int] = (1920, 1080),
                         prefix: str = "timelapse") -> list:
        """
        Capture time-lapse sequence.
        
        Args:
            interval: Time between captures (seconds)
            count: Number of images to capture
            resolution: Image resolution
            prefix: Filename prefix
        
        Returns:
            List of captured image paths
        """
        logger.info(f"Starting time-lapse: {count} images @ {interval}s interval")
        
        captured_images = []
        
        for i in range(count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{i:04d}_{timestamp}.jpg"
            
            image_path = self.capture_image(filename, resolution)
            captured_images.append(image_path)
            
            logger.info(f"Captured {i+1}/{count}")
            
            if i < count - 1:  # Don't wait after last image
                time.sleep(interval)
        
        logger.info(f"Time-lapse complete: {len(captured_images)} images")
        return captured_images
    
    def capture_burst(self, count: int,
                     resolution: Tuple[int, int] = (4624, 3472),
                     prefix: str = "burst") -> list:
        """
        Capture burst sequence (rapid fire).
        
        Args:
            count: Number of images to capture
            resolution: Image resolution
            prefix: Filename prefix
        
        Returns:
            List of captured image paths
        """
        logger.info(f"Starting burst capture: {count} images")
        
        # Configure for burst
        config = self.picam2.create_still_configuration(
            main={"size": resolution, "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        
        time.sleep(2)  # Allow auto-exposure
        
        captured_images = []
        
        for i in range(count):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{prefix}_{i:04d}_{timestamp}.jpg"
            output_path = self.output_dir / filename
            
            self.picam2.capture_file(str(output_path))
            captured_images.append(str(output_path))
            
            logger.debug(f"Burst {i+1}/{count}")
        
        self.picam2.stop()
        
        logger.info(f"Burst complete: {len(captured_images)} images")
        return captured_images
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get camera information and capabilities"""
        return {
            'model': self.camera_info.get('Model', 'Unknown'),
            'sensor_size': self.camera_info.get('PixelArraySize', 'Unknown'),
            'unit_cell_size': self.camera_info.get('UnitCellSize', 'Unknown'),
            'color_filter_arrangement': self.camera_info.get('ColorFilterArrangement', 'Unknown'),
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.is_recording:
            self.stop_video_recording()
        
        GPIO.cleanup()
        logger.info("Camera controller cleaned up")


class ZoomController:
    """
    Zoom control via servo motor.
    
    Assumes zoom mechanism is controlled by a servo on channel 15.
    """
    
    def __init__(self, servo_channel: int = 15):
        """
        Initialize zoom controller.
        
        Args:
            servo_channel: PWM channel for zoom servo
        """
        from adafruit_servokit import ServoKit
        
        self.kit = ServoKit(channels=16)
        self.channel = servo_channel
        self.current_zoom = 0.0  # 0.0 = wide, 1.0 = telephoto
        
        # Set to wide angle
        self.set_zoom(0.0)
        
        logger.info(f"Zoom controller initialized on channel {servo_channel}")
    
    def set_zoom(self, zoom_level: float, duration: float = 1.0):
        """
        Set zoom level.
        
        Args:
            zoom_level: 0.0 (wide) to 1.0 (telephoto)
            duration: Time to complete zoom (seconds)
        """
        zoom_level = max(0.0, min(1.0, zoom_level))
        
        # Convert to servo angle (0-180 degrees)
        target_angle = zoom_level * 180
        current_angle = self.current_zoom * 180
        
        # Smooth zoom
        steps = int(duration * 50)  # 50 Hz update rate
        
        for step in range(steps + 1):
            t = step / steps
            angle = current_angle + t * (target_angle - current_angle)
            self.kit.servo[self.channel].angle = angle
            time.sleep(1.0 / 50)
        
        self.current_zoom = zoom_level
        logger.info(f"Zoom set to {zoom_level:.2f}")
    
    def zoom_in(self, amount: float = 0.1, duration: float = 0.5):
        """Zoom in by specified amount"""
        new_zoom = min(1.0, self.current_zoom + amount)
        self.set_zoom(new_zoom, duration)
    
    def zoom_out(self, amount: float = 0.1, duration: float = 0.5):
        """Zoom out by specified amount"""
        new_zoom = max(0.0, self.current_zoom - amount)
        self.set_zoom(new_zoom, duration)
    
    def get_zoom_level(self) -> float:
        """Get current zoom level"""
        return self.current_zoom


if __name__ == "__main__":
    # Test script
    print("Camera Controller Test")
    print("=" * 50)
    
    # Initialize camera
    camera = CameraController()
    
    # Print camera info
    info = camera.get_camera_info()
    print("\nCamera Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test preview
    print("\nStarting preview...")
    camera.start_preview(duration=3)
    
    # Test still capture
    print("\nCapturing test image...")
    image_path = camera.capture_image(resolution=(1920, 1080))
    print(f"Image saved: {image_path}")
    
    # Test auto-focus
    print("\nTesting auto-focus...")
    if camera.auto_focus():
        print("Focus successful")
    else:
        print("Focus failed")
    
    # Cleanup
    print("\nCleaning up...")
    camera.cleanup()
    print("Test complete!")