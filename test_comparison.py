#!/usr/bin/env python3
"""
Test comparison between different approaches
"""
import requests
import time

def test_simple_endpoint():
    """Test the simple endpoint"""
    print("🔧 Testing Simple Endpoint")
    print("=" * 30)
    
    base_url = "http://localhost:5000"
    
    try:
        start_time = time.time()
        # Use longer timeout for simple endpoint since it tests all cameras
        response = requests.get(f"{base_url}/api/cameras/simple-test", timeout=180)
        end_time = time.time()
        
        print(f"⏱️ Simple endpoint time: {end_time - start_time:.2f} seconds")
        
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
        print(f"⏱️ Simple endpoint time: {end_time - start_time:.2f} seconds")
        print(f"❌ Simple endpoint error: {e}")

def test_fast_endpoint():
    """Test the fast endpoint"""
    print("\n⚡ Testing Fast Endpoint")
    print("=" * 30)
    
    base_url = "http://localhost:5000"
    
    try:
        start_time = time.time()
        # Use longer timeout for fast endpoint since it tests all cameras
        response = requests.get(f"{base_url}/api/cameras/fast-test", timeout=180)
        end_time = time.time()
        
        print(f"⏱️ Fast endpoint time: {end_time - start_time:.2f} seconds")
        
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
        print(f"⏱️ Fast endpoint time: {end_time - start_time:.2f} seconds")
        print(f"❌ Fast endpoint error: {e}")

def test_individual_endpoints():
    """Test individual camera endpoints"""
    print("\n📹 Testing Individual Endpoints")
    print("=" * 30)
    
    base_url = "http://localhost:5000"
    
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id}...")
        try:
            start_time = time.time()
            # Use longer timeout for camera 2, shorter for others
            timeout = 120 if camera_id == 2 else 30
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=timeout)
            end_time = time.time()
            
            print(f"⏱️ Camera {camera_id} time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id}: {data['available']} (backend: {data.get('backend', 'unknown')})")
            else:
                print(f"❌ Camera {camera_id} failed: {response.status_code}")
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ Camera {camera_id} time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} error: {e}")

def main():
    """Main test function"""
    print("🔍 Endpoint Comparison Test")
    print("=" * 50)
    
    # Test simple endpoint
    test_simple_endpoint()
    
    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Test fast endpoint
    test_fast_endpoint()
    
    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Test individual endpoints
    test_individual_endpoints()

if __name__ == "__main__":
    main()
