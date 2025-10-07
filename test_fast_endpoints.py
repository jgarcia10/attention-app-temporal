#!/usr/bin/env python3
"""
Test fast camera endpoints
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fast_camera_manager import FastCameraManager

def test_fast_camera_manager():
    """Test the fast camera manager"""
    print("⚡ Testing Fast Camera Manager")
    print("=" * 40)
    
    manager = FastCameraManager()
    
    # Test cameras 0, 1, 2
    for camera_id in range(3):
        print(f"\n📹 Testing Camera {camera_id}")
        print("-" * 20)
        
        # Fast test
        print(f"⚡ Fast test camera {camera_id}...")
        success, backend = manager.test_camera_fast(camera_id)
        
        if success:
            print(f"✅ Camera {camera_id} works with {backend}")
            
            # Fast info
            print(f"⚡ Fast info camera {camera_id}...")
            info = manager.get_camera_info_fast(camera_id)
            print(f"📊 Camera {camera_id} info: {info}")
            
            # Fast init
            print(f"⚡ Fast init camera {camera_id}...")
            cap = manager.initialize_camera_fast(camera_id, 640, 480, 20)
            
            if cap:
                print(f"✅ Camera {camera_id} initialized successfully")
                cap.release()
            else:
                print(f"❌ Camera {camera_id} failed to initialize")
        else:
            print(f"❌ Camera {camera_id} failed: {backend}")
        
        print()

if __name__ == "__main__":
    test_fast_camera_manager()
