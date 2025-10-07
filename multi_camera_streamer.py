"""
Multi-camera streaming service for concurrent video processing
"""
import cv2
import numpy as np
import time
import threading
import signal
from typing import Generator, Optional, Dict, List, Any
from core.pipeline import AttentionPipeline
from services.isolated_camera_processor import IsolatedMultiCameraManager
from services.video_recorder import VideoRecorder, MultiCameraVideoRecorder
from services.robust_camera_manager import RobustCameraManager


class MultiCameraStreamer:
    def __init__(self, pipeline: AttentionPipeline, max_parallel_workers: int = 4):
        """Initialize multi-camera streamer with isolated camera processing"""
        self.pipeline = pipeline
        self.active_streams = {}  # {camera_id: stream_info}
        self.stream_lock = threading.Lock()
        self.aggregated_stats = {"green": 0, "yellow": 0, "red": 0, "total": 0}
        self.stats_lock = threading.Lock()
        
        # Create isolated camera manager
        self.isolated_manager = IsolatedMultiCameraManager(
            model_path=pipeline.detector.model_path,
            conf_threshold=pipeline.detector.conf_threshold,
            yaw_threshold=pipeline.head_pose_estimator.yaw_threshold,
            pitch_threshold=pipeline.head_pose_estimator.pitch_threshold
        )
        
        # Initialize video recorders
        self.video_recorder = VideoRecorder()
        self.multi_camera_recorder = MultiCameraVideoRecorder()
        self.robust_camera_manager = RobustCameraManager()
    
    def _initialize_camera_with_timeout(self, camera_id: int, width: int, height: int, fps: int, timeout: int = 10) -> Optional[cv2.VideoCapture]:
        """Initialize camera with timeout to prevent hanging"""
        print(f"⏱️ Initializing camera {camera_id} with {timeout}s timeout...")
        
        def init_camera():
            try:
                # Use robust camera manager for initialization
                print(f"🚀 Using robust camera manager for camera {camera_id}...")
                cap = self.robust_camera_manager.initialize_camera_robust(camera_id, width, height, fps, timeout)
                
                if cap:
                    print(f"✅ Camera {camera_id} initialized successfully with robust manager")
                    return cap
                else:
                    print(f"❌ Camera {camera_id} failed robust initialization")
                    return None
                    
            except Exception as e:
                print(f"❌ Error in camera {camera_id} initialization: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Use threading with timeout
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = init_camera()
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print(f"⏰ Camera {camera_id} initialization timed out after {timeout}s")
            return None
        
        if exception[0]:
            print(f"❌ Exception during camera {camera_id} initialization: {exception[0]}")
            return None
        
        if result[0] is None:
            print(f"❌ Camera {camera_id} initialization failed")
            return None
        
        print(f"✅ Camera {camera_id} initialized successfully")
        return result[0]
    
    def start_camera_stream(self, camera_id: int, width: int = 640, height: int = 480, fps: int = 20) -> bool:
        """
        Start streaming from a specific camera
        
        Args:
            camera_id: Camera index
            width: Stream width
            height: Stream height
            fps: Target FPS
            
        Returns:
            True if stream started successfully
        """
        with self.stream_lock:
            if camera_id in self.active_streams:
                print(f"Camera {camera_id} is already streaming")
                return True  # Already streaming
            
            try:
                print(f"🔧 Initializing camera {camera_id}...")
                
                # Initialize video capture with timeout
                cap = self._initialize_camera_with_timeout(camera_id, width, height, fps, timeout=15)
                
                if cap is None:
                    print(f"❌ Failed to initialize camera {camera_id}")
                    return False
                
                # Create isolated processor for this camera
                print(f"🔄 Creating isolated processor for camera {camera_id}...")
                processor = self.isolated_manager.create_camera_processor(camera_id)
                print(f"✅ Created isolated processor for camera {camera_id}")
                
                print(f"🚀 Starting isolated processor for camera {camera_id}...")
                processor.start_processing()
                print(f"✅ Started isolated processor for camera {camera_id}")
                
                # Create stream info
                stream_info = {
                    'camera_id': camera_id,
                    'cap': cap,
                    'is_streaming': True,
                    'stream_thread': None,
                    'frame_lock': threading.Lock(),
                    'latest_frame': None,
                    'latest_stats': None,
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'processor': processor
                }
                
                # Start streaming thread
                print(f"🧵 Starting stream thread for camera {camera_id}...")
                stream_info['stream_thread'] = threading.Thread(
                    target=self._camera_stream_loop,
                    args=(stream_info,),
                    daemon=True
                )
                stream_info['stream_thread'].start()
                print(f"✅ Stream thread started for camera {camera_id}")
                
                self.active_streams[camera_id] = stream_info
                print(f"🎉 Successfully started isolated streaming from camera {camera_id}")
                return True
                
            except Exception as e:
                print(f"❌ Error starting camera {camera_id} stream: {e}")
                import traceback
                traceback.print_exc()
                # Clean up if something went wrong
                try:
                    if 'cap' in locals():
                        cap.release()
                        print(f"🧹 Released camera {camera_id} after error")
                except Exception as cleanup_error:
                    print(f"❌ Error during cleanup for camera {camera_id}: {cleanup_error}")
                return False
    
    def stop_camera_stream(self, camera_id: int):
        """Stop streaming from a specific camera"""
        with self.stream_lock:
            if camera_id in self.active_streams:
                stream_info = self.active_streams[camera_id]
                stream_info['is_streaming'] = False
                
                # Release camera first to unblock any pending read operations
                if stream_info['cap']:
                    try:
                        stream_info['cap'].release()
                        print(f"Released camera {camera_id}")
                    except Exception as e:
                        print(f"Error releasing camera {camera_id}: {e}")
                
                # Wait for thread to finish
                if stream_info['stream_thread'] and stream_info['stream_thread'].is_alive():
                    print(f"Waiting for camera {camera_id} thread to finish...")
                    stream_info['stream_thread'].join(timeout=2.0)
                    if stream_info['stream_thread'].is_alive():
                        print(f"Camera {camera_id} thread still running, but camera released - will finish naturally")
                
                del self.active_streams[camera_id]
                # Stop isolated processor for this camera
                self.isolated_manager.stop_camera_processing(camera_id)
                print(f"Stopped streaming from camera {camera_id}")
            else:
                print(f"Camera {camera_id} is not currently streaming")
    
    def stop_all_streams(self):
        """Stop all active camera streams"""
        # Get camera IDs first, then stop them without holding the lock
        with self.stream_lock:
            camera_ids = list(self.active_streams.keys())
        
        # Stop each camera stream (this will acquire the lock individually)
        for camera_id in camera_ids:
            self.stop_camera_stream(camera_id)
        
        # Reset pipeline state for clean restart
        try:
            self.pipeline.reset()
            print("Pipeline reset for clean restart")
        except Exception as e:
            print(f"Error resetting pipeline: {e}")
        
        # Stop all isolated processors
        self.isolated_manager.stop_all_processing()
        
        # Small delay to ensure cameras are fully released
        time.sleep(0.5)
    
    def shutdown(self):
        """Shutdown the multi-camera streamer and all its components"""
        # Stop all streams first
        self.stop_all_streams()
        
        # Stop all isolated processors
        self.isolated_manager.stop_all_processing()
        
        print("Multi-camera streamer shutdown complete")
    
    def _camera_stream_loop(self, stream_info: Dict[str, Any]):
        """Main streaming loop for a single camera (runs in separate thread)"""
        camera_id = stream_info['camera_id']
        cap = stream_info['cap']
        frame_time = 1.0 / stream_info['fps']
        
        try:
            while stream_info['is_streaming'] and cap.isOpened():
                start_time = time.time()
                
                try:
                    ret, frame = cap.read()
                    if not ret:
                        print(f"Camera {camera_id}: Failed to read frame, stopping stream")
                        break
                    
                    # Submit frame to isolated processor for this camera
                    stream_info['processor'].submit_frame(
                        frame, stream_info['width'], stream_info['height']
                    )
                    
                    # Get latest result from isolated processor
                    annotated_frame, stats = stream_info['processor'].get_latest_result()
                    if annotated_frame is not None and stats is not None:
                        # Update latest frame and stats (thread-safe)
                        with stream_info['frame_lock']:
                            stream_info['latest_frame'] = annotated_frame
                            stream_info['latest_stats'] = stats
                        
                        # Update aggregated stats
                        self._update_aggregated_stats(stats)
                    
                    # Maintain target FPS
                    elapsed = time.time() - start_time
                    sleep_time = frame_time - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
                except Exception as e:
                    print(f"Error in camera {camera_id} stream loop: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        finally:
            # Ensure cleanup happens even if there's an exception
            stream_info['is_streaming'] = False
            print(f"Camera {camera_id} stream loop ended")
    
    
    def _update_aggregated_stats(self, stats: Dict[str, int]):
        """Update aggregated statistics across all cameras"""
        # Get aggregated stats from isolated manager
        self.aggregated_stats = self.isolated_manager.get_aggregated_stats()
    
    def get_camera_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get latest frame from a specific camera"""
        with self.stream_lock:
            if camera_id in self.active_streams:
                stream_info = self.active_streams[camera_id]
                with stream_info['frame_lock']:
                    return stream_info['latest_frame'].copy() if stream_info['latest_frame'] is not None else None
        return None
    
    def get_camera_stats(self, camera_id: int) -> Optional[Dict[str, int]]:
        """Get latest stats from a specific camera"""
        with self.stream_lock:
            if camera_id in self.active_streams:
                stream_info = self.active_streams[camera_id]
                with stream_info['frame_lock']:
                    return stream_info['latest_stats'].copy() if stream_info['latest_stats'] else None
        return None
    
    def get_aggregated_stats(self) -> Dict[str, int]:
        """Get aggregated statistics from all active cameras"""
        with self.stats_lock:
            return self.aggregated_stats.copy()
    
    def get_active_cameras(self) -> List[int]:
        """Get list of active camera IDs"""
        return self.isolated_manager.get_active_cameras()
    
    def is_camera_active(self, camera_id: int) -> bool:
        """Check if a specific camera is actively streaming"""
        with self.stream_lock:
            return camera_id in self.active_streams and self.active_streams[camera_id]['is_streaming']
    
    def start_recording(self, recording_id: str, width: int = 640, height: int = 480, fps: int = 20, custom_name: Optional[str] = None) -> bool:
        """
        Start recording the multi-camera stream
        
        Args:
            recording_id: Unique identifier for this recording
            width: Video width
            height: Video height
            fps: Frames per second
            
        Returns:
            True if recording started successfully
        """
        active_cameras = self.get_active_cameras()
        if not active_cameras:
            print("No active cameras to record")
            return False
        
        # Get sample frames from active cameras to determine layout
        sample_frames = {}
        with self.stream_lock:
            # Create a copy of camera IDs to avoid dictionary iteration issues
            camera_ids = list(self.active_streams.keys())
            for camera_id in camera_ids:
                if camera_id in self.active_streams:  # Check if still exists
                    stream_info = self.active_streams[camera_id]
                    with stream_info['frame_lock']:
                        if stream_info['latest_frame'] is not None:
                            sample_frames[camera_id] = stream_info['latest_frame']
        
        if not sample_frames:
            print("No frames available from active cameras")
            return False
        
        return self.multi_camera_recorder.start_multi_camera_recording(
            recording_id, sample_frames, fps, custom_name=custom_name
        )
    
    def stop_recording(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """
        Stop recording and return summary
        
        Args:
            recording_id: Recording identifier
            
        Returns:
            Recording summary or None if not found
        """
        return self.multi_camera_recorder.stop_recording(recording_id)
    
    def is_recording(self, recording_id: str) -> bool:
        """Check if a recording is active"""
        return self.multi_camera_recorder.is_recording(recording_id)
    
    def get_active_recordings(self) -> List[str]:
        """Get list of active recording IDs"""
        return self.multi_camera_recorder.get_active_recordings()
    
    def write_recording_frame(self, recording_id: str, camera_frames: Dict[int, np.ndarray], stats: Optional[Dict[str, int]] = None) -> bool:
        """
        Write a frame to the recording
        
        Args:
            recording_id: Recording identifier
            camera_frames: Dictionary of {camera_id: frame}
            stats: Attention statistics for this frame
            
        Returns:
            True if frame was written successfully
        """
        # For multi-camera, we need to aggregate stats from all cameras
        if stats is None:
            # Get aggregated stats from isolated manager
            stats = self.isolated_manager.get_aggregated_stats()
        
        return self.multi_camera_recorder.write_multi_camera_frame(recording_id, camera_frames, stats)
    
    def get_multi_camera_mjpeg_generator(self) -> Generator[bytes, None, None]:
        """
        Generator for multi-camera MJPEG stream (horizontal layout)
        
        Yields:
            JPEG frame bytes in multipart format with all camera feeds
        """
        print("Starting multi-camera MJPEG generator")
        while True:
            try:
                # Get frames from all active cameras
                camera_frames = {}
                with self.stream_lock:
                    # Create a copy of camera IDs to avoid dictionary iteration issues
                    camera_ids = list(self.active_streams.keys())
                    print(f"Active cameras: {camera_ids}")
                    for camera_id in camera_ids:
                        if camera_id in self.active_streams:  # Check if still exists
                            stream_info = self.active_streams[camera_id]
                            with stream_info['frame_lock']:
                                if stream_info['latest_frame'] is not None:
                                    camera_frames[camera_id] = stream_info['latest_frame'].copy()
                                    print(f"Got frame from camera {camera_id}")
                
                if camera_frames:
                    # Create horizontal layout
                    combined_frame = self._create_horizontal_layout(camera_frames)
                    
                    # Write to active recordings
                    active_recordings = self.get_active_recordings()
                    if active_recordings:
                        # Get aggregated stats for attention tracking
                        aggregated_stats = self.isolated_manager.get_aggregated_stats()
                        
                        # Write to all active recordings
                        for recording_id in active_recordings:
                            self.write_recording_frame(recording_id, camera_frames, aggregated_stats)
                    
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', combined_frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, 80])
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        
                        # Yield frame in multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS max for streaming
                
            except Exception as e:
                print(f"Error in multi-camera MJPEG generator: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    def _create_horizontal_layout(self, camera_frames: Dict[int, np.ndarray]) -> np.ndarray:
        """
        Create horizontal layout of camera frames
        
        Args:
            camera_frames: Dictionary of {camera_id: frame}
            
        Returns:
            Combined frame with all cameras in horizontal layout
        """
        if not camera_frames:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Resize all frames to same height
        target_height = 480
        frames = []
        
        for camera_id, frame in camera_frames.items():
            if frame is not None:
                # Resize frame to target height while maintaining aspect ratio
                h, w = frame.shape[:2]
                aspect_ratio = w / h
                target_width = int(target_height * aspect_ratio)
                resized_frame = cv2.resize(frame, (target_width, target_height))
                
                # Add camera label
                label = f"Camera {camera_id}"
                cv2.putText(resized_frame, label, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                frames.append(resized_frame)
        
        if not frames:
            return np.zeros((target_height, 640, 3), dtype=np.uint8)
        
        # Combine frames horizontally
        combined_frame = np.hstack(frames)
        
        # Add aggregated stats overlay
        stats = self.get_aggregated_stats()
        stats_text = f"Total - Green: {stats['green']} | Yellow: {stats['yellow']} | Red: {stats['red']} | Total: {stats['total']}"
        
        # Add stats overlay at the bottom
        cv2.rectangle(combined_frame, (10, combined_frame.shape[0] - 40), 
                     (combined_frame.shape[1] - 10, combined_frame.shape[0] - 10), 
                     (0, 0, 0), -1)
        cv2.putText(combined_frame, stats_text, (20, combined_frame.shape[0] - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return combined_frame
