"""
Windows Performance Configuration
Optimized settings for better camera streaming performance on Windows
"""

import os
import platform

def get_windows_optimized_config():
    """
    Get optimized configuration for Windows systems
    
    Returns:
        dict: Optimized configuration parameters
    """
    if platform.system().lower() != "windows":
        return {}
    
    return {
        # Camera settings optimized for Windows
        'camera_backend': 'DirectShow',  # Most reliable on Windows
        'buffer_size': 1,  # Minimal buffer for lower latency
        'auto_exposure': 0.25,  # Manual exposure for consistency
        'fourcc': 'MJPG',  # Optimized codec for Windows
        
        # Resolution settings
        'stream_width': 640,
        'stream_height': 480,
        'processing_width': 320,
        'processing_height': 240,
        
        # FPS settings
        'stream_fps': 15,  # Reduced for better performance
        'max_stream_fps': 15,  # Cap streaming FPS
        
        # Processing optimizations
        'skip_frames': 2,  # Process every 3rd frame
        'jpeg_quality': 70,  # Lower quality for faster streaming
        'enable_frame_skipping': True,
        'enable_low_res_processing': True,
        
        # Threading optimizations
        'max_workers': 2,  # Limit concurrent processing
        'thread_priority': 'normal',  # Don't use high priority
        
        # Memory optimizations
        'enable_memory_cleanup': True,
        'cleanup_interval': 30,  # seconds
        
        # Windows-specific optimizations
        'disable_auto_focus': True,
        'disable_auto_white_balance': True,
        'disable_auto_gain': True,
    }

def apply_windows_optimizations(cap, config=None):
    """
    Apply Windows-specific optimizations to a camera capture object
    
    Args:
        cap: OpenCV VideoCapture object
        config: Optional configuration dict
    """
    if platform.system().lower() != "windows":
        return
    
    if config is None:
        config = get_windows_optimized_config()
    
    try:
        # Apply buffer size optimization
        if 'buffer_size' in config:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, config['buffer_size'])
        
        # Apply exposure settings
        if 'auto_exposure' in config:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, config['auto_exposure'])
        
        # Apply codec optimization
        if 'fourcc' in config:
            fourcc = cv2.VideoWriter_fourcc(*config['fourcc'])
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        
        # Disable auto features for better performance
        if config.get('disable_auto_focus', False):
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        if config.get('disable_auto_white_balance', False):
            cap.set(cv2.CAP_PROP_AUTO_WB, 0)
        
        if config.get('disable_auto_gain', False):
            cap.set(cv2.CAP_PROP_GAIN, 0)
            
    except Exception as e:
        print(f"Warning: Could not apply all Windows optimizations: {e}")

def get_optimal_camera_backend():
    """
    Get the optimal camera backend for Windows
    
    Returns:
        int: OpenCV backend constant
    """
    if platform.system().lower() != "windows":
        return cv2.CAP_ANY
    
    # DirectShow is typically fastest on Windows
    return cv2.CAP_DSHOW

def should_skip_frame(frame_count, skip_frames=2):
    """
    Determine if a frame should be skipped for processing
    
    Args:
        frame_count: Current frame number
        skip_frames: Number of frames to skip between processing
        
    Returns:
        bool: True if frame should be skipped
    """
    return frame_count % (skip_frames + 1) != 0

def get_processing_resolution(original_width, original_height, max_width=320, max_height=240):
    """
    Get optimal processing resolution for better performance
    
    Args:
        original_width: Original frame width
        original_height: Original frame height
        max_width: Maximum processing width
        max_height: Maximum processing height
        
    Returns:
        tuple: (width, height) for processing
    """
    # Calculate aspect ratio
    aspect_ratio = original_width / original_height
    
    # Determine processing resolution
    if original_width <= max_width and original_height <= max_height:
        return original_width, original_height
    
    # Scale down maintaining aspect ratio
    if aspect_ratio > 1:  # Landscape
        processing_width = max_width
        processing_height = int(max_width / aspect_ratio)
    else:  # Portrait
        processing_height = max_height
        processing_width = int(max_height * aspect_ratio)
    
    return processing_width, processing_height

# Import cv2 for the constants
try:
    import cv2
except ImportError:
    print("Warning: OpenCV not available for Windows optimizations")
    cv2 = None
