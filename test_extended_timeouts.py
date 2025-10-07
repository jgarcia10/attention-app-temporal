#!/usr/bin/env python3
"""
Test script to verify extended timeouts work for camera initialization
"""
import requests
import time
import sys

def test_individual_cameras():
    """Test individual camera endpoints with extended timeouts"""
    print("🔍 Testing Individual Camera Endpoints with Extended Timeouts")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id}...")
        start_time = time.time()
        
        try:
            # Use longer timeout for camera 2, shorter for others
            timeout = 120 if camera_id == 2 else 30
            print(f"⏱️ Using timeout of {timeout}s for camera {camera_id}")
            
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=timeout)
            end_time = time.time()
            
            print(f"⏱️ Actual execution time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id}: {data['available']}")
                print(f"   Backend: {data.get('backend', 'unknown')}")
                print(f"   Timeout used: {data.get('timeout_used', 'unknown')}s")
                if 'info' in data:
                    info = data['info']
                    if info.get('available'):
                        print(f"   Resolution: {info.get('width', 'unknown')}x{info.get('height', 'unknown')}")
                        print(f"   FPS: {info.get('fps', 'unknown')}")
            else:
                print(f"❌ Camera {camera_id} failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ Actual execution time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} error: {e}")

def test_fast_endpoint():
    """Test the fast endpoint with extended timeouts"""
    print("\n⚡ Testing Fast Endpoint with Extended Timeouts")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        start_time = time.time()
        # Use longer timeout for fast endpoint since it tests all cameras
        response = requests.get(f"{base_url}/api/cameras/fast-test", timeout=180)
        end_time = time.time()
        
        print(f"⏱️ Fast endpoint execution time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Fast endpoint successful:")
            for cam in cameras:
                print(f"  - Camera {cam['camera_id']}: {cam['available']} ({cam['backend']}) - timeout: {cam.get('timeout_used', 'unknown')}s")
        else:
            print(f"❌ Fast endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        end_time = time.time()
        print(f"⏱️ Fast endpoint execution time: {end_time - start_time:.2f} seconds")
        print(f"❌ Fast endpoint error: {e}")

def test_simple_endpoint():
    """Test the simple endpoint with extended timeouts"""
    print("\n🔧 Testing Simple Endpoint with Extended Timeouts")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        start_time = time.time()
        # Use longer timeout for simple endpoint since it tests all cameras
        response = requests.get(f"{base_url}/api/cameras/simple-test", timeout=180)
        end_time = time.time()
        
        print(f"⏱️ Simple endpoint execution time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Simple endpoint successful:")
            for cam in cameras:
                print(f"  - Camera {cam['camera_id']}: {cam['available']} ({cam['backend']}) - timeout: {cam.get('timeout_used', 'unknown')}s")
        else:
            print(f"❌ Simple endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        end_time = time.time()
        print(f"⏱️ Simple endpoint execution time: {end_time - start_time:.2f} seconds")
        print(f"❌ Simple endpoint error: {e}")

def main():
    """Main test function"""
    print("🚀 Extended Timeout Camera Test")
    print("=" * 60)
    print("This test verifies that the extended timeouts work for camera initialization")
    print("Expected behavior:")
    print("- Camera 0: Should work quickly (1-2 seconds)")
    print("- Camera 1: Should work in 5-10 seconds")
    print("- Camera 2: Should work in 60-90 seconds (this was the problematic one)")
    print("=" * 60)
    
    # Test individual cameras first
    test_individual_cameras()
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before testing endpoints...")
    time.sleep(5)
    
    # Test fast endpoint
    test_fast_endpoint()
    
    # Wait a bit between tests
    print("\n⏳ Waiting 5 seconds before testing simple endpoint...")
    time.sleep(5)
    
    # Test simple endpoint
    test_simple_endpoint()
    
    print("\n✅ Extended timeout test completed!")
    print("If all cameras are now working, the timeout modifications were successful.")

if __name__ == "__main__":
    main()
