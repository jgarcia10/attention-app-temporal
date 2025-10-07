#!/usr/bin/env python3
"""
Camera cleanup script to force release all camera resources
"""
import cv2
import time
import platform
import subprocess
import gc

def cleanup_all_cameras():
    """Force cleanup of all camera resources"""
    print("🧹 Camera Cleanup Script")
    print("=" * 30)
    
    # Try to release all possible camera indices
    for camera_id in range(10):  # Try up to 10 cameras
        print(f"🧹 Cleaning camera {camera_id}...")
        
        for attempt in range(3):  # Try 3 times per camera
            try:
                cap = cv2.VideoCapture(camera_id)
                if cap.isOpened():
                    cap.release()
                    print(f"✅ Released camera {camera_id} (attempt {attempt + 1})")
                else:
                    print(f"⚠️ Camera {camera_id} not opened (attempt {attempt + 1})")
                break
            except Exception as e:
                print(f"❌ Error releasing camera {camera_id} (attempt {attempt + 1}): {e}")
                time.sleep(0.1)
    
    # Force garbage collection
    print("🗑️ Running garbage collection...")
    gc.collect()
    time.sleep(1)
    
    # On Windows, try to reset camera drivers
    if platform.system().lower() == "windows":
        print("🔄 Resetting Windows camera drivers...")
        try:
            result = subprocess.run([
                'powershell', '-Command',
                '''
                Get-PnpDevice -Class Camera | ForEach-Object {
                    Write-Host "Resetting $($_.FriendlyName)..."
                    Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false
                    Start-Sleep -Seconds 1
                    Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false
                }
                '''
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Windows camera drivers reset successfully")
            else:
                print(f"⚠️ Could not reset Windows camera drivers: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error resetting Windows camera drivers: {e}")
    
    print("✅ Camera cleanup completed")

if __name__ == "__main__":
    cleanup_all_cameras()
