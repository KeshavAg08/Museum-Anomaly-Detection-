#!/usr/bin/env python3
"""
Enhanced integration test script for ESP32 and USB camera
Run this to diagnose and test your museum monitoring system
"""

import asyncio
import httpx
import cv2
import os
import json
from datetime import datetime

# Configuration (matches your setup)
ESP32_IP = "10.174.95.69"
ESP32_PORT = 80
USB_CAMERA_INDEX = 0

async def test_esp32_endpoints():
    """Test all ESP32 endpoints we discovered"""
    print("🔍 Testing ESP32 Endpoints...")
    print(f"ESP32 URL: http://{ESP32_IP}:{ESP32_PORT}")
    
    # Based on your discovery results, test these endpoints
    endpoints_to_test = [
        "/api/sensors",  # Recommended endpoint
        "/json",         # Comprehensive data
        "/config"        # Configuration endpoint
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n📡 Testing {endpoint}...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"http://{ESP32_IP}:{ESP32_PORT}{endpoint}")
                
                if response.status_code == 200:
                    print(f"✅ {endpoint}: Status {response.status_code}")
                    
                    try:
                        # Try to parse as JSON
                        data = response.json()
                        print(f"   📊 JSON Data Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        # Show relevant sensor data
                        if endpoint == "/api/sensors":
                            print(f"   🌡️  Temperature: {data.get('temperature', 'N/A')}°C")
                            print(f"   💧 Humidity: {data.get('humidity', 'N/A')}%")
                            print(f"   📳 Vibration: {data.get('vibration_value', 'N/A')}")
                            print(f"   📶 WiFi RSSI: {data.get('wifi_rssi', 'N/A')} dBm")
                        
                        elif endpoint == "/json":
                            if "current_readings" in data:
                                current = data["current_readings"]
                                print(f"   🌡️  Temperature: {current.get('temperature_celsius', 'N/A')}°C")
                                print(f"   💧 Humidity: {current.get('humidity_percent', 'N/A')}%")
                                print(f"   📳 Vibration: {current.get('vibration_value', 'N/A')}")
                            
                            if "device_info" in data:
                                device = data["device_info"]
                                print(f"   🔧 Device: {device.get('name', 'Unknown')}")
                                print(f"   ⏱️  Uptime: {device.get('uptime_formatted', 'Unknown')}")
                        
                        working_endpoints.append((endpoint, data, "json"))
                        
                    except json.JSONDecodeError:
                        # Handle text response
                        text_content = response.text[:200]
                        print(f"   📄 Text Response: {text_content}...")
                        working_endpoints.append((endpoint, text_content, "text"))
                        
                else:
                    print(f"❌ {endpoint}: Status {response.status_code}")
                    
        except asyncio.TimeoutError:
            print(f"⏰ {endpoint}: Timeout - ESP32 may be slow or unresponsive")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    return working_endpoints

def test_usb_camera_detailed():
    """Detailed USB camera testing"""
    print("\n🔍 Testing USB Camera (Detailed)...")
    
    # Test multiple camera indices
    camera_found = False
    working_cameras = []
    
    for i in range(6):  # Test indices 0-5
        try:
            print(f"\n📹 Testing camera index {i}...")
            cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                # Try to read a frame
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✅ Camera {i}: Working! Resolution: {width}x{height}")
                    
                    # Test JPEG encoding
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 70]
                    success, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    if success:
                        print(f"   📸 JPEG Encoding: Success ({len(buffer)} bytes)")
                        working_cameras.append(i)
                        camera_found = True
                    else:
                        print(f"   ❌ JPEG Encoding: Failed")
                    
                    # Get camera properties
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
                    print(f"   🎥 FPS: {fps}, Format: {int(fourcc)}")
                    
                else:
                    print(f"❌ Camera {i}: Can't capture frame")
                
                cap.release()
            else:
                print(f"❌ Camera {i}: Can't open")
                
        except Exception as e:
            print(f"❌ Camera {i}: Exception - {e}")
    
    if camera_found:
        print(f"\n✅ Found {len(working_cameras)} working camera(s): {working_cameras}")
        recommended_index = working_cameras[0]
        print(f"💡 Recommended: Use USB_CAMERA_INDEX={recommended_index}")
        return True, recommended_index
    else:
        print("\n❌ No working USB cameras found")
        return False, None

