"""
Flask application for attention detection system
"""
import os
import time
import tempfile
from flask import Flask, request, Response, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading

from core.pipeline import AttentionPipeline
from services.stream import VideoStreamer
from services.multi_camera_streamer import MultiCameraStreamer
from services.camera_detector import CameraDetector
from services.video_job import VideoJobManager
from schemas.dto import (
    HealthResponse, StreamRequest, StatsResponse, JobCreateResponse,
    JobStatusResponse, ErrorResponse, ConfigResponse, ConfigUpdateRequest
)


# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])

# Configuration
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './output'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('./models', exist_ok=True)

# Global configuration (can be updated via API)
config = {
    'yolo_model_path': os.getenv('YOLO_MODEL_PATH', './models/yolov8n.pt'),
    'conf_threshold': float(os.getenv('CONF_THRESHOLD', '0.4')),
    'yaw_threshold': float(os.getenv('YAW_T', '25')),
    'pitch_threshold': float(os.getenv('PITCH_T', '20')),
    'stream_width': int(os.getenv('STREAM_WIDTH', '1280')),
    'stream_height': int(os.getenv('STREAM_HEIGHT', '720')),
    'stream_fps': int(os.getenv('STREAM_FPS', '20'))
}

# Initialize pipeline and services
pipeline = AttentionPipeline(
    model_path=config['yolo_model_path'],
    conf_threshold=config['conf_threshold'],
    yaw_threshold=config['yaw_threshold'],
    pitch_threshold=config['pitch_threshold']
)

streamer = VideoStreamer(pipeline)
multi_camera_streamer = MultiCameraStreamer(pipeline, max_parallel_workers=4)
camera_detector = CameraDetector()
job_manager = VideoJobManager(pipeline, OUTPUT_FOLDER)

# Cleanup thread for old jobs
def cleanup_jobs():
    """Background thread to clean up old jobs"""
    while True:
        try:
            job_manager.cleanup_old_jobs(max_age_hours=24)
            time.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Error in cleanup thread: {e}")
            time.sleep(3600)

cleanup_thread = threading.Thread(target=cleanup_jobs, daemon=True)
cleanup_thread.start()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    return jsonify(ErrorResponse(
        error=type(error).__name__,
        message=str(error),
        timestamp=time.time()
    ).model_dump()), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify(HealthResponse(
        timestamp=time.time()
    ).model_dump())


