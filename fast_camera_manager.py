#!/usr/bin/env python3
"""
Fast camera manager - optimized for speed
"""
import cv2
import time
from typing import Dict, List, Any, Optional, Tuple


class FastCameraManager:
    def __init__(self):
        """Initialize fast camera manager"""
        self.camera_cache = {}
    
    def test_camera_fast(self, camera_id: int) -> Tuple[bool, str]:
        """Test camera with fastest possible method"""
        print(f"⚡ Fast test camera {camera_id}...")
        
        try:
            # Try only the most common backends
            backends = [
                (None, "Default"),
                (cv2.CAP_DSHOW, "DirectShow")
            ]
            
            for backend, name in backends:
                try:
                    if backend is not None:
                        cap = cv2.VideoCapture(camera_id, backend)
                    else:
                        cap = cv2.VideoCapture(camera_id)
                    
                    if cap.isOpened():
                        # Quick frame test
                        ret, frame = cap.read()
                        cap.release()
                        
                        if ret and frame is not None:
                            print(f"✅ Camera {camera_id} works with {name}")
                            return True, name
                    
                except Exception as e:
                    print(f"❌ Camera {camera_id} failed with {name}: {e}")
                    continue
            
            return False, "All backends failed"
            
        except Exception as e:
            print(f"❌ Exception testing camera {camera_id}: {e}")
            return False, str(e)
    
    def get_camera_info_fast(self, camera_id: int) -> Dict[str, Any]:
        """Get camera info with fastest method"""
        print(f"⚡ Fast info camera {camera_id}...")
        
        # Test camera first
        success, backend = self.test_camera_fast(camera_id)
        
        if not success:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': 'Camera failed fast test',
                'backend': 'None'
            }
        
        # Get basic info
        try:
            backend_map = {
                "Default": None,
                "DirectShow": cv2.CAP_DSHOW
            }
            
            backend_val = backend_map.get(backend, None)
            
            if backend_val is not None:
                cap = cv2.VideoCapture(camera_id, backend_val)
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
                    'backend': backend
                }
            else:
                return {
                    'id': camera_id,
                    'name': f'Camera {camera_id}',
                    'available': False,
                    'error': 'Camera failed to open',
                    'backend': backend
                }
                
        except Exception as e:
            return {
                'id': camera_id,
                'name': f'Camera {camera_id}',
                'available': False,
                'error': str(e),
                'backend': backend
            }
    
    def initialize_camera_fast(self, camera_id: int, width: int = 640, height: int = 480, 
                              fps: int = 20) -> Optional[cv2.VideoCapture]:
        """Initialize camera with fastest method"""
        print(f"⚡ Fast init camera {camera_id}...")
        
        # Test which backend works
        success, backend = self.test_camera_fast(camera_id)
        
        if not success:
            print(f"❌ Camera {camera_id} failed fast test")
            return None
        
        # Initialize with working backend
        try:
            backend_map = {
                "Default": None,
                "DirectShow": cv2.CAP_DSHOW
            }
            
            backend_val = backend_map.get(backend, None)
            
            if backend_val is not None:
                cap = cv2.VideoCapture(camera_id, backend_val)
            else:
                cap = cv2.VideoCapture(camera_id)
            
            if cap.isOpened():
                # Quick frame test
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Set properties
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    print(f"✅ Camera {camera_id} initialized fast with {backend}")
                    return cap
                else:
                    cap.release()
                    print(f"❌ Camera {camera_id} cannot read frames")
            else:
                print(f"❌ Camera {camera_id} failed to open")
                
        except Exception as e:
            print(f"❌ Exception initializing camera {camera_id}: {e}")
        
        return None
