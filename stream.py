"""
MJPEG streaming service for real-time video processing
"""
import cv2
import numpy as np
import time
import threading
import platform
from typing import Generator, Optional, Tuple
from core.pipeline import AttentionPipeline
from services.video_recorder import VideoRecorder
from windows_performance_config import (
    get_windows_optimized_config, 
    apply_windows_optimizations,
    get_optimal_camera_backend,
    should_skip_frame,
    get_processing_resolution
)


class VideoStreamer:
    def __init__(self, pipeline: AttentionPipeline):
        """Initialize video streamer with processing pipeline"""
        self.pipeline = pipeline
        self.is_streaming = False
        self.current_source = None
        self.stream_thread = None
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.latest_stats = None
        
        # Initialize video recorder
        self.video_recorder = VideoRecorder()
        
        # Load Windows optimizations
        self.windows_config = get_windows_optimized_config()
    
    def start_stream(self, source: str, path: str = None, 
                    width: int = 1280, height: int = 720, fps: int = 20) -> bool:
        """
        Start video streaming
        
        Args:
            source: 'webcam', 'rtsp', or 'file'
            path: Path for RTSP URL or file path
            width: Stream width
            height: Stream height
            fps: Target FPS
            
        Returns:
            True if stream started successfully
        """
        if self.is_streaming:
            self.stop_stream()
        
        try:
            # Initialize video capture
            if source == 'webcam':
                # Use optimized backend selection for Windows performance
                if platform.system().lower() == "windows":
                    optimal_backend = get_optimal_camera_backend()
                    backends = [optimal_backend, cv2.CAP_ANY]
                else:
                    backends = [cv2.CAP_ANY]
                
                cap = None
                for backend in backends:
                    try:
                        print(f"Trying to open webcam with backend {backend}")
                        cap = cv2.VideoCapture(0, backend)
                        
                        if cap.isOpened():
                            # Test if we can read a frame
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                print(f"Successfully opened webcam with backend {backend}")
                                break
                            else:
                                print(f"Webcam opened but cannot read frames with backend {backend}")
                                cap.release()
                                cap = None
                        else:
                            print(f"Failed to open webcam with backend {backend}")
                            if cap:
                                cap.release()
                                cap = None
                    except Exception as e:
                        print(f"Error with backend {backend}: {e}")
                        if cap:
                            cap.release()
                            cap = None
                        continue
                
                if not cap or not cap.isOpened():
                    print("Failed to open webcam with any backend")
                    return False
                    
            elif source == 'rtsp' and path:
                cap = cv2.VideoCapture(path)
            elif source == 'file' and path:
                cap = cv2.VideoCapture(path)
            else:
                return False
            
            if not cap.isOpened():
                return False
            
            # Set capture properties with Windows optimizations
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Apply Windows-specific optimizations
            apply_windows_optimizations(cap, self.windows_config)
            
            self.current_source = cap
            self.is_streaming = True
            
            # Start streaming thread
            self.stream_thread = threading.Thread(
                target=self._stream_loop,
                args=(width, height, fps),
                daemon=True
            )
            self.stream_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting stream: {e}")
            return False
    
    def stop_stream(self):
        """Stop video streaming"""
        self.is_streaming = False
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        if self.current_source:
            self.current_source.release()
            self.current_source = None
        
        self.pipeline.reset()
    
    def _stream_loop(self, width: int, height: int, fps: int):
        """Main streaming loop (runs in separate thread) - Optimized for Windows"""
        frame_time = 1.0 / fps
        frame_count = 0
        skip_frames = self.windows_config.get('skip_frames', 2)
        
        while self.is_streaming and self.current_source:
            start_time = time.time()
            
            try:
                ret, frame = self.current_source.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames for better performance using optimized function
                if not should_skip_frame(frame_count, skip_frames):
                    # Get optimal processing resolution
                    processing_width, processing_height = get_processing_resolution(
                        width, height, 
                        self.windows_config.get('processing_width', 320),
                        self.windows_config.get('processing_height', 240)
                    )
                    
                    annotated_frame, stats = self.pipeline.process_frame(
                        frame, processing_width, processing_height
                    )
                    
                    # Resize back to original resolution for display
                    if processing_width != width or processing_height != height:
                        annotated_frame = cv2.resize(annotated_frame, (width, height))
                else:
                    # Use previous frame for skipped frames
                    with self.frame_lock:
                        if self.latest_frame is not None:
                            annotated_frame = self.latest_frame.copy()
                            stats = self.latest_stats.copy() if self.latest_stats else None
                        else:
                            annotated_frame = frame
                            stats = None
                
                # Update latest frame and stats (thread-safe)
                with self.frame_lock:
                    self.latest_frame = annotated_frame
                    self.latest_stats = stats
                
                # Maintain target FPS
                elapsed = time.time() - start_time
                sleep_time = frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Error in stream loop: {e}")
                break
        
        self.is_streaming = False
    
    def get_mjpeg_generator(self) -> Generator[bytes, None, None]:
        """
        Generator for MJPEG stream
        
        Yields:
            JPEG frame bytes in multipart format
        """
        while self.is_streaming:
            with self.frame_lock:
                if self.latest_frame is not None:
                    # Write to active recordings
                    active_recordings = self.get_active_recordings()
                    if active_recordings:
                        for recording_id in active_recordings:
                            self.write_recording_frame(recording_id, self.latest_frame, self.latest_stats)
                    
                    # Encode frame as JPEG with optimized quality for Windows
                    jpeg_quality = self.windows_config.get('jpeg_quality', 70)
                    ret, buffer = cv2.imencode('.jpg', self.latest_frame, 
                                             [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        
                        # Yield frame in multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
            
            # Use optimized sleep time from Windows config
            max_fps = self.windows_config.get('max_stream_fps', 15)
            sleep_time = 1.0 / max_fps
            time.sleep(sleep_time)
    
    def get_latest_stats(self) -> Optional[dict]:
        """Get latest processing statistics"""
        with self.frame_lock:
            return self.latest_stats.copy() if self.latest_stats else None
    
    def is_active(self) -> bool:
        """Check if streaming is active"""
        return self.is_streaming
    
    def start_recording(self, recording_id: str, width: int = 1280, height: int = 720, fps: int = 20, custom_name: Optional[str] = None) -> bool:
        """
        Start recording the video stream
        
        Args:
            recording_id: Unique identifier for this recording
            width: Video width
            height: Video height
            fps: Frames per second
            
        Returns:
            True if recording started successfully
        """
        if not self.is_streaming:
            print("Cannot start recording: no active stream")
            return False
        
        return self.video_recorder.start_recording(recording_id, width, height, fps, custom_name=custom_name)
    
    def stop_recording(self, recording_id: str) -> Optional[dict]:
        """
        Stop recording and return summary
        
        Args:
            recording_id: Recording identifier
            
        Returns:
            Recording summary or None if not found
        """
        return self.video_recorder.stop_recording(recording_id)
    
    def is_recording(self, recording_id: str) -> bool:
        """Check if a recording is active"""
        return self.video_recorder.is_recording(recording_id)
    
    def get_active_recordings(self) -> list:
        """Get list of active recording IDs"""
        return self.video_recorder.get_active_recordings()
    
    def write_recording_frame(self, recording_id: str, frame: np.ndarray, stats: Optional[dict] = None) -> bool:
        """
        Write a frame to the recording
        
        Args:
            recording_id: Recording identifier
            frame: Frame to write
            stats: Attention statistics for this frame
            
        Returns:
            True if frame was written successfully
        """
        return self.video_recorder.write_frame(recording_id, frame, stats)