@app.route('/api/test', methods=['GET'])
def test():
    """Simple test endpoint for debugging"""
    return jsonify({
        "message": "Backend is working",
        "timestamp": time.time(),
        "pipeline_loaded": pipeline is not None,
        "job_manager_loaded": job_manager is not None
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(ConfigResponse(**config).model_dump())


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    try:
        update_data = ConfigUpdateRequest(**request.json)
        
        # Update config with non-None values
        for key, value in update_data.model_dump().items():
            if value is not None:
                config[key] = value
        
        # Recreate pipeline with new config
        global pipeline, streamer, multi_camera_streamer
        pipeline = AttentionPipeline(
            model_path=config['yolo_model_path'],
            conf_threshold=config['conf_threshold'],
            yaw_threshold=config['yaw_threshold'],
            pitch_threshold=config['pitch_threshold']
        )
        streamer = VideoStreamer(pipeline)
        multi_camera_streamer = MultiCameraStreamer(pipeline, max_parallel_workers=4)
        
        return jsonify(ConfigResponse(**config).model_dump())
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="ConfigUpdateError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 400


@app.route('/api/stream', methods=['GET'])
def video_stream():
    """MJPEG video stream endpoint"""
    try:
        # Parse query parameters
        source = request.args.get('source', 'webcam')
        path = request.args.get('path')
        width = int(request.args.get('w', config['stream_width']))
        height = int(request.args.get('h', config['stream_height']))
        fps = int(request.args.get('fps', config['stream_fps']))
        
        # Start streaming if not already active
        if not streamer.is_active():
            success = streamer.start_stream(source, path, width, height, fps)
            if not success:
                return jsonify(ErrorResponse(
                    error="StreamError",
                    message="Failed to start video stream",
                    timestamp=time.time()
                ).model_dump()), 500
        
        # Return MJPEG stream
        return Response(
            streamer.get_mjpeg_generator(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="StreamError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/stream/stop', methods=['POST'])
def stop_stream():
    """Stop video stream"""
    try:
        streamer.stop_stream()
        return jsonify({"message": "Stream stopped successfully"})
    except Exception as e:
        return jsonify(ErrorResponse(
            error="StreamError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API communication"""
    return jsonify({
        "message": "API is working",
        "timestamp": time.time(),
        "camera_detector_available": camera_detector is not None
    })

@app.route('/api/cameras', methods=['GET'])
def get_available_cameras():
    """Get list of available cameras (fast detection)"""
    try:
        print("=== CAMERA DETECTION REQUEST ===")
        print(f"Camera detector instance: {camera_detector}")
        print("Starting fast camera detection...")
        
        # Use fast detection with fewer cameras and backends
        cameras = camera_detector.detect_cameras(max_cameras=3)
        
        print(f"Detection completed. Found {len(cameras)} cameras:")
        for cam in cameras:
            print(f"  - Camera {cam['id']}: {cam['name']} ({cam['width']}x{cam['height']})")
        
        response_data = {
            "cameras": cameras,
            "count": len(cameras),
            "timestamp": time.time()
        }
        
        print(f"Returning response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Camera detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(ErrorResponse(
            error="CameraDetectionError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500

@app.route('/api/cameras/full', methods=['GET'])
def get_all_available_cameras():
    """Get list of all available cameras (comprehensive detection)"""
    try:
        print("=== FULL CAMERA DETECTION REQUEST ===")
        print("Starting comprehensive camera detection...")
        
        # Use full detection with all cameras and backends
        cameras = camera_detector.detect_cameras(max_cameras=10)
        
        print(f"Full detection completed. Found {len(cameras)} cameras:")
        for cam in cameras:
            print(f"  - Camera {cam['id']}: {cam['name']} ({cam['width']}x{cam['height']})")
        
        response_data = {
            "cameras": cameras,
            "count": len(cameras),
            "timestamp": time.time()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Full camera detection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(ErrorResponse(
            error="CameraDetectionError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/cameras/<int:camera_id>/test', methods=['GET'])
def test_camera(camera_id):
    """Test if a specific camera is available"""
    try:
        is_available = camera_detector.test_camera(camera_id)
        camera_info = camera_detector.get_camera_info(camera_id)
        return jsonify({
            "camera_id": camera_id,
            "available": is_available,
            "info": camera_info,
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify(ErrorResponse(
            error="CameraTestError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/multi-camera/stream', methods=['GET'])
def multi_camera_stream():
    """Multi-camera MJPEG stream endpoint"""
    try:
        # Parse query parameters
        camera_ids = request.args.get('cameras', '0')  # Default to camera 0
        camera_list = [int(x.strip()) for x in camera_ids.split(',') if x.strip()]
        width = int(request.args.get('w', 640))
        height = int(request.args.get('h', 480))
        fps = int(request.args.get('fps', 20))
        
        # Start streams for all requested cameras
        started_cameras = []
        for camera_id in camera_list:
            if multi_camera_streamer.start_camera_stream(camera_id, width, height, fps):
                started_cameras.append(camera_id)
        
        if not started_cameras:
            return jsonify(ErrorResponse(
                error="MultiCameraStreamError",
                message="No cameras could be started",
                timestamp=time.time()
            ).model_dump()), 500
        
        # Return MJPEG stream
        return Response(
            multi_camera_streamer.get_multi_camera_mjpeg_generator(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="MultiCameraStreamError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/multi-camera/start', methods=['POST'])
def start_multi_camera():
    """Start multi-camera streaming"""
    try:
        data = request.json or {}
        camera_ids = data.get('cameras', [0])  # Default to camera 0
        width = data.get('width', 640)
        height = data.get('height', 480)
        fps = data.get('fps', 20)
        
        started_cameras = []
        failed_cameras = []
        
        print(f"🚀 Starting multi-camera stream with cameras: {camera_ids}")
        
        for camera_id in camera_ids:
            print(f"📹 Attempting to start camera {camera_id}...")
            try:
                if multi_camera_streamer.start_camera_stream(camera_id, width, height, fps):
                    started_cameras.append(camera_id)
                    print(f"✅ Camera {camera_id} started successfully")
                else:
                    failed_cameras.append(camera_id)
                    print(f"❌ Camera {camera_id} failed to start")
            except Exception as e:
                failed_cameras.append(camera_id)
                print(f"❌ Exception starting camera {camera_id}: {e}")
                import traceback
                traceback.print_exc()
        
        return jsonify({
            "started_cameras": started_cameras,
            "failed_cameras": failed_cameras,
            "message": f"Started {len(started_cameras)} cameras, {len(failed_cameras)} failed",
            "timestamp": time.time()
        })
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="MultiCameraStartError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/multi-camera/stop', methods=['POST'])
def stop_multi_camera():
    """Stop multi-camera streaming"""
    try:
        print("🛑 Multi-camera stop request received")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.json or {}
        else:
            data = request.form.to_dict() or {}
        
        camera_ids = data.get('cameras', [])  # Empty list means stop all
        
        print(f"📋 Stop request data: {data}")
        print(f"📋 Camera IDs to stop: {camera_ids}")
        
        if not camera_ids:
            print("🛑 Stopping all camera streams...")
            multi_camera_streamer.stop_all_streams()
            print("✅ All camera streams stopped")
            return jsonify({
                "message": "All camera streams stopped",
                "timestamp": time.time()
            })
        else:
            print(f"🛑 Stopping specific cameras: {camera_ids}")
            stopped_cameras = []
            for camera_id in camera_ids:
                print(f"🛑 Stopping camera {camera_id}...")
                multi_camera_streamer.stop_camera_stream(camera_id)
                stopped_cameras.append(camera_id)
                print(f"✅ Camera {camera_id} stopped")
            
            print(f"✅ Stopped {len(stopped_cameras)} cameras")
            return jsonify({
                "stopped_cameras": stopped_cameras,
                "message": f"Stopped {len(stopped_cameras)} cameras",
                "timestamp": time.time()
            })
        
    except Exception as e:
        print(f"❌ Error stopping multi-camera streams: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(ErrorResponse(
            error="MultiCameraStopError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/multi-camera/status', methods=['GET'])
def get_multi_camera_status():
    """Get multi-camera streaming status"""
    try:
        active_cameras = multi_camera_streamer.get_active_cameras()
        aggregated_stats = multi_camera_streamer.get_aggregated_stats()
        
        # Get individual camera stats
        camera_stats = {}
        for camera_id in active_cameras:
            camera_stats[camera_id] = multi_camera_streamer.get_camera_stats(camera_id)
        
        return jsonify({
            "active_cameras": active_cameras,
            "camera_count": len(active_cameras),
            "aggregated_stats": aggregated_stats,
            "individual_stats": camera_stats,
            "timestamp": time.time()
        })
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="MultiCameraStatusError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


# Recording endpoints
@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    """Start recording the current stream"""
    try:
        data = request.get_json()
        recording_id = data.get('recording_id', f"recording_{int(time.time())}")
        width = data.get('width', 1280)
        height = data.get('height', 720)
        fps = data.get('fps', 20)
        stream_type = data.get('stream_type', 'single')  # 'single' or 'multi'
        custom_name = data.get('custom_name', None)
        
        success = False
        if stream_type == 'single':
            success = streamer.start_recording(recording_id, width, height, fps, custom_name)
        elif stream_type == 'multi':
            success = multi_camera_streamer.start_recording(recording_id, width, height, fps, custom_name)
        
        if success:
            return jsonify({
                'recording_id': recording_id,
                'stream_type': stream_type,
                'width': width,
                'height': height,
                'fps': fps,
                'message': f'Recording started successfully',
                'timestamp': time.time()
            })
        else:
            return jsonify(ErrorResponse(
                error="RecordingError",
                message=f"Failed to start recording: {stream_type} stream not active",
                timestamp=time.time()
            ).model_dump()), 400
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="RecordingError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    """Stop recording and return summary"""
    try:
        data = request.get_json()
        recording_id = data.get('recording_id')
        stream_type = data.get('stream_type', 'single')  # 'single' or 'multi'
        
        if not recording_id:
            return jsonify(ErrorResponse(
                error="RecordingError",
                message="recording_id is required",
                timestamp=time.time()
            ).model_dump()), 400
        
        summary = None
        if stream_type == 'single':
            summary = streamer.stop_recording(recording_id)
        elif stream_type == 'multi':
            summary = multi_camera_streamer.stop_recording(recording_id)
        
        if summary:
            return jsonify({
                'recording_id': recording_id,
                'stream_type': stream_type,
                'summary': summary,
                'message': 'Recording stopped successfully',
                'timestamp': time.time()
            })
        else:
            return jsonify(ErrorResponse(
                error="RecordingError",
                message=f"Recording {recording_id} not found or already stopped",
                timestamp=time.time()
            ).model_dump()), 404
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="RecordingError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500

@app.route('/api/recording/status', methods=['GET'])
def get_recording_status():
    """Get status of active recordings"""
    try:
        stream_type = request.args.get('stream_type', 'single')
        
        if stream_type == 'single':
            active_recordings = streamer.get_active_recordings()
        elif stream_type == 'multi':
            active_recordings = multi_camera_streamer.get_active_recordings()
        else:
            return jsonify(ErrorResponse(
                error="RecordingError",
                message="Invalid stream_type. Must be 'single' or 'multi'",
                timestamp=time.time()
            ).model_dump()), 400
        
        return jsonify({
            'stream_type': stream_type,
            'active_recordings': active_recordings,
            'recording_count': len(active_recordings),
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="RecordingError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500

# Report generation endpoints
@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """Generate attention analysis report for a recording"""
    try:
        data = request.get_json()
        recording_id = data.get('recording_id')
        stream_type = data.get('stream_type', 'single')
        
        if not recording_id:
            return jsonify(ErrorResponse(
                error="ReportError",
                message="recording_id is required",
                timestamp=time.time()
            ).model_dump()), 400
        
        # Import here to avoid circular imports
        from services.report_generator import ReportGenerator
        
        # Get recording information
        recording_info = None
        attention_data = None
        
        # Try to get attention data from active recorders first
        attention_data = None
        recording_info = None
        
        if stream_type == 'single':
            attention_data = streamer.video_recorder.get_attention_data(recording_id)
        elif stream_type == 'multi':
            attention_data = multi_camera_streamer.video_recorder.get_attention_data(recording_id)
        
        # If not found in active recorders, try to load from saved JSON file
        if not attention_data:
            import json
            from pathlib import Path
            
            recordings_dir = Path("recordings")
            
            print(f"Recording ID from request: {recording_id}")
            
            # List all available attention data files for debugging
            all_attention_files = list(recordings_dir.glob("*_attention_data.json"))
            print(f"Available attention data files: {[f.name for f in all_attention_files]}")
            
            # Try multiple strategies to find the attention data file
            attention_file = None
            
            # Strategy 1: Exact match
            exact_file = recordings_dir / f"{recording_id}_attention_data.json"
            if exact_file.exists():
                attention_file = exact_file
                print(f"Found exact match: {attention_file}")
            
            # Strategy 2: Find the most recent attention data file if no exact match
            # Only use this as fallback if we have no other options
            if not attention_file and all_attention_files:
                # Sort by modification time (most recent first)
                most_recent_file = max(all_attention_files, key=lambda f: f.stat().st_mtime)
                attention_file = most_recent_file
                print(f"Using most recent attention data file as fallback: {attention_file}")
                print("WARNING: This may not be the correct recording data!")
            
            # Strategy 3: Try to find by partial match (extract base name from recording_id)
            if not attention_file and all_attention_files:
                # Extract the base name from recording_id (remove timestamp part)
                base_name = recording_id.split('_2025-')[0] if '_2025-' in recording_id else recording_id
                print(f"Looking for files matching base name: {base_name}")
                
                # Try to find files that contain the base name
                matching_files = [f for f in all_attention_files if base_name in f.name]
                if matching_files:
                    # If multiple matches, use the most recent one
                    attention_file = max(matching_files, key=lambda f: f.stat().st_mtime)
                    print(f"Found partial match: {attention_file}")
                else:
                    print(f"No files found matching base name: {base_name}")
            
            if attention_file and attention_file.exists():
                try:
                    with open(attention_file, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                    attention_data = {
                        'tracking_data': saved_data.get('tracking_data', []),
                        'summary_statistics': saved_data.get('summary_statistics', {}),
                        'total_duration': saved_data.get('total_duration', 0),
                        'total_frames': saved_data.get('total_frames', 0),
                        'custom_name': saved_data.get('custom_name')
                    }
                    print(f"Loaded attention data from {attention_file}")
                except Exception as e:
                    print(f"Error loading attention data: {e}")
            else:
                print(f"No attention data file found for recording {recording_id}")
        
        if not attention_data:
            return jsonify(ErrorResponse(
                error="ReportError",
                message=f"No attention data found for recording {recording_id}. Make sure the recording was completed and attention tracking was active.",
                timestamp=time.time()
            ).model_dump()), 404
        
        # Create recording info
        recording_info = {
            'recording_id': recording_id,
            'custom_name': attention_data.get('custom_name'),
            'duration': attention_data.get('total_duration', 0),
            'width': 1280,
            'height': 720,
            'fps': 20,
            'frame_count': attention_data.get('total_frames', 0)
        }
        
        # Update recording info with actual data
        if attention_data.get('summary_statistics'):
            recording_info['duration'] = attention_data.get('total_duration', 0)
            recording_info['frame_count'] = len(attention_data.get('tracking_data', []))
        
        # Extract sample frames from the video file
        sample_frames = []
        try:
            import cv2
            from pathlib import Path
            
            # Look for the video file using flexible matching
            recordings_dir = Path("recordings")
            
            # Strategy 1: Exact match
            video_files = list(recordings_dir.glob(f"*{recording_id}*.mp4"))
            
            # Strategy 2: If no exact match, try to find the most recent video file
            if not video_files:
                all_video_files = list(recordings_dir.glob("*.mp4"))
                if all_video_files:
                    # Sort by modification time (most recent first)
                    most_recent_video = max(all_video_files, key=lambda f: f.stat().st_mtime)
                    video_files = [most_recent_video]
                    print(f"Using most recent video file: {most_recent_video}")
            
            # Strategy 3: Try partial match
            if not video_files:
                base_name = recording_id.split('_2025-')[0] if '_2025-' in recording_id else recording_id
                print(f"Looking for video files matching base name: {base_name}")
                video_files = [f for f in recordings_dir.glob("*.mp4") if base_name in f.name]
            
            if video_files:
                video_path = video_files[0]  # Take the first matching file
                cap = cv2.VideoCapture(str(video_path))
                
                if cap.isOpened():
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    
                    # Extract 4 sample frames evenly distributed
                    frame_indices = [int(total_frames * i / 4) for i in range(4)]
                    
                    for frame_idx in frame_indices:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame = cap.read()
                        if ret:
                            sample_frames.append(frame)
                    
                    cap.release()
                    print(f"Extracted {len(sample_frames)} sample frames from {video_path}")
                else:
                    print(f"Could not open video file: {video_path}")
            else:
                print(f"No video file found for recording {recording_id}")
                
        except Exception as e:
            print(f"Error extracting sample frames: {e}")
        
        # Generate report
        report_generator = ReportGenerator()
        report_path = report_generator.generate_attention_report(
            recording_id, recording_info, attention_data, sample_frames
        )
        
        return jsonify({
            'recording_id': recording_id,
            'stream_type': stream_type,
            'report_path': report_path,
            'message': 'Report generated successfully',
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="ReportError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500

@app.route('/api/report/download/<path:filename>', methods=['GET'])
def download_report(filename):
    """Download a generated report"""
    try:
        from flask import send_file
        import os
        
        print(f"Download request for filename: {filename}")
        
        # Security check - ensure filename is safe
        if '..' in filename or '/' in filename or '\\' in filename:
            print(f"Invalid filename detected: {filename}")
            return jsonify(ErrorResponse(
                error="ReportError",
                message="Invalid filename",
                timestamp=time.time()
            ).model_dump()), 400
        
        report_path = os.path.join('reports', filename)
        print(f"Looking for report at: {report_path}")
        
        if not os.path.exists(report_path):
            print(f"Report file not found: {report_path}")
            # List available reports for debugging
            reports_dir = 'reports'
            if os.path.exists(reports_dir):
                available_reports = os.listdir(reports_dir)
                print(f"Available reports: {available_reports}")
            return jsonify(ErrorResponse(
                error="ReportError",
                message="Report file not found",
                timestamp=time.time()
            ).model_dump()), 404
        
        print(f"Sending file: {report_path}")
        return send_file(report_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"Error downloading report: {e}")
        return jsonify(ErrorResponse(
            error="ReportError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload video file for processing"""
    try:
        if 'file' not in request.files:
            return jsonify(ErrorResponse(
                error="UploadError",
                message="No file provided",
                timestamp=time.time()
            ).model_dump()), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify(ErrorResponse(
                error="UploadError",
                message="No file selected",
                timestamp=time.time()
            ).model_dump()), 400
        
        if not allowed_file(file.filename):
            return jsonify(ErrorResponse(
                error="UploadError",
                message=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}",
                timestamp=time.time()
            ).model_dump()), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        # Create processing job
        job_id = job_manager.create_job(filepath)
        
        return jsonify(JobCreateResponse(
            job_id=job_id
        ).model_dump())
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="UploadError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get job processing status"""
    try:
        job = job_manager.get_job_status(job_id)
        
        if not job:
            return jsonify(ErrorResponse(
                error="JobNotFound",
                message=f"Job {job_id} not found",
                timestamp=time.time()
            ).model_dump()), 404
        
        return jsonify(JobStatusResponse(**job).model_dump())
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="JobStatusError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/job/<job_id>/result', methods=['GET'])
def get_job_result(job_id):
    """Download processed video result"""
    try:
        result_path = job_manager.get_job_result_path(job_id)
        
        if not result_path:
            return jsonify(ErrorResponse(
                error="ResultNotFound",
                message=f"Result for job {job_id} not found or not ready",
                timestamp=time.time()
            ).model_dump()), 404
        
        return send_file(
            result_path,
            as_attachment=True,
            download_name=f"processed_{job_id}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="ResultError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/stats/live', methods=['GET'])
def get_live_stats():
    """Get live processing statistics"""
    try:
        # Get stats from streamer if active
        if streamer.is_active():
            stats = streamer.get_latest_stats()
            if stats:
                # Ensure timestamp is current and remove any existing timestamp from stats
                stats_copy = stats.copy()
                stats_copy['timestamp'] = time.time()
                return jsonify(StatsResponse(**stats_copy).model_dump())
        
        # Return empty stats if no active stream
        return jsonify(StatsResponse(
            timestamp=time.time()
        ).model_dump())
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="StatsError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


@app.route('/api/stats/average', methods=['GET'])
def get_average_stats():
    """Get average statistics over time period"""
    try:
        seconds = int(request.args.get('seconds', 10))
        
        if streamer.is_active():
            avg_stats = pipeline.get_average_stats(seconds)
            # Ensure timestamp is current and remove any existing timestamp from stats
            avg_stats_copy = avg_stats.copy()
            avg_stats_copy['timestamp'] = time.time()
            return jsonify(StatsResponse(**avg_stats_copy).model_dump())
        
        return jsonify(StatsResponse(
            timestamp=time.time()
        ).model_dump())
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="StatsError",
            message=str(e),
            timestamp=time.time()
        ).model_dump()), 500


if __name__ == '__main__':
    print("Starting Attention Detection Server...")
    print(f"Configuration: {config}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        threaded=True
    )