async def test_backend_integration():
    """Test if backend can connect to ESP32"""
    print("\n🔍 Testing Backend Integration...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test backend health
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Backend is running!")
                print(f"   📊 Status: {data.get('status')}")
                print(f"   🔧 Mock mode: {data.get('mock_mode')}")
                print(f"   📡 ESP32 connected: {data.get('esp32_connected')}")
                print(f"   📹 Camera status: {data.get('camera_status')}")
                print(f"   🌐 ESP32 IP: {data.get('esp32_ip')}")
                
                return True
            else:
                print(f"❌ Backend responded with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"ℹ️  Backend not running: {e}")
        print("   💡 Start backend with: python main.py")
        return False

async def test_esp32_specific_endpoints():
    """Test ESP32 backend-specific endpoints"""
    print("\n🔍 Testing ESP32 Backend Endpoints...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test ESP32 status endpoint
            response = await client.get("http://localhost:8000/esp32/status")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ ESP32 Status endpoint working!")
                print(f"   Status: {data.get('status')}")
                
                if 'device_info' in data:
                    device = data['device_info']
                    print(f"   Device: {device.get('name', 'Unknown')}")
                
                return True
            else:
                print(f"❌ ESP32 status endpoint: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ ESP32 backend endpoints: {e}")
        return False

def create_env_recommendations(working_cameras, esp32_working):
    """Create .env file recommendations"""
    print("\n📝 Environment Configuration Recommendations:")
    print("=" * 50)
    
    env_content = []
    
    # Server Configuration
    env_content.append("# Server Configuration")
    env_content.append("FRONTEND_ORIGIN=http://localhost:5173")
    env_content.append("UVICORN_NO_ACCESS_LOG=1")
    env_content.append("")
    
    # Sensor Configuration
    env_content.append("# Sensor Configuration")
    if esp32_working:
        env_content.append("MOCK_SENSORS=false  # Use real ESP32 sensors")
        env_content.append(f"ESP32_IP={ESP32_IP}")
        env_content.append(f"ESP32_PORT={ESP32_PORT}")
        env_content.append("REAL_DATA_EXHIBIT_ID=1  # Exhibit ID that uses real sensors")
    else:
        env_content.append("MOCK_SENSORS=true   # ESP32 not available, use mock data")
        env_content.append(f"# ESP32_IP={ESP32_IP}  # Uncomment when ESP32 is available")
        env_content.append(f"# ESP32_PORT={ESP32_PORT}")
    
    env_content.append("")
    
    # Camera Configuration
    env_content.append("# Camera Configuration")
    if working_cameras:
        recommended_cam = working_cameras[0] if isinstance(working_cameras, list) else working_cameras
        env_content.append(f"USB_CAMERA_INDEX={recommended_cam}")
        env_content.append("CAMERA_QUALITY=70")
        env_content.append("CAMERA_FPS=10")
    else:
        env_content.append("USB_CAMERA_INDEX=0  # Adjust if needed")
        env_content.append("CAMERA_QUALITY=70")
        env_content.append("CAMERA_FPS=10")
    
    env_content.append("")
    
    # Thresholds
    env_content.append("# Anomaly Detection Thresholds")
    env_content.append("TEMP_MIN=18.0")
    env_content.append("TEMP_MAX=24.0")
    env_content.append("HUMIDITY_MIN=40.0")
    env_content.append("HUMIDITY_MAX=60.0")
    env_content.append("VIBRATION_MAX=0.5")
    
    print("\n📄 Recommended .env content:")
    print("-" * 30)
    for line in env_content:
        print(line)
    print("-" * 30)

async def main():
    """Run comprehensive integration test"""
    print("🏛️  Museum Anomaly Detection - Comprehensive Integration Test")
    print("=" * 60)
    print(f"⏰ Test Time: {datetime.now()}")
    print(f"🌐 ESP32 Target: {ESP32_IP}:{ESP32_PORT}")
    print("=" * 60)
    
    test_results = {}
    
    # Test ESP32 endpoints
    working_endpoints = await test_esp32_endpoints()
    esp32_working = len(working_endpoints) > 0
    test_results["ESP32 Connection"] = esp32_working
    
    # Test USB camera
    camera_working, working_cameras = test_usb_camera_detailed()
    test_results["USB Camera"] = camera_working
    
    # Test backend integration
    backend_running = await test_backend_integration()
    test_results["Backend Health"] = backend_running
    
    # Test ESP32 backend endpoints if backend is running
    if backend_running:
        esp32_backend = await test_esp32_specific_endpoints()
        test_results["ESP32 Backend Integration"] = esp32_backend
    
    # Results Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30}: {status}")
    
    # Detailed Analysis
    print("\n🔍 DETAILED ANALYSIS:")
    print("-" * 40)
    
    if esp32_working:
        print("✅ ESP32 Status: CONNECTED")
        print("   Your ESP32 is responding and providing sensor data")
        print("   Recommended endpoint: /api/sensors")
    else:
        print("❌ ESP32 Status: DISCONNECTED")
        print("   Troubleshooting steps:")
        print("   1. Verify ESP32 is powered on")
        print("   2. Check WiFi connection")
        print("   3. Try browsing to http://10.174.95.69/")
        print("   4. Check firewall settings")
    
    if camera_working:
        print(f"✅ Camera Status: WORKING (Index: {working_cameras})")
        print("   USB camera is detected and can capture frames")
    else:
        print("❌ Camera Status: NOT DETECTED")
        print("   Troubleshooting steps:")
        print("   1. Check USB camera is connected")
        print("   2. Try different USB ports")
        print("   3. Install camera drivers if needed")
        print("   4. Test with other camera software")
    
    # Create environment recommendations
    create_env_recommendations(working_cameras, esp32_working)
    
    # Next Steps
    print("\n🚀 NEXT STEPS:")
    print("=" * 30)
    
    if esp32_working and camera_working:
        print("🎉 All hardware is working!")
        print("1. Update your backend/.env file with recommendations above")
        print("2. Start your backend: cd backend && python main.py")
        print("3. Start your frontend: cd frontend && npm run dev")
        print("4. Visit http://localhost:5173 to see your dashboard")
    
    elif esp32_working:
        print("⚠️  ESP32 working, camera needs attention")
        print("1. Fix camera issues first")
        print("2. Update .env file")
        print("3. Backend will work with ESP32 data and placeholder camera")
    
    elif camera_working:
        print("⚠️  Camera working, ESP32 needs attention")
        print("1. Fix ESP32 connection")
        print("2. Backend will work with camera and mock sensor data")
    
    else:
        print("❌ Both ESP32 and camera need attention")
        print("1. Fix hardware connections")
        print("2. Backend will run in full mock mode")
        print("3. You can still test the web interface")
    
    # Final score
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    print(f"\n📈 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🏆 Perfect! All systems are go!")
    elif passed >= total // 2:
        print("👍 Good! Most systems working, minor issues to resolve")
    else:
        print("⚠️  Multiple issues detected, but system is still usable")

if __name__ == "__main__":
    print("Starting comprehensive integration test...")
    print("This may take 30-60 seconds...")
    asyncio.run(main())