"""
Web Server for Camera Platform Control
Provides REST API and web interface for controlling the camera platform.
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any
import json

# Import platform controllers
try:
    from stewart_platform import StewartPlatform
    from camera_control import CameraController, ZoomController
    from ai_processor import ObjectDetector, ObjectTracker, AutoFraming
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    logging.warning("Hardware modules not available - running in simulation mode")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'camera-platform-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
platform_state = {
    'initialized': False,
    'position': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0},
    'is_moving': False,
    'emergency_stopped': False,
    'camera_recording': False,
    'ai_tracking': False,
    'tracking_target': None
}

# Controllers (initialized on startup)
platform = None
camera = None
zoom = None
detector = None
tracker = None
auto_framing = None


def initialize_hardware():
    """Initialize all hardware controllers"""
    global platform, camera, zoom, detector, tracker, auto_framing
    
    if not HARDWARE_AVAILABLE:
        logger.warning("Hardware not available - running in simulation mode")
        return False
    
    try:
        # Initialize Stewart platform
        logger.info("Initializing Stewart platform...")
        platform = StewartPlatform()
        
        # Initialize camera
        logger.info("Initializing camera...")
        camera = CameraController()
        
        # Initialize zoom
        logger.info("Initializing zoom controller...")
        zoom = ZoomController()
        
        # Initialize AI (optional)
        try:
            logger.info("Initializing AI detector...")
            detector = ObjectDetector("~/hailo_models/yolov5s.hef")
            tracker = ObjectTracker()
            auto_framing = AutoFraming(detector, tracker, platform, camera)
        except Exception as e:
            logger.warning(f"AI initialization failed: {e}")
            detector = None
            tracker = None
            auto_framing = None
        
        platform_state['initialized'] = True
        logger.info("Hardware initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"Hardware initialization failed: {e}")
        return False


# REST API Routes

@app.route('/')
def index():
    """Serve main web interface"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current platform status"""
    return jsonify(platform_state)

