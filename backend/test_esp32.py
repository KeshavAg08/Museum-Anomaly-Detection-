#!/usr/bin/env python3
"""
Quick ESP32 test - save this as test_esp32.py in your backend folder
"""

import requests
import json

ESP32_IP = "10.174.95.69"

def test_esp32():
    print(f"Testing ESP32 at {ESP32_IP}...")
    
    # Test main page
    try:
        response = requests.get(f"http://{ESP32_IP}/", timeout=5)
        print(f"✅ Main page: {response.status_code}")
    except Exception as e:
        print(f"❌ Main page failed: {e}")
        return False
    
    # Test sensor endpoints
    endpoints = ["/sensors", "/data", "/sensor"]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://{ESP32_IP}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: Working")
                try:
                    data = response.json()
                    print(f"   Data: {json.dumps(data, indent=2)}")
                    return True
                except:
                    print(f"   Raw: {response.text[:100]}...")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    return False

if __name__ == "__main__":
    test_esp32()