#!/usr/bin/env python3
"""
Debug HTTP vs Direct execution
"""
import sys
import os
import time
import requests
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fast_camera_manager import FastCameraManager

def test_direct_execution():
    """Test direct execution"""
    print("🔧 Testing Direct Execution")
    print("=" * 30)
    
    manager = FastCameraManager()
    
    for camera_id in range(3):
        print(f"\n📹 Direct test camera {camera_id}...")
        start_time = time.time()
        
        success, backend = manager.test_camera_fast(camera_id)
        
        end_time = time.time()
        print(f"⏱️ Direct execution time: {end_time - start_time:.2f} seconds")
        print(f"✅ Camera {camera_id}: {success} ({backend})")

def test_http_execution():
    """Test HTTP execution"""
    print("\n🌐 Testing HTTP Execution")
    print("=" * 30)
    
    base_url = "http://localhost:5000"
    
    for camera_id in range(3):
        print(f"\n📹 HTTP test camera {camera_id}...")
        start_time = time.time()
        
        try:
            response = requests.get(f"{base_url}/api/cameras/{camera_id}/test", timeout=10)
            end_time = time.time()
            
            print(f"⏱️ HTTP execution time: {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Camera {camera_id}: {data['available']}")
            else:
                print(f"❌ Camera {camera_id} failed: {response.status_code}")
        except Exception as e:
            end_time = time.time()
            print(f"⏱️ HTTP execution time: {end_time - start_time:.2f} seconds")
            print(f"❌ Camera {camera_id} error: {e}")

def test_fast_endpoint():
    """Test the fast endpoint"""
    print("\n⚡ Testing Fast Endpoint")
    print("=" * 30)
    
    base_url = "http://localhost:5000"
    
    print("📹 Testing fast endpoint...")
    start_time = time.time()
    
    try:
        response = requests.get(f"{base_url}/api/cameras/fast-test", timeout=15)
        end_time = time.time()
        
        print(f"⏱️ Fast endpoint time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('cameras', [])
            print(f"✅ Fast endpoint successful:")
            for cam in cameras:
                print(f"  - Camera {cam['camera_id']}: {cam['available']} ({cam['backend']})")
        else:
            print(f"❌ Fast endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        end_time = time.time()
        print(f"⏱️ Fast endpoint time: {end_time - start_time:.2f} seconds")
        print(f"❌ Fast endpoint error: {e}")

def main():
    """Main test function"""
    print("🔍 HTTP vs Direct Execution Debug")
    print("=" * 50)
    
    # Test direct execution first
    test_direct_execution()
    
    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Test HTTP execution
    test_http_execution()
    
    # Wait a bit
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Test fast endpoint
    test_fast_endpoint()

if __name__ == "__main__":
    main()
