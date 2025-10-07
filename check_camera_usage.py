#!/usr/bin/env python3
"""
Check what applications are using cameras
"""
import cv2
import time
import platform
import subprocess

def check_camera_usage():
    """Check what's using the cameras"""
    print("🔍 Camera Usage Checker")
    print("=" * 30)
    
    # Test each camera
    for camera_id in range(3):
        print(f"\n📹 Checking Camera {camera_id}")
        print("-" * 20)
        
        # Try to open camera
        try:
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                print(f"✅ Camera {camera_id} is available")
                cap.release()
            else:
                print(f"❌ Camera {camera_id} is NOT available")
        except Exception as e:
            print(f"❌ Camera {camera_id} error: {e}")
    
    # On Windows, try to list camera devices
    if platform.system().lower() == "windows":
        print(f"\n🖥️ Windows Camera Information")
        print("-" * 30)
        
        try:
            # Simple device listing
            result = subprocess.run([
                'powershell', '-Command',
                'Get-PnpDevice -Class Camera | Select-Object FriendlyName, Status | Format-Table -AutoSize'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("📋 Camera devices:")
                print(result.stdout)
            else:
                print(f"❌ Could not list camera devices: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error listing camera devices: {e}")
    
    print(f"\n💡 Troubleshooting Tips:")
    print("-" * 20)
    print("1. Close any camera applications (Camera app, Skype, Teams, etc.)")
    print("2. Check Windows Camera privacy settings")
    print("3. Restart the backend application")
    print("4. Try running as administrator")
    print("5. Check Device Manager for camera issues")

if __name__ == "__main__":
    check_camera_usage()
