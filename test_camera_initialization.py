#!/usr/bin/env python3
"""
Test script to verify camera initialization timeouts work correctly
"""
import sys
import os
import time
import requests
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.simple_camera_manager import SimpleCameraManager
from services.multi_camera_streamer import MultiCameraStreamer
from core.pipeline import AttentionPipeline

def test_direct_initialization():
    """Test direct camera initialization with extended timeouts"""
    print("🔧 Testing Direct Camera Initialization")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = AttentionPipeline(
        model_path='./models/yolov8n.pt',
        conf_threshold=0.4,
        yaw_threshold=25,
        pitch_threshold=20
    )
    
    # Test simple camera manager
    simple_manager = SimpleCameraManager()
    
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id} initialization...")
        start_time = time.time()
        
        try:
            cap = simple_manager.initialize_camera_simple(camera_id, 640, 480, 20)
            end_time = time.time()
            
            print(f"⏱️ Initialization time: {end_time - start_time:.2f} seconds")
            
            if cap:
                print(f"✅ Camera {camera_id} initialized successfully")
                cap.release()
            else:
                print(f"❌ Camera {camera_id} failed to initialize")
                
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ Initialization time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} initialization error: {e}")

def test_multi_camera_streamer():
    """Test multi-camera streamer initialization"""
    print("\n🚀 Testing Multi-Camera Streamer Initialization")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = AttentionPipeline(
        model_path='./models/yolov8n.pt',
        conf_threshold=0.4,
        yaw_threshold=25,
        pitch_threshold=20
    )
    
    # Test multi-camera streamer
    multi_streamer = MultiCameraStreamer(pipeline, max_parallel_workers=4)
    
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id} with multi-streamer...")
        start_time = time.time()
        
        try:
            success = multi_streamer.start_camera_stream(camera_id, 640, 480, 20)
            end_time = time.time()
            
            print(f"⏱️ Initialization time: {end_time - start_time:.2f} seconds")
            
            if success:
                print(f"✅ Camera {camera_id} started successfully")
                # Stop the camera
                multi_streamer.stop_camera_stream(camera_id)
            else:
                print(f"❌ Camera {camera_id} failed to start")
                
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ Initialization time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} initialization error: {e}")

def test_http_endpoints():
    """Test HTTP endpoints with extended timeouts"""
    print("\n🌐 Testing HTTP Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test individual camera endpoints
    for camera_id in range(3):
        print(f"\n📹 Testing HTTP endpoint for camera {camera_id}...")
        start_time = time.time()
        
        try:
            # Use longer timeout for camera 2, shorter for others
            timeout = 120 if camera_id == 2 else 30
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=timeout)
            end_time = time.time()
            
            print(f"⏱️ HTTP response time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id}: {data['available']} (backend: {data.get('backend', 'unknown')})")
            else:
                print(f"❌ Camera {camera_id} failed: {response.status_code}")
                
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ HTTP response time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} HTTP error: {e}")
    
    # Test multi-camera start endpoint
    print(f"\n🚀 Testing multi-camera start endpoint...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{base_url}/api/multi-camera/start", 
                               json={"cameras": [0, 1, 2], "width": 640, "height": 480, "fps": 20},
                               timeout=180)
        end_time = time.time()
        
        print(f"⏱️ Multi-camera start time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Multi-camera start successful:")
            print(f"   Started cameras: {data.get('started_cameras', [])}")
            print(f"   Failed cameras: {data.get('failed_cameras', [])}")
            
            # Stop the cameras
            stop_response = requests.post(f"{base_url}/api/multi-camera/stop", 
                                        json={"cameras": [0, 1, 2]}, timeout=30)
            if stop_response.status_code == 200:
                print("✅ Multi-camera stop successful")
        else:
            print(f"❌ Multi-camera start failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        end_time = time.time()
        print(f"⏱️ Multi-camera start time: {end_time - start_time:.2f} seconds")
        print(f"❌ Multi-camera start error: {e}")

def main():
    """Main test function"""
    print("🔍 Camera Initialization Timeout Test")
    print("=" * 60)
    print("This test verifies that camera initialization timeouts work correctly")
    print("Expected behavior:")
    print("- Camera 0: Should initialize quickly (1-2 seconds)")
    print("- Camera 1: Should initialize in 5-10 seconds")
    print("- Camera 2: Should initialize in 60-90 seconds (extended timeout)")
    print("=" * 60)
    
    # Test direct initialization
    test_direct_initialization()
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before testing multi-camera streamer...")
    time.sleep(5)
    
    # Test multi-camera streamer
    test_multi_camera_streamer()
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before testing HTTP endpoints...")
    time.sleep(5)
    
    # Test HTTP endpoints
    test_http_endpoints()
    
    print("\n✅ Camera initialization timeout test completed!")
    print("If all cameras initialized successfully, the timeout modifications were successful.")

if __name__ == "__main__":
    main()
