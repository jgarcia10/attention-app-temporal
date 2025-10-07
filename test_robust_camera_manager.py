#!/usr/bin/env python3
"""
Test script for robust camera manager
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.robust_camera_manager import RobustCameraManager

def test_robust_camera_manager():
    """Test the robust camera manager"""
    print("🔍 Testing Robust Camera Manager")
    print("=" * 50)
    
    manager = RobustCameraManager()
    
    # Test cameras 0, 1, 2
    for camera_id in range(3):
        print(f"\n📹 Testing Camera {camera_id}")
        print("-" * 30)
        
        # Test with multiple strategies
        print(f"🧪 Testing camera {camera_id} with multiple strategies...")
        success, strategy = manager.test_camera_with_multiple_strategies(camera_id, timeout=10)
        
        if success:
            print(f"✅ Camera {camera_id} works with {strategy}")
            
            # Get camera info
            print(f"📋 Getting camera {camera_id} info...")
            info = manager.get_camera_info_robust(camera_id, timeout=10)
            print(f"📊 Camera {camera_id} info: {info}")
            
            # Try to initialize
            print(f"🚀 Initializing camera {camera_id}...")
            cap = manager.initialize_camera_robust(camera_id, 640, 480, 20, timeout=10)
            
            if cap:
                print(f"✅ Camera {camera_id} initialized successfully")
                cap.release()
            else:
                print(f"❌ Camera {camera_id} failed to initialize")
        else:
            print(f"❌ Camera {camera_id} failed all tests: {strategy}")
        
        print()

if __name__ == "__main__":
    test_robust_camera_manager()
