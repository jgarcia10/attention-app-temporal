#!/usr/bin/env python3
"""
Test script for specific camera initialization issues
"""
import requests
import json
import time

def test_camera_1_and_2():
    """Test cameras 1 and 2 specifically"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Cameras 1 and 2 Specifically")
    print("=" * 50)
    
    # Test camera 1
    print("\n📹 Testing Camera 1...")
    try:
        start_response = requests.post(f"{base_url}/api/multi-camera/start", 
                                     json={
                                         "camera_ids": [1],
                                         "width": 640,
                                         "height": 480,
                                         "fps": 20
                                     }, timeout=30)
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            print(f"Camera 1 start response: {start_data}")
            
            started_cameras = start_data.get('started_cameras', [])
            failed_cameras = start_data.get('failed_cameras', [])
            
            if 1 in started_cameras:
                print("✅ Camera 1 started successfully")
                
                # Stop camera 1
                stop_response = requests.post(f"{base_url}/api/multi-camera/stop", 
                                            json={}, 
                                            headers={'Content-Type': 'application/json'},
                                            timeout=10)
                print(f"Camera 1 stop response: {stop_response.status_code}")
            else:
                print("❌ Camera 1 failed to start")
                if 1 in failed_cameras:
                    print("Camera 1 is in failed cameras list")
        else:
            print(f"❌ Camera 1 start request failed: {start_response.status_code}")
            print(f"Response: {start_response.text}")
            
    except Exception as e:
        print(f"❌ Exception testing camera 1: {e}")
    
    time.sleep(2)
    
    # Test camera 2
    print("\n📹 Testing Camera 2...")
    try:
        start_response = requests.post(f"{base_url}/api/multi-camera/start", 
                                     json={
                                         "camera_ids": [2],
                                         "width": 640,
                                         "height": 480,
                                         "fps": 20
                                     }, timeout=30)
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            print(f"Camera 2 start response: {start_data}")
            
            started_cameras = start_data.get('started_cameras', [])
            failed_cameras = start_data.get('failed_cameras', [])
            
            if 2 in started_cameras:
                print("✅ Camera 2 started successfully")
                
                # Stop camera 2
                stop_response = requests.post(f"{base_url}/api/multi-camera/stop", 
                                            json={}, 
                                            headers={'Content-Type': 'application/json'},
                                            timeout=10)
                print(f"Camera 2 stop response: {stop_response.status_code}")
            else:
                print("❌ Camera 2 failed to start")
                if 2 in failed_cameras:
                    print("Camera 2 is in failed cameras list")
        else:
            print(f"❌ Camera 2 start request failed: {start_response.status_code}")
            print(f"Response: {start_response.text}")
            
    except Exception as e:
        print(f"❌ Exception testing camera 2: {e}")

def test_camera_detection():
    """Test camera detection to see what cameras are actually available"""
    base_url = "http://localhost:5000"
    
    print("\n🔍 Testing Camera Detection")
    print("=" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/cameras", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Found {len(cameras)} cameras:")
            for cam in cameras:
                print(f"  - Camera {cam['id']}: {cam['name']} ({cam['width']}x{cam['height']}) - Available: {cam['available']}")
        else:
            print(f"❌ Camera detection failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception in camera detection: {e}")

def test_individual_camera_endpoints():
    """Test individual camera test endpoints"""
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Individual Camera Test Endpoints")
    print("=" * 50)
    
    for camera_id in [0, 1, 2]:
        print(f"\n📹 Testing camera {camera_id} test endpoint...")
        try:
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Camera {camera_id} test result: {data}")
            else:
                print(f"❌ Camera {camera_id} test failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception testing camera {camera_id}: {e}")

if __name__ == "__main__":
    test_camera_detection()
    test_individual_camera_endpoints()
    test_camera_1_and_2()
