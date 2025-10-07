#!/usr/bin/env python3
"""
Test the application's camera endpoints directly
"""
import requests
import json
import time

def test_app_camera_endpoints():
    """Test the application's camera endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Application Camera Endpoints")
    print("=" * 50)
    
    # Test 1: Camera detection
    print("\n📋 Step 1: Testing camera detection...")
    try:
        response = requests.get(f"{base_url}/api/cameras", timeout=30)
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Found {len(cameras)} cameras:")
            for cam in cameras:
                print(f"  - Camera {cam['id']}: {cam['name']} - Available: {cam['available']}")
        else:
            print(f"❌ Camera detection failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception in camera detection: {e}")
    
    # Test 2: Individual camera tests
    print(f"\n🧪 Step 2: Testing individual cameras...")
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id} endpoint...")
        try:
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=20)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id} test result: {data}")
            else:
                print(f"❌ Camera {camera_id} test failed: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Exception testing camera {camera_id}: {e}")
    
    # Test 3: Multi-camera start
    print(f"\n🚀 Step 3: Testing multi-camera start...")
    try:
        response = requests.post(f"{base_url}/api/multi-camera/start", 
                               json={
                                   "camera_ids": [0, 1, 2],
                                   "width": 640,
                                   "height": 480,
                                   "fps": 20
                               }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Multi-camera start result: {data}")
            
            started_cameras = data.get('started_cameras', [])
            failed_cameras = data.get('failed_cameras', [])
            
            print(f"📊 Started cameras: {started_cameras}")
            print(f"📊 Failed cameras: {failed_cameras}")
            
            # Test stream endpoint
            if started_cameras:
                print(f"\n📺 Step 4: Testing stream endpoint...")
                stream_url = f"{base_url}/api/multi-camera/stream?cameras={','.join(map(str, started_cameras))}&w=640&h=480&fps=20"
                print(f"Stream URL: {stream_url}")
                
                stream_response = requests.get(stream_url, stream=True, timeout=10)
                if stream_response.status_code == 200:
                    print("✅ Stream endpoint responding")
                    # Try to read a few chunks
                    chunk_count = 0
                    for chunk in stream_response.iter_content(chunk_size=1024):
                        chunk_count += 1
                        if chunk_count >= 3:  # Read 3 chunks
                            break
                    print(f"✅ Successfully read {chunk_count} chunks from stream")
                else:
                    print(f"❌ Stream endpoint failed: {stream_response.status_code}")
            
            # Stop cameras
            print(f"\n🛑 Step 5: Stopping cameras...")
            stop_response = requests.post(f"{base_url}/api/multi-camera/stop", 
                                        json={}, 
                                        headers={'Content-Type': 'application/json'},
                                        timeout=10)
            print(f"Stop response: {stop_response.status_code}")
            
        else:
            print(f"❌ Multi-camera start failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception in multi-camera test: {e}")

if __name__ == "__main__":
    test_app_camera_endpoints()
