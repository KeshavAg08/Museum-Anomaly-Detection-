#!/usr/bin/env python3
"""
Quick ESP32 connectivity test
Save as esp32_quick_test.py and run to diagnose connection issues
"""

import requests
import json
import socket
from urllib.parse import urlparse

ESP32_IP = "10.174.95.69"
ESP32_PORT = 80

def test_network_connectivity():
    """Test basic network connectivity to ESP32"""
    print(f"🔍 Testing network connectivity to {ESP32_IP}...")
    
    try:
        # Test if we can reach the IP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ESP32_IP, ESP32_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connection to {ESP32_IP}:{ESP32_PORT} successful")
            return True
        else:
            print(f"❌ Cannot connect to {ESP32_IP}:{ESP32_PORT} (Error: {result})")
            return False
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def test_http_get(endpoint="/"):
    """Test HTTP GET request to ESP32"""
    url = f"http://{ESP32_IP}:{ESP32_PORT}{endpoint}"
    print(f"\n🔍 Testing HTTP GET: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"📊 Content Length: {len(response.content)} bytes")
        print(f"📄 Content Type: {response.headers.get('content-type', 'unknown')}")
        
        # Try to show some content
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"📋 JSON Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return True, data
            except:
                print("❌ Invalid JSON response")
                return False, response.text[:200]
        else:
            content_preview = response.text[:200].replace('\n', '\\n').replace('\r', '\\r')
            print(f"📝 Content Preview: {content_preview}...")
            return True, response.text
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (ESP32 may be slow or overloaded)")
        return False, None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error (ESP32 may be offline or unreachable)")
        return False, None
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
        return False, None

def main():
    print("ESP32 Quick Connectivity Test")
    print("=" * 40)
    print(f"Target: {ESP32_IP}:{ESP32_PORT}")
    print()
    
    # Step 1: Test network connectivity
    network_ok = test_network_connectivity()
    
    if not network_ok:
        print("\n❌ NETWORK CONNECTIVITY FAILED")
        print("\nTroubleshooting Steps:")
        print("1. Check if ESP32 is powered on")
        print("2. Verify ESP32 WiFi connection")
        print("3. Check if you're on the same network")
        print("4. Try pinging the ESP32: ping 10.174.95.69")
        print("5. Check firewall settings")
        return
    
    # Step 2: Test HTTP endpoints
    endpoints_to_test = [
        "/",
        "/api/sensors",
        "/json",
        "/sensors",
        "/data",
        "/config"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        success, data = test_http_get(endpoint)
        if success:
            working_endpoints.append((endpoint, data))
    
    print(f"\n📊 RESULTS SUMMARY:")
    print("=" * 30)
    print(f"Network connectivity: {'✅ OK' if network_ok else '❌ FAILED'}")
    print(f"Working endpoints: {len(working_endpoints)}")
    
    if working_endpoints:
        print("\n✅ WORKING ENDPOINTS:")
        for endpoint, data in working_endpoints:
            data_type = "JSON" if isinstance(data, dict) else "Text"
            print(f"   {endpoint} ({data_type})")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if len(working_endpoints) == 0:
        print("❌ No endpoints working - ESP32 may have issues")
        print("   - Check ESP32 serial monitor for errors")
        print("   - Verify ESP32 sketch is running correctly")
        print("   - Try restarting the ESP32")
    elif any(endpoint in [ep[0] for ep, _ in working_endpoints] for endpoint in ['/api/sensors', '/json']):
        print("✅ Good! ESP32 has sensor endpoints")
        print("   - Your integration should work")
        print("   - Use /api/sensors for the backend")
    else:
        print("⚠️  ESP32 responding but no sensor endpoints found")
        print("   - Check if correct sketch is uploaded")
        print("   - Verify sensor endpoints in ESP32 code")

if __name__ == "__main__":
    main()