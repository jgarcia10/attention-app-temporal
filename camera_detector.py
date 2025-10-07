"""
Camera detection utility for finding available cameras
"""
import cv2
import time
import platform
import subprocess
import re
from typing import List, Dict, Any
from services.simple_camera_manager import SimpleCameraManager


class CameraDetector:
    def __init__(self):
        """Initialize camera detector"""
        self.available_cameras = []
        self.simple_camera_manager = SimpleCameraManager()
        self.camera_info = {}
    
    def detect_cameras(self, max_cameras: int = 5) -> List[Dict[str, Any]]:
        """
        Detect all available cameras on the system
        
        Args:
            max_cameras: Maximum number of cameras to test
            
        Returns:
            List of camera information dictionaries
        """
        cameras = []
        system = platform.system().lower()
        
        print(f"Detecting cameras on {system} system...")
        
        # Try different backends for better compatibility (reduced for speed)
        backends = [cv2.CAP_ANY]
        if system == "windows":
            # Windows-specific backends (try most common first)
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        elif system == "linux":
            # Linux-specific backends
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
        
        for backend in backends:
            print(f"Trying backend: {backend}")
            cameras_found = self._detect_cameras_with_backend(backend, max_cameras)
            if cameras_found:
                cameras.extend(cameras_found)
                break  # Use first working backend
        
        # If no cameras found with specific backends, try default method
        if not cameras:
            print("No cameras found with specific backends, trying default method...")
            cameras = self._detect_cameras_default(max_cameras)
        
        self.available_cameras = cameras
        print(f"Total cameras found: {len(cameras)}")
        return cameras
    
    def _detect_cameras_with_backend(self, backend: int, max_cameras: int) -> List[Dict[str, Any]]:
        """Detect cameras using a specific backend"""
        cameras = []
        system = platform.system().lower()
        
        for i in range(max_cameras):
            try:
                # Try to open camera with specific backend
                cap = cv2.VideoCapture(i, backend)
                
                if cap.isOpened():
                    # Quick test - try to read a frame with timeout
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Get camera properties
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        # Try to get camera name if possible (skip on Windows for speed)
                        if system == "windows":
                            camera_name = f'Camera {i}'
                        else:
                            camera_name = self._get_camera_name(i, backend)
                        
                        camera_info = {
                            'id': i,
                            'name': camera_name,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'backend': backend,
                            'available': True
                        }
                        cameras.append(camera_info)
                        print(f"Found camera {i} ({camera_name}): {width}x{height} @ {fps} FPS")
                    
                cap.release()
                # Reduced delay for faster detection
                time.sleep(0.05 if system == "windows" else 0.1)
                
            except Exception as e:
                print(f"Error testing camera {i} with backend {backend}: {e}")
                continue
        
        return cameras
    
    def _detect_cameras_default(self, max_cameras: int) -> List[Dict[str, Any]]:
        """Default camera detection method"""
        cameras = []
        
        for i in range(max_cameras):
            try:
                # Try to open camera
                cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    # Test if we can read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Get camera properties
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        camera_info = {
                            'id': i,
                            'name': f'Camera {i}',
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'available': True
                        }
                        cameras.append(camera_info)
                        print(f"Found camera {i}: {width}x{height} @ {fps} FPS")
                    
                cap.release()
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error testing camera {i}: {e}")
                continue
        
        return cameras
    
    def _get_camera_name(self, camera_id: int, backend: int) -> str:
        """Try to get a more descriptive camera name"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Try to get camera name from Windows registry or device manager
                return self._get_windows_camera_name(camera_id)
            elif system == "linux":
                # Try to get camera name from /dev/video* devices
                return self._get_linux_camera_name(camera_id)
            else:
                return f'Camera {camera_id}'
                
        except Exception:
            return f'Camera {camera_id}'
    
    def _get_windows_camera_name(self, camera_id: int) -> str:
        """Get camera name on Windows"""
        try:
            # Try to get camera name from Windows device manager
            result = subprocess.run([
                'powershell', '-Command',
                f'Get-PnpDevice -Class Camera | Select-Object -Index {camera_id} | Select-Object -ExpandProperty FriendlyName'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                name = result.stdout.strip()
                return name if name else f'Camera {camera_id}'
            else:
                return f'Camera {camera_id}'
                
        except Exception:
            return f'Camera {camera_id}'
    
    def _get_linux_camera_name(self, camera_id: int) -> str:
        """Get camera name on Linux"""
        try:
            # Try to get camera name from v4l2
            result = subprocess.run([
                'v4l2-ctl', '--list-devices'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse v4l2 output to find camera names
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if f'/dev/video{camera_id}' in line:
                        # Look for the device name in previous lines
                        for j in range(max(0, i-3), i):
                            if lines[j].strip() and not lines[j].startswith('/dev/'):
                                return lines[j].strip()
                return f'Camera {camera_id}'
            else:
                return f'Camera {camera_id}'
                
        except Exception:
            return f'Camera {camera_id}'
    
    def test_camera(self, camera_id: int, timeout: int = 15) -> bool:
        """
        Test if a specific camera is available with robust testing
        
        Args:
            camera_id: Camera index to test
            timeout: Timeout in seconds
            
        Returns:
            True if camera is available and working
        """
        print(f"🧪 Testing camera {camera_id} with simple manager...")
        success, backend = self.simple_camera_manager.test_camera_simple(camera_id, timeout=5)
        
        if success:
            print(f"✅ Camera {camera_id} test passed with {backend}")
            return True
        else:
            print(f"❌ Camera {camera_id} test failed: {backend}")
            return False
    
    def get_camera_info(self, camera_id: int, timeout: int = 15) -> Dict[str, Any]:
        """
        Get detailed information about a specific camera with robust testing
        
        Args:
            camera_id: Camera index
            timeout: Timeout in seconds
            
        Returns:
            Camera information dictionary
        """
        print(f"📋 Getting simple info for camera {camera_id}...")
        return self.simple_camera_manager.get_camera_info_simple(camera_id, timeout)
