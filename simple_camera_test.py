#!/usr/bin/env python3
"""
Simple camera test without PowerShell commands
"""
import cv2
import time
import platform

def test_camera_simple(camera_id: int, timeout: int = 5):
    """Test camera with simple approach"""
    print(f"📹 Testing camera {camera_id} (simple method)...")
    
    # Try different backends
    backends = [
        (None, "Default"),
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
        (cv2.CAP_ANY, "Any")
    ]
    
    for backend, name in backends:
        print(f"  🧪 Trying {name} backend...")
        
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
                    cap.release()
                    return True, name
                else:
                    print(f"    ❌ Camera {camera_id} cannot read frames with {name}")
                
                cap.release()
            else:
                print(f"    ❌ Camera {camera_id} failed to open with {name}")
                
        except Exception as e:
            print(f"    ❌ Exception with {name}: {e}")
    
    return False, "All backends failed"

def main():
    """Main test function"""
    print("🔍 Simple Camera Test (No PowerShell)")
    print("=" * 40)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"OpenCV Version: {cv2.__version__}")
    
    # Test cameras 0, 1, 2
    for camera_id in range(3):
        print(f"\n📹 Testing Camera {camera_id}")
        print("-" * 20)
        
        success, backend = test_camera_simple(camera_id, timeout=5)
        
        if success:
            print(f"✅ Camera {camera_id} works with {backend}")
        else:
            print(f"❌ Camera {camera_id} failed: {backend}")
        
        time.sleep(1)  # Small delay between cameras

if __name__ == "__main__":
    main()
