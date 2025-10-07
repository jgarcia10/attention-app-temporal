#!/usr/bin/env python3
"""
Robust camera manager with multiple fallback strategies
"""
import cv2
import time
import threading
import platform
import subprocess
import psutil
from typing import Dict, List, Any, Optional, Tuple
import gc


class RobustCameraManager:
    def __init__(self):
        """Initialize robust camera manager"""
        self.system = platform.system().lower()
        self.camera_cache = {}
        self.lock = threading.Lock()
        
    def force_cleanup_camera(self, camera_id: int) -> bool:
        """Force cleanup of camera resources"""
        try:
            print(f"🧹 Force cleaning camera {camera_id}...")
            
            # Try to release any existing captures
            for _ in range(3):  # Try 3 times
                try:
                    cap = cv2.VideoCapture(camera_id)
                    if cap.isOpened():
                        cap.release()
                        print(f"✅ Released camera {camera_id} capture")
                    break
                except:
                    pass
                time.sleep(0.1)
            
            # Force garbage collection
            gc.collect()
            time.sleep(0.5)
            
            # On Windows, try to reset camera drivers
            if self.system == "windows":
                self._reset_windows_camera_driver(camera_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error force cleaning camera {camera_id}: {e}")
            return False
    
    def _reset_windows_camera_driver(self, camera_id: int):
        """Reset Windows camera driver (simplified)"""
        try:
            print(f"🔄 Attempting Windows camera driver reset for camera {camera_id}...")
            
            # Skip the actual reset - it's too slow and risky
            print(f"⚠️ Skipping Windows camera driver reset (too slow/risky)")
            print(f"💡 Try manually closing any camera applications using camera {camera_id}")
            
            # Just wait a bit for any existing processes to release the camera
            time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error with Windows camera driver reset: {e}")
    
    def test_camera_with_multiple_strategies(self, camera_id: int, timeout: int = 10) -> Tuple[bool, str]:
        """Test camera with multiple strategies"""
        strategies = [
            ("Direct OpenCV", self._test_direct_opencv),
            ("DirectShow Backend", self._test_directshow_backend),
            ("Media Foundation Backend", self._test_media_foundation_backend),
            ("V4L2 Backend", self._test_v4l2_backend),
            ("Any Backend", self._test_any_backend)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                print(f"🧪 Testing camera {camera_id} with {strategy_name}...")
                success, error = strategy_func(camera_id, timeout)
                
                if success:
                    print(f"✅ Camera {camera_id} works with {strategy_name}")
                    return True, strategy_name
                else:
                    print(f"❌ Camera {camera_id} failed with {strategy_name}: {error}")
                    
            except Exception as e:
                print(f"❌ Exception testing camera {camera_id} with {strategy_name}: {e}")
        
        return False, "All strategies failed"
    
    def _test_direct_opencv(self, camera_id: int, timeout: int) -> Tuple[bool, str]:
        """Test with direct OpenCV"""
        return self._test_with_backend(camera_id, timeout, None)
    
    def _test_directshow_backend(self, camera_id: int, timeout: int) -> Tuple[bool, str]:
        """Test with DirectShow backend"""
        return self._test_with_backend(camera_id, timeout, cv2.CAP_DSHOW)
    
    def _test_media_foundation_backend(self, camera_id: int, timeout: int) -> Tuple[bool, str]:
        """Test with Media Foundation backend"""
        return self._test_with_backend(camera_id, timeout, cv2.CAP_MSMF)
    
    def _test_v4l2_backend(self, camera_id: int, timeout: int) -> Tuple[bool, str]:
        """Test with V4L2 backend"""
        return self._test_with_backend(camera_id, timeout, cv2.CAP_V4L2)
    
    def _test_any_backend(self, camera_id: int, timeout: int) -> Tuple[bool, str]:
        """Test with Any backend"""
        return self._test_with_backend(camera_id, timeout, cv2.CAP_ANY)
    
    def _test_with_backend(self, camera_id: int, timeout: int, backend: Optional[int]) -> Tuple[bool, str]:
        """Test camera with specific backend"""
        result = [False]
        exception = [None]
        
        def test_worker():
            try:
                # Force cleanup first
                self.force_cleanup_camera(camera_id)
                
                # Create capture with or without backend
                if backend is not None:
                    cap = cv2.VideoCapture(camera_id, backend)
                else:
                    cap = cv2.VideoCapture(camera_id)
                
                if cap.isOpened():
                    # Test frame read
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        result[0] = True
                    cap.release()
                else:
                    exception[0] = "Camera failed to open"
                    
            except Exception as e:
                exception[0] = str(e)
        
        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            return False, f"Timeout after {timeout}s"
        
        if exception[0]:
            return False, exception[0]
        
        return result[0], "Success"
    
    def initialize_camera_robust(self, camera_id: int, width: int = 640, height: int = 480, 
                               fps: int = 20, timeout: int = 15) -> Optional[cv2.VideoCapture]:
        """Initialize camera with robust fallback strategies"""
        print(f"🚀 Robust initialization of camera {camera_id}...")
        
        # First, test which strategy works
        success, strategy = self.test_camera_with_multiple_strategies(camera_id, timeout=5)
        
        if not success:
            print(f"❌ Camera {camera_id} failed all tests")
            return None
        
        print(f"✅ Camera {camera_id} works with {strategy}, initializing...")
        
        # Now initialize with the working strategy
        backend_map = {
            "Direct OpenCV": None,
            "DirectShow Backend": cv2.CAP_DSHOW,
            "Media Foundation Backend": cv2.CAP_MSMF,
            "V4L2 Backend": cv2.CAP_V4L2,
            "Any Backend": cv2.CAP_ANY
        }
        
        backend = backend_map.get(strategy, None)
        
        result = [None]
        exception = [None]
        
        def init_worker():
            try:
                # Force cleanup first
                self.force_cleanup_camera(camera_id)
                
                # Create capture with working backend
                if backend is not None:
                    cap = cv2.VideoCapture(camera_id, backend)
                else:
                    cap = cv2.VideoCapture(camera_id)
                
                if cap.isOpened():
                    # Test frame read
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Set properties
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        cap.set(cv2.CAP_PROP_FPS, fps)
                        result[0] = cap
                    else:
                        cap.release()
                        exception[0] = "Cannot read frames"
                else:
                    exception[0] = "Camera failed to open"
                    
            except Exception as e:
                exception[0] = str(e)
        
        thread = threading.Thread(target=init_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print(f"⏰ Camera {camera_id} initialization timed out after {timeout}s")
            return None
        
        if exception[0]:
            print(f"❌ Exception initializing camera {camera_id}: {exception[0]}")
            return None
        
        if result[0]:
            print(f"✅ Camera {camera_id} initialized successfully with {strategy}")
            return result[0]
        
        return None
    
    def get_camera_info_robust(self, camera_id: int, timeout: int = 15) -> Dict[str, Any]:
        """Get camera info with robust testing"""
        print(f"📋 Getting robust info for camera {camera_id}...")
        
        # Test camera first
        success, strategy = self.test_camera_with_multiple_strategies(camera_id, timeout=5)
        
        if not success:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': 'Camera failed all tests',
                'strategy': 'None'
            }
        
        # Get info with working strategy
        backend_map = {
            "Direct OpenCV": None,
            "DirectShow Backend": cv2.CAP_DSHOW,
            "Media Foundation Backend": cv2.CAP_MSMF,
            "V4L2 Backend": cv2.CAP_V4L2,
            "Any Backend": cv2.CAP_ANY
        }
        
        backend = backend_map.get(strategy, None)
        
        result = [None]
        exception = [None]
        
        def info_worker():
            try:
                if backend is not None:
                    cap = cv2.VideoCapture(camera_id, backend)
                else:
                    cap = cv2.VideoCapture(camera_id)
                
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    cap.release()
                    
                    result[0] = {
                        'id': camera_id,
                        'name': f'Camera {camera_id}',
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'available': True,
                        'strategy': strategy
                    }
                else:
                    exception[0] = "Camera failed to open"
                    
            except Exception as e:
                exception[0] = str(e)
        
        thread = threading.Thread(target=info_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': 'Timeout',
                'strategy': strategy
            }
        
        if exception[0]:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': exception[0],
                'strategy': strategy
            }
        
        return result[0] if result[0] else {
            'id': camera_id,
            'name': f'Camera {camera_id}',
            'available': False,
            'error': 'Unknown error',
            'strategy': strategy
        }
