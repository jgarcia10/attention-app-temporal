#!/usr/bin/env python3
"""
Simple camera manager - since simple tests work, use simple approach
"""
import cv2
import time
import threading
from typing import Dict, List, Any, Optional, Tuple


class SimpleCameraManager:
    def __init__(self):
        """Initialize simple camera manager"""
        pass
    
    def test_camera_simple(self, camera_id: int, timeout: int = 5) -> Tuple[bool, str]:
        """Test camera with simple approach and timeout support"""
        print(f"🧪 Testing camera {camera_id} (simple method) with {timeout}s timeout...")
        
        # Try different backends (same as simple_camera_test.py)
        backends = [
            (None, "Default"),
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (cv2.CAP_ANY, "Any")
        ]
        
        for backend, name in backends:
            print(f"  🧪 Trying {name} backend...")
            
            try:
                # Use threading with timeout to prevent hanging
                result = [False, ""]
                exception_occurred = [False]
                
                def test_backend():
                    try:
                        if backend is not None:
                            cap = cv2.VideoCapture(camera_id, backend)
                        else:
                            cap = cv2.VideoCapture(camera_id)
                        
                        if cap.isOpened():
                            print(f"    ✅ Camera {camera_id} opened with {name}")
                            
                            # Try to read a frame
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                print(f"    ✅ Camera {camera_id} can read frames: {frame.shape}")
                                result[0] = True
                                result[1] = name
                            else:
                                print(f"    ❌ Camera {camera_id} cannot read frames with {name}")
                            
                            cap.release()
                        else:
                            print(f"    ❌ Camera {camera_id} failed to open with {name}")
                    except Exception as e:
                        print(f"    ❌ Exception with {name}: {e}")
                        exception_occurred[0] = True
                
                # Run test in thread with timeout
                test_thread = threading.Thread(target=test_backend)
                test_thread.daemon = True
                test_thread.start()
                test_thread.join(timeout=timeout)
                
                if test_thread.is_alive():
                    print(f"    ⏰ Camera {camera_id} test timed out after {timeout}s with {name}")
                    continue
                
                if exception_occurred[0]:
                    continue
                
                if result[0]:
                    return result[0], result[1]
                    
            except Exception as e:
                print(f"    ❌ Exception with {name}: {e}")
        
        return False, "All backends failed or timed out"
    
    def initialize_camera_simple(self, camera_id: int, width: int = 640, height: int = 480, 
                               fps: int = 20, timeout: int = 10) -> Optional[cv2.VideoCapture]:
        """Initialize camera with simple approach"""
        print(f"🚀 Simple initialization of camera {camera_id}...")
        
        # First test which backend works
        success, backend_name = self.test_camera_simple(camera_id, timeout=3)
        
        if not success:
            print(f"❌ Camera {camera_id} failed simple test")
            return None
        
        print(f"✅ Camera {camera_id} works with {backend_name}, initializing...")
        
        # Map backend names to actual backends
        backend_map = {
            "Default": None,
            "DirectShow": cv2.CAP_DSHOW,
            "Media Foundation": cv2.CAP_MSMF,
            "Any": cv2.CAP_ANY
        }
        
        backend = backend_map.get(backend_name, None)
        
        # Initialize with working backend
        try:
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
                    print(f"✅ Camera {camera_id} initialized successfully with {backend_name}")
                    return cap
                else:
                    cap.release()
                    print(f"❌ Camera {camera_id} cannot read frames during initialization")
            else:
                print(f"❌ Camera {camera_id} failed to open during initialization")
                
        except Exception as e:
            print(f"❌ Exception initializing camera {camera_id}: {e}")
        
        return None
    
    def get_camera_info_simple(self, camera_id: int, timeout: int = 10) -> Dict[str, Any]:
        """Get camera info with simple approach"""
        print(f"📋 Getting simple info for camera {camera_id}...")
        
        # Test camera first
        success, backend_name = self.test_camera_simple(camera_id, timeout=3)
        
        if not success:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': 'Camera failed simple test',
                'backend': 'None'
            }
        
        # Get info with working backend
        backend_map = {
            "Default": None,
            "DirectShow": cv2.CAP_DSHOW,
            "Media Foundation": cv2.CAP_MSMF,
            "Any": cv2.CAP_ANY
        }
        
        backend = backend_map.get(backend_name, None)
        
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
                
                return {
                    'id': camera_id,
                    'name': f'Camera {camera_id}',
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'available': True,
                    'backend': backend_name
                }
            else:
                return {
                    'id': camera_id,
                    'name': f'Camera {camera_id}',
                    'available': False,
                    'error': 'Camera failed to open',
                    'backend': backend_name
                }
                
        except Exception as e:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': str(e),
                'backend': backend_name
            }
