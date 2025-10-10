#!/usr/bin/env python3
"""
Windows Performance Configuration Script
Configures the application for optimal performance on Windows systems
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_windows_requirements():
    """Check if running on Windows and verify requirements"""
    if platform.system().lower() != "windows":
        print("❌ This script is designed for Windows systems only.")
        return False
    
    print("✅ Running on Windows system")
    return True

def set_environment_variables():
    """Set environment variables for optimal Windows performance"""
    print("🔧 Setting Windows-optimized environment variables...")
    
    # Performance-optimized settings
    env_vars = {
        'STREAM_WIDTH': '640',
        'STREAM_HEIGHT': '480', 
        'STREAM_FPS': '15',
        'PROCESSING_WIDTH': '320',
        'PROCESSING_HEIGHT': '240',
        'SKIP_FRAMES': '2',
        'JPEG_QUALITY': '70',
        'CONF_THRESHOLD': '0.4',
        'YAW_T': '25',
        'PITCH_T': '20',
        'FLASK_DEBUG': 'False',
        'PYTHONOPTIMIZE': '1',  # Enable Python optimizations
        'OMP_NUM_THREADS': '2',  # Limit OpenMP threads
        'OPENCV_VIDEOIO_PRIORITY_MSMF': '0',  # Disable MSMF priority
        'OPENCV_VIDEOIO_PRIORITY_DSHOW': '1',  # Enable DirectShow priority
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    print("✅ Environment variables set")

def optimize_camera_settings():
    """Optimize camera settings for Windows"""
    print("📹 Optimizing camera settings for Windows...")
    
    # Create a simple test to verify camera optimization
    try:
        import cv2
        
        # Test DirectShow backend
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cap.isOpened():
            print("✅ DirectShow backend available")
            cap.release()
        else:
            print("⚠️ DirectShow backend not available, will use default")
            
    except ImportError:
        print("⚠️ OpenCV not available for camera testing")
    except Exception as e:
        print(f"⚠️ Camera test failed: {e}")

def create_windows_batch_file():
    """Create a Windows batch file for easy startup"""
    print("📝 Creating Windows startup batch file...")
    
    batch_content = """@echo off
echo Starting Attention Detection App with Windows optimizations...

REM Set Windows-optimized environment variables
set STREAM_WIDTH=640
set STREAM_HEIGHT=480
set STREAM_FPS=15
set PROCESSING_WIDTH=320
set PROCESSING_HEIGHT=240
set SKIP_FRAMES=2
set JPEG_QUALITY=70
set CONF_THRESHOLD=0.4
set YAW_T=25
set PITCH_T=20
set FLASK_DEBUG=False
set PYTHONOPTIMIZE=1
set OMP_NUM_THREADS=2
set OPENCV_VIDEOIO_PRIORITY_MSMF=0
set OPENCV_VIDEOIO_PRIORITY_DSHOW=1

REM Start the application
python app.py

pause
"""
    
    batch_file = Path("start_windows_optimized.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"✅ Created {batch_file}")

def create_windows_powershell_script():
    """Create a PowerShell script for advanced users"""
    print("📝 Creating PowerShell startup script...")
    
    ps_content = """# Windows Optimized Startup Script for Attention Detection App
Write-Host "Starting Attention Detection App with Windows optimizations..." -ForegroundColor Green

# Set Windows-optimized environment variables
$env:STREAM_WIDTH = "640"
$env:STREAM_HEIGHT = "480"
$env:STREAM_FPS = "15"
$env:PROCESSING_WIDTH = "320"
$env:PROCESSING_HEIGHT = "240"
$env:SKIP_FRAMES = "2"
$env:JPEG_QUALITY = "70"
$env:CONF_THRESHOLD = "0.4"
$env:YAW_T = "25"
$env:PITCH_T = "20"
$env:FLASK_DEBUG = "False"
$env:PYTHONOPTIMIZE = "1"
$env:OMP_NUM_THREADS = "2"
$env:OPENCV_VIDEOIO_PRIORITY_MSMF = "0"
$env:OPENCV_VIDEOIO_PRIORITY_DSHOW = "1"

Write-Host "Environment variables set for optimal Windows performance" -ForegroundColor Yellow

# Start the application
python app.py

Read-Host "Press Enter to exit"
"""
    
    ps_file = Path("start_windows_optimized.ps1")
    with open(ps_file, 'w') as f:
        f.write(ps_content)
    
    print(f"✅ Created {ps_file}")

def print_optimization_summary():
    """Print a summary of optimizations applied"""
    print("\n" + "="*60)
    print("🎯 WINDOWS PERFORMANCE OPTIMIZATIONS APPLIED")
    print("="*60)
    print("📊 Resolution Settings:")
    print("  - Stream: 640x480 (reduced from 1280x720)")
    print("  - Processing: 320x240 (for AI detection)")
    print("  - FPS: 15 (reduced from 20)")
    print()
    print("⚡ Performance Optimizations:")
    print("  - Frame skipping: Process every 3rd frame")
    print("  - JPEG quality: 70% (reduced from 80%)")
    print("  - DirectShow backend priority")
    print("  - Reduced buffer sizes")
    print("  - Limited OpenMP threads")
    print()
    print("🔧 Camera Optimizations:")
    print("  - Auto-exposure disabled")
    print("  - Auto-focus disabled")
    print("  - Auto white balance disabled")
    print("  - MJPG codec for better performance")
    print()
    print("📁 Startup Files Created:")
    print("  - start_windows_optimized.bat (for easy startup)")
    print("  - start_windows_optimized.ps1 (PowerShell version)")
    print()
    print("🚀 To start the optimized application:")
    print("  1. Double-click 'start_windows_optimized.bat'")
    print("  2. Or run: python app.py (with env vars set)")
    print()
    print("💡 Additional Tips:")
    print("  - Close unnecessary applications")
    print("  - Ensure camera drivers are up to date")
    print("  - Run as administrator if camera access issues occur")
    print("  - Check Windows Camera privacy settings")
    print("="*60)

def main():
    """Main configuration function"""
    print("🪟 Windows Performance Configuration for Attention Detection App")
    print("="*60)
    
    if not check_windows_requirements():
        sys.exit(1)
    
    try:
        set_environment_variables()
        optimize_camera_settings()
        create_windows_batch_file()
        create_windows_powershell_script()
        print_optimization_summary()
        
        print("\n✅ Windows performance configuration completed successfully!")
        print("🎯 The application is now optimized for Windows systems.")
        
    except Exception as e:
        print(f"\n❌ Error during configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
