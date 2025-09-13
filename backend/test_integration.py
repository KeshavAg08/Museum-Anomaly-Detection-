#!/usr/bin/env python3
"""
Test script to verify ESP32 and USB camera integration
Run this before starting your main application
"""

import asyncio
import httpx
import cv2
import os
from datetime import datetime

# Load configuration (same as your .env)
ESP32_IP = os.getenv("ESP32_IP", "10.174.95.69")
ESP32_PORT = int(os.getenv("ESP32_PORT", "80"))
USB_CAMERA_INDEX = int(os.getenv("USB_CAMERA_INDEX", "0"))

async def test_esp32_connection():
    """Test ESP32 sensor connection"""
    print("🔍 Testing ESP32 Connection...")
    print(f"ESP32 IP: {ESP32_IP}:{ESP32_PORT}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test /api/sensors endpoint
            response = await client.get(f"http://{ESP32_IP}:{ESP32_PORT}/api/sensors")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ESP32 /api/sensors endpoint working!")
                print(f"   Temperature: {data.get('temperature', 'N/A')}°C")
                print(f"   Humidity: {data.get('humidity', 'N/A')}%")
                print(f"   Vibration: {data.get('vibration_value', 'N/A')}")
                print(f"   WiFi RSSI: {data.get('wifi_rssi', 'N/A')} dBm")
                return True
            else:
                print(f"❌ ESP32 responded with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error connecting to ESP32: {e}")
        return False

async def test_esp32_full_data():
    """Test ESP32 comprehensive data endpoint"""
    print("\n🔍 Testing ESP32 Full Data Endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://{ESP32_IP}:{ESP32_PORT}/json")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ESP32 /json endpoint working!")
                
                if "device_info" in data:
                    device_info = data["device_info"]
                    print(f"   Device: {device_info.get('name', 'Unknown')}")
                    print(f"   Version: {device_info.get('version', 'Unknown')}")
                    print(f"   Uptime: {device_info.get('uptime_formatted', 'Unknown')}")
                
                if "current_readings" in data:
                    readings = data["current_readings"]
                    print(f"   Current Temp: {readings.get('temperature_celsius', 'N/A')}°C")
                    print(f"   Current Humidity: {readings.get('humidity_percent', 'N/A')}%")
                    print(f"   Current Vibration: {readings.get('vibration_value', 'N/A')}")
                
                if "sensor_history" in data:
                    history = data["sensor_history"]
                    print(f"   History entries: {len(history)} readings")
                
                return True
            else:
                print(f"❌ ESP32 /json responded with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error getting ESP32 full data: {e}")
        return False

def test_usb_camera():
    """Test USB camera connection"""
    print("\n🔍 Testing USB Camera...")
    print(f"Camera Index: {USB_CAMERA_INDEX}")
    
    try:
        cap = cv2.VideoCapture(USB_CAMERA_INDEX)
        
        if not cap.isOpened():
            print(f"❌ Failed to open USB camera at index {USB_CAMERA_INDEX}")
            return False
        
        # Try to capture a frame
        ret, frame = cap.read()
        if ret:
            height, width, channels = frame.shape
            print(f"✅ USB camera working!")
            print(f"   Resolution: {width}x{height}")
            print(f"   Channels: {channels}")
            
            # Test encoding to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            print(f"   JPEG encoding: {len(buffer)} bytes")
            
            cap.release()
            return True
        else:
            print("❌ Failed to capture frame from USB camera")
            cap.release()
            return False
            
    except Exception as e:
        print(f"❌ Error testing USB camera: {e}")
        return False

def test_camera_alternatives():
    """Test alternative camera indices if default fails"""
    print("\n🔍 Testing alternative camera indices...")
    
    for i in range(5):  # Test indices 0-4
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Found working camera at index {i}")
                    cap.release()
                else:
                    cap.release()
            else:
                print(f"❌ No camera at index {i}")
        except:
            print(f"❌ Error testing camera index {i}")

async def test_backend_health():
    """Test if backend is running"""
    print("\n🔍 Testing Backend Health (if running)...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Backend is running!")
                print(f"   Status: {data.get('status')}")
                print(f"   Mock mode: {data.get('mock_mode')}")
                print(f"   ESP32 connected: {data.get('esp32_connected')}")
                print(f"   Camera status: {data.get('camera_status')}")
                return True
            else:
                print(f"❌ Backend responded with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"ℹ️  Backend not running or not accessible: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("Museum Anomaly Detection - Integration Test")
    print("=" * 50)
    
    results = []
    
    # Test ESP32 connection
    esp32_basic = await test_esp32_connection()
    results.append(("ESP32 Basic", esp32_basic))
    
    # Test ESP32 full data
    esp32_full = await test_esp32_full_data()
    results.append(("ESP32 Full Data", esp32_full))
    
    # Test USB camera
    camera = test_usb_camera()
    results.append(("USB Camera", camera))
    
    # If camera fails, test alternatives
    if not camera:
        test_camera_alternatives()
    
    # Test backend if running
    backend = await test_backend_health()
    results.append(("Backend Health", backend))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if not esp32_basic:
        print("❌ ESP32 Connection Failed:")
        print("   1. Check ESP32 is powered on and connected to WiFi")
        print("   2. Verify ESP32 IP address in .env file")
        print("   3. Try accessing http://10.174.95.69/ in your browser")
        print("   4. Check your network connection")
    
    if not camera:
        print("❌ USB Camera Failed:")
        print("   1. Check USB camera is connected")
        print("   2. Try different USB ports")
        print("   3. Update USB_CAMERA_INDEX in .env if needed")
        print("   4. Install camera drivers if required")
    
    if esp32_basic and camera:
        print("✅ All hardware tests passed!")
        print("   You can now start your backend with: python main.py")
        print("   Or use: uvicorn main:app --reload")
    
    total_passed = sum(1 for _, result in results if result)
    print(f"\n📈 Overall: {total_passed}/{len(results)} tests passed")

if __name__ == "__main__":
    asyncio.run(main())