@app.route('/api/platform/move', methods=['POST'])
def move_platform():
    """Move platform to specified position"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Platform not initialized'}), 500
    
    data = request.json
    
    try:
        x = float(data.get('x', 0))
        y = float(data.get('y', 0))
        z = float(data.get('z', 0))
        roll = float(data.get('roll', 0))
        pitch = float(data.get('pitch', 0))
        yaw = float(data.get('yaw', 0))
        duration = float(data.get('duration', 1.0))
        
        # Move platform in background thread
        def move_thread():
            platform_state['is_moving'] = True
            try:
                platform.move_to(x, y, z, roll, pitch, yaw, duration)
                platform_state['position'] = {
                    'x': x, 'y': y, 'z': z,
                    'roll': roll, 'pitch': pitch, 'yaw': yaw
                }
            except Exception as e:
                logger.error(f"Move failed: {e}")
            finally:
                platform_state['is_moving'] = False
                socketio.emit('position_update', platform_state['position'])
        
        thread = threading.Thread(target=move_thread)
        thread.start()
        
        return jsonify({'status': 'moving', 'target': data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/platform/home', methods=['POST'])
def home_platform():
    """Move platform to home position"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Platform not initialized'}), 500
    
    try:
        platform.home()
        platform_state['position'] = {
            'x': 0, 'y': 0, 'z': 0,
            'roll': 0, 'pitch': 0, 'yaw': 0
        }
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platform/emergency-stop', methods=['POST'])
def emergency_stop():
    """Trigger emergency stop"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Platform not initialized'}), 500
    
    try:
        platform.emergency_stop()
        platform_state['emergency_stopped'] = True
        socketio.emit('emergency_stop', {'status': 'stopped'})
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platform/reset-emergency', methods=['POST'])
def reset_emergency():
    """Reset emergency stop"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Platform not initialized'}), 500
    
    try:
        platform.reset_emergency_stop()
        platform_state['emergency_stopped'] = False
        return jsonify({'status': 'reset'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/capture', methods=['POST'])
def capture_image():
    """Capture still image"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Camera not initialized'}), 500
    
    data = request.json or {}
    
    try:
        resolution = tuple(data.get('resolution', [1920, 1080]))
        filename = data.get('filename', None)
        
        image_path = camera.capture_image(filename=filename, resolution=resolution)
        
        return jsonify({
            'status': 'success',
            'image_path': image_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/start-recording', methods=['POST'])
def start_recording():
    """Start video recording"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Camera not initialized'}), 500
    
    data = request.json or {}
    
    try:
        resolution = tuple(data.get('resolution', [1920, 1080]))
        framerate = int(data.get('framerate', 30))
        
        camera.start_video_recording(resolution=resolution, framerate=framerate)
        platform_state['camera_recording'] = True
        
        return jsonify({'status': 'recording'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/stop-recording', methods=['POST'])
def stop_recording():
    """Stop video recording"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Camera not initialized'}), 500
    
    try:
        camera.stop_video_recording()
        platform_state['camera_recording'] = False
        
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/timelapse', methods=['POST'])
def capture_timelapse():
    """Capture time-lapse sequence"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Camera not initialized'}), 500
    
    data = request.json
    
    try:
        interval = float(data.get('interval', 1.0))
        count = int(data.get('count', 10))
        resolution = tuple(data.get('resolution', [1920, 1080]))
        
        # Run in background thread
        def timelapse_thread():
            try:
                images = camera.capture_timelapse(interval, count, resolution)
                socketio.emit('timelapse_complete', {'images': images})
            except Exception as e:
                logger.error(f"Time-lapse failed: {e}")
                socketio.emit('timelapse_error', {'error': str(e)})
        
        thread = threading.Thread(target=timelapse_thread)
        thread.start()
        
        return jsonify({'status': 'started', 'count': count, 'interval': interval})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/camera/zoom', methods=['POST'])
def set_zoom():
    """Set camera zoom level"""
    if not platform_state['initialized']:
        return jsonify({'error': 'Zoom not initialized'}), 500
    
    data = request.json
    
    try:
        zoom_level = float(data.get('zoom', 0.0))
        duration = float(data.get('duration', 1.0))
        
        zoom.set_zoom(zoom_level, duration)
        
        return jsonify({'status': 'success', 'zoom': zoom_level})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/start-tracking', methods=['POST'])
def start_tracking():
    """Start AI object tracking"""
    if not platform_state['initialized'] or auto_framing is None:
        return jsonify({'error': 'AI not available'}), 500
    
    data = request.json
    
    try:
        target_class = data.get('target', 'person')
        
        auto_framing.start_tracking(target_class)
        platform_state['ai_tracking'] = True
        platform_state['tracking_target'] = target_class
        
        return jsonify({'status': 'tracking', 'target': target_class})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/stop-tracking', methods=['POST'])
def stop_tracking():
    """Stop AI object tracking"""
    if not platform_state['initialized'] or auto_framing is None:
        return jsonify({'error': 'AI not available'}), 500
    
    try:
        auto_framing.stop_tracking()
        platform_state['ai_tracking'] = False
        platform_state['tracking_target'] = None
        
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/presets')
def get_presets():
    """Get motion presets"""
    presets = {
        'home': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0},
        'look_left': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': -20},
        'look_right': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 20},
        'look_up': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 15, 'yaw': 0},
        'look_down': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': -15, 'yaw': 0},
        'elevated': {'x': 0, 'y': 0, 'z': 20, 'roll': 0, 'pitch': 0, 'yaw': 0},
    }
    return jsonify(presets)

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration"""
    config_path = Path('config/platform_config.json')
    
    if request.method == 'GET':
        if config_path.exists():
            with open(config_path, 'r') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({})
    
    elif request.method == 'POST':
        data = request.json
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({'status': 'saved'})


# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected")
    emit('status', platform_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")

@socketio.on('request_status')
def handle_status_request():
    """Send current status to client"""
    emit('status', platform_state)


# Background monitoring thread
def monitoring_thread():
    """Background thread for monitoring and updates"""
    while True:
        if platform_state['initialized']:
            # Update position
            if platform is not None:
                current_pose = platform.get_current_pose()
                platform_state['position'] = {
                    'x': current_pose[0],
                    'y': current_pose[1],
                    'z': current_pose[2],
                    'roll': current_pose[3],
                    'pitch': current_pose[4],
                    'yaw': current_pose[5]
                }
            
            # Emit status update
            socketio.emit('status_update', platform_state)
        
        time.sleep(0.5)  # Update at 2 Hz


if __name__ == '__main__':
    print("=" * 60)
    print("Camera Platform Web Server")
    print("=" * 60)
    
    # Initialize hardware
    print("\nInitializing hardware...")
    if initialize_hardware():
        print("✓ Hardware initialized successfully")
    else:
        print("⚠ Running in simulation mode (hardware not available)")
    
    # Start monitoring thread
    monitor = threading.Thread(target=monitoring_thread, daemon=True)
    monitor.start()
    
    # Start web server
    print("\nStarting web server...")
    print("Access the interface at: http://localhost:5000")
    print("API documentation: http://localhost:5000/api/status")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if platform is not None:
            platform.shutdown()
        if camera is not None:
            camera.cleanup()
        print("Goodbye!")