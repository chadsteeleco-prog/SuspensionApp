"""
AI Processing Module
Provides object detection, tracking, and scene analysis using Hailo-8 accelerator.
"""

import numpy as np
import cv2
import time
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Hailo imports
try:
    from hailo_platform import (HEF, VDevice, HailoStreamInterface, 
                               InferVStreams, ConfigureParams)
    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    logging.warning("Hailo SDK not available - AI features disabled")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Object detection result"""
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    class_id: int
    class_name: str
    confidence: float
    center: Tuple[int, int]


@dataclass
class TrackingTarget:
    """Tracking target information"""
    detection: Detection
    track_id: int
    age: int  # Number of frames tracked
    velocity: Tuple[float, float]  # (vx, vy) pixels/frame


class ObjectDetector:
    """
    Object detection using Hailo-8 AI accelerator.
    
    Supports YOLOv5, YOLOv8, and other detection models.
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        Initialize object detector.
        
        Args:
            model_path: Path to HEF model file
            confidence_threshold: Minimum confidence for detections
        """
        if not HAILO_AVAILABLE:
            raise RuntimeError("Hailo SDK not available")
        
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        
        # Load model
        logger.info(f"Loading model: {self.model_path}")
        self.hef = HEF(str(self.model_path))
        
        # Get model info
        self.input_vstream_info = self.hef.get_input_vstream_infos()[0]
        self.output_vstream_info = self.hef.get_output_vstream_infos()
        
        # Input shape
        self.input_shape = self.input_vstream_info.shape
        self.input_height = self.input_shape[0]
        self.input_width = self.input_shape[1]
        
        logger.info(f"Model input shape: {self.input_shape}")
        
        # Configure device
        self.device = VDevice()
        self.network_group = self.device.configure(self.hef)[0]
        
        # COCO class names (for YOLO models)
        self.class_names = self._load_coco_names()
        
        logger.info("Object detector initialized")
    
    def _load_coco_names(self) -> List[str]:
        """Load COCO class names"""
        return [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for model input.
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            Preprocessed image ready for inference
        """
        # Resize to model input size
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        normalized = rgb.astype(np.float32) / 255.0
        
        # Add batch dimension
        batched = np.expand_dims(normalized, axis=0)
        
        return batched
    
    def postprocess(self, outputs: List[np.ndarray], 
                   original_shape: Tuple[int, int]) -> List[Detection]:
        """
        Post-process model outputs to extract detections.
        
        Args:
            outputs: Raw model outputs
            original_shape: Original image shape (height, width)
        
        Returns:
            List of Detection objects
        """
        detections = []
        
        # This is a simplified post-processing
        # Actual implementation depends on specific model output format
        
        # For YOLO models, outputs typically contain:
        # - Bounding boxes (x, y, w, h)
        # - Confidence scores
        # - Class probabilities
        
        # Parse outputs (example for YOLOv5)
        for output in outputs:
            for detection in output:
                confidence = detection[4]
                
                if confidence < self.confidence_threshold:
                    continue
                
                # Extract bbox
                x_center, y_center, width, height = detection[:4]
                
                # Convert to pixel coordinates
                orig_h, orig_w = original_shape
                x = int((x_center - width/2) * orig_w)
                y = int((y_center - height/2) * orig_h)
                w = int(width * orig_w)
                h = int(height * orig_h)
                
                # Get class
                class_scores = detection[5:]
                class_id = np.argmax(class_scores)
                class_confidence = class_scores[class_id]
                
                # Calculate center
                center_x = x + w // 2
                center_y = y + h // 2
                
                det = Detection(
                    bbox=(x, y, w, h),
                    class_id=int(class_id),
                    class_name=self.class_names[class_id] if class_id < len(self.class_names) else "unknown",
                    confidence=float(confidence * class_confidence),
                    center=(center_x, center_y)
                )
                
                detections.append(det)
        
        return detections
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect objects in frame.
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            List of Detection objects
        """
        original_shape = frame.shape[:2]
        
        # Preprocess
        input_data = self.preprocess(frame)
        
        # Run inference
        with InferVStreams(self.network_group, 
                          input_vstreams_params={self.input_vstream_info.name: input_data},
                          output_vstreams_params={}) as infer_pipeline:
            
            # Infer
            infer_results = infer_pipeline.infer({self.input_vstream_info.name: input_data})
        
        # Post-process
        outputs = list(infer_results.values())
        detections = self.postprocess(outputs, original_shape)
        
        return detections
    
    def detect_and_draw(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Detection]]:
        """
        Detect objects and draw bounding boxes on frame.
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            Tuple of (annotated frame, detections)
        """
        detections = self.detect(frame)
        
        # Draw detections
        annotated = frame.copy()
        
        for det in detections:
            x, y, w, h = det.bbox
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw label
            label = f"{det.class_name}: {det.confidence:.2f}"
            cv2.putText(annotated, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(annotated, det.center, 5, (0, 0, 255), -1)
        
        return annotated, detections


class ObjectTracker:
    """
    Multi-object tracker with simple centroid-based tracking.
    
    Tracks objects across frames using IoU matching and centroid distance.
    """
    
    def __init__(self, max_age: int = 30, min_hits: int = 3):
        """
        Initialize object tracker.
        
        Args:
            max_age: Maximum frames to keep track without detection
            min_hits: Minimum detections before track is confirmed
        """
        self.max_age = max_age
        self.min_hits = min_hits
        
        self.tracks: Dict[int, TrackingTarget] = {}
        self.next_track_id = 0
        
        logger.info("Object tracker initialized")
    
    def _calculate_iou(self, bbox1: Tuple[int, int, int, int],
                      bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union between two bounding boxes"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def update(self, detections: List[Detection]) -> List[TrackingTarget]:
        """
        Update tracks with new detections.
        
        Args:
            detections: List of current frame detections
        
        Returns:
            List of active tracking targets
        """
        # Match detections to existing tracks
        matched_tracks = set()
        matched_detections = set()
        
        for track_id, track in list(self.tracks.items()):
            best_match = None
            best_iou = 0.3  # Minimum IoU threshold
            
            for i, det in enumerate(detections):
                if i in matched_detections:
                    continue
                
                iou = self._calculate_iou(track.detection.bbox, det.bbox)
                
                if iou > best_iou:
                    best_iou = iou
                    best_match = i
            
            if best_match is not None:
                # Update track
                det = detections[best_match]
                
                # Calculate velocity
                vx = det.center[0] - track.detection.center[0]
                vy = det.center[1] - track.detection.center[1]
                
                self.tracks[track_id] = TrackingTarget(
                    detection=det,
                    track_id=track_id,
                    age=track.age + 1,
                    velocity=(vx, vy)
                )
                
                matched_tracks.add(track_id)
                matched_detections.add(best_match)
            else:
                # No match - age out track
                track.age -= 1
                if track.age <= 0:
                    del self.tracks[track_id]
        
        # Create new tracks for unmatched detections
        for i, det in enumerate(detections):
            if i not in matched_detections:
                self.tracks[self.next_track_id] = TrackingTarget(
                    detection=det,
                    track_id=self.next_track_id,
                    age=1,
                    velocity=(0.0, 0.0)
                )
                self.next_track_id += 1
        
        # Return confirmed tracks
        confirmed_tracks = [
            track for track in self.tracks.values()
            if track.age >= self.min_hits
        ]
        
        return confirmed_tracks
    
    def get_track_by_class(self, class_name: str) -> Optional[TrackingTarget]:
        """Get first track matching class name"""
        for track in self.tracks.values():
            if track.detection.class_name == class_name and track.age >= self.min_hits:
                return track
        return None


class AutoFraming:
    """
    Automatic camera framing using object detection and tracking.
    
    Integrates with Stewart platform to keep target centered in frame.
    """
    
    def __init__(self, detector: ObjectDetector, tracker: ObjectTracker,
                 stewart_platform, camera_controller):
        """
        Initialize auto-framing system.
        
        Args:
            detector: Object detector instance
            tracker: Object tracker instance
            stewart_platform: Stewart platform controller
            camera_controller: Camera controller
        """
        self.detector = detector
        self.tracker = tracker
        self.platform = stewart_platform
        self.camera = camera_controller
        
        # PID controller parameters
        self.kp_pan = 0.01   # Proportional gain for pan (yaw)
        self.kp_tilt = 0.01  # Proportional gain for tilt (pitch)
        
        self.target_class = None
        self.is_tracking = False
        
        logger.info("Auto-framing system initialized")
    
    def start_tracking(self, target_class: str):
        """
        Start tracking specified object class.
        
        Args:
            target_class: Object class to track (e.g., 'person', 'car')
        """
        self.target_class = target_class
        self.is_tracking = True
        logger.info(f"Started tracking: {target_class}")
    
    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        logger.info("Stopped tracking")
    
    def update(self, frame: np.ndarray, frame_center: Tuple[int, int]) -> bool:
        """
        Update tracking and adjust platform position.
        
        Args:
            frame: Current camera frame
            frame_center: Center of frame (x, y)
        
        Returns:
            True if target found and tracked, False otherwise
        """
        if not self.is_tracking:
            return False
        
        # Detect objects
        detections = self.detector.detect(frame)
        
        # Update tracker
        tracks = self.tracker.update(detections)
        
        # Find target
        target_track = None
        for track in tracks:
            if track.detection.class_name == self.target_class:
                target_track = track
                break
        
        if target_track is None:
            return False
        
        # Calculate error from frame center
        target_center = target_track.detection.center
        error_x = target_center[0] - frame_center[0]
        error_y = target_center[1] - frame_center[1]
        
        # Calculate platform adjustments (simple P controller)
        pan_adjustment = -error_x * self.kp_pan   # Yaw
        tilt_adjustment = error_y * self.kp_tilt  # Pitch
        
        # Apply adjustments
        try:
            self.platform.move_relative(
                dyaw=pan_adjustment,
                dpitch=tilt_adjustment,
                duration=0.1
            )
        except Exception as e:
            logger.warning(f"Platform adjustment failed: {e}")
        
        return True


# Fallback implementation when Hailo is not available
class DummyDetector:
    """Dummy detector for testing without Hailo hardware"""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        logger.warning("Using dummy detector - no actual detection")
        self.confidence_threshold = confidence_threshold
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Return empty detection list"""
        return []
    
    def detect_and_draw(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Detection]]:
        """Return original frame with no detections"""
        return frame, []


if __name__ == "__main__":
    # Test script
    print("AI Processor Test")
    print("=" * 50)
    
    if not HAILO_AVAILABLE:
        print("Hailo SDK not available - cannot run test")
        exit(1)
    
    # Initialize detector
    model_path = "~/hailo_models/yolov5s.hef"
    detector = ObjectDetector(model_path)
    
    # Test with sample image
    test_image = cv2.imread("test_image.jpg")
    
    if test_image is not None:
        print("\nRunning detection...")
        start_time = time.time()
        
        annotated, detections = detector.detect_and_draw(test_image)
        
        inference_time = time.time() - start_time
        
        print(f"Inference time: {inference_time*1000:.1f}ms")
        print(f"Detections: {len(detections)}")
        
        for det in detections:
            print(f"  - {det.class_name}: {det.confidence:.2f}")
        
        # Save result
        cv2.imwrite("detection_result.jpg", annotated)
        print("\nResult saved: detection_result.jpg")
    else:
        print("Test image not found")
    
    print("\nTest complete!")