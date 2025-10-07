#!/usr/bin/env python3
"""
Test fast API endpoints
"""
import requests
import time

def test_fast_api():
    """Test fast API endpoints"""
    base_url = "http://localhost:5000"
    
    print("⚡ Testing Fast API Endpoints")
    print("=" * 40)
    
    # Test 1: Basic API test
    print("\n📋 Step 1: Basic API test...")
    try:
        response = requests.get(f"{base_url}/api/test", timeout=5)
        if response.status_code == 200:
            print("✅ Basic API working")
        else:
            print(f"❌ Basic API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic API error: {e}")
    
    # Test 2: Fast camera test endpoint
    print("\n⚡ Step 2: Fast camera test endpoint...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/cameras/fast-test", timeout=10)
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Fast camera test successful:")
            for cam in cameras:
                print(f"  - Camera {cam['camera_id']}: {cam['available']} ({cam['backend']})")
        else:
            print(f"❌ Fast camera test failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Fast camera test error: {e}")
    
    # Test 3: Individual camera tests (fast)
    print(f"\n⚡ Step 3: Individual camera tests...")
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id}...")
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=5)
            end_time = time.time()
            
            print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id}: {data['available']}")
            else:
                print(f"❌ Camera {camera_id} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Camera {camera_id} error: {e}")

if __name__ == "__main__":
    test_fast_api()
