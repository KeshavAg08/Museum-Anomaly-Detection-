#!/usr/bin/env python3
"""
Discover what endpoints your ESP32 provides
Save this as discover_esp32.py in your backend folder
"""

import requests
import json
import re

ESP32_IP = "10.174.95.69"

def get_main_page():
    """Get the main page and look for links/endpoints"""
    print(f"🔍 Analyzing ESP32 main page at {ESP32_IP}...")
    
    try:
        response = requests.get(f"http://{ESP32_IP}/", timeout=10)
        if response.status_code == 200:
            content = response.text
            print("✅ Main page content received")
            print(f"Content length: {len(content)} characters")
            
            # Look for common patterns
            print("\n📄 Main page content (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            # Look for links in the HTML
            links = re.findall(r'href=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if links:
                print(f"\n🔗 Found {len(links)} links:")
                for link in links:
                    print(f"   {link}")
            
            # Look for common endpoint patterns
            endpoints_in_text = re.findall(r'/[a-zA-Z][a-zA-Z0-9_/-]*', content)
            if endpoints_in_text:
                print(f"\n📍 Potential endpoints found in content:")
                unique_endpoints = list(set(endpoints_in_text))
                for endpoint in unique_endpoints:
                    print(f"   {endpoint}")
            
            return content, links, unique_endpoints
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return None, [], []
    except Exception as e:
        print(f"❌ Error getting main page: {e}")
        return None, [], []

def test_common_endpoints():
    """Test common ESP32 endpoints"""
    print(f"\n🔍 Testing common ESP32 endpoints...")
    
    # Common endpoints for ESP32 projects
    endpoints_to_try = [
        "/json",
        "/api",
        "/status",
        "/readings",
        "/temp",
        "/humidity",
        "/sensors.json",
        "/data.json",
        "/api/sensors",
        "/api/data",
        "/get",
        "/values",
        "/sensor_data",
        "/measurements",
        "/environmental",
        "/monitor",
        "/info",
        "/state"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"http://{ESP32_IP}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: Working!")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"   JSON data: {json.dumps(data, indent=2)}")
                    working_endpoints.append((endpoint, data, "json"))
                except:
                    # Show raw content if not JSON
                    content = response.text.strip()
                    print(f"   Raw content: {content[:200]}{'...' if len(content) > 200 else ''}")
                    working_endpoints.append((endpoint, content, "text"))
            elif response.status_code == 404:
                print(f"❌ {endpoint}: 404 Not Found")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    return working_endpoints

def analyze_sensor_data(working_endpoints):
    """Analyze the sensor data format"""
    print(f"\n📊 Analyzing sensor data format...")
    
    for endpoint, data, data_type in working_endpoints:
        print(f"\n🔍 Endpoint: {endpoint}")
        print(f"   Type: {data_type}")
        
        if data_type == "json" and isinstance(data, dict):
            print("   JSON Structure:")
            for key, value in data.items():
                print(f"      {key}: {value} (type: {type(value).__name__})")
                
            # Look for sensor-like data
            sensor_keys = []
            if any(key.lower() in ['temp', 'temperature'] for key in data.keys()):
                sensor_keys.append("temperature")
            if any(key.lower() in ['hum', 'humidity'] for key in data.keys()):
                sensor_keys.append("humidity")
            if any(key.lower() in ['vib', 'vibration', 'shake', 'motion'] for key in data.keys()):
                sensor_keys.append("vibration")
            
            if sensor_keys:
                print(f"   🎯 Detected sensor data: {', '.join(sensor_keys)}")
        
        elif data_type == "text":
            print(f"   Text content: {str(data)[:100]}...")

def provide_integration_guidance(working_endpoints, main_content):
    """Provide specific integration guidance"""
    print(f"\n" + "="*60)
    print("🎯 INTEGRATION GUIDANCE")
    print("="*60)
    
    if working_endpoints:
        print("✅ Found working endpoints on your ESP32:")
        
        best_endpoint = None
        best_data = None
        
        for endpoint, data, data_type in working_endpoints:
            print(f"\n📍 Endpoint: {endpoint}")
            print(f"   Returns: {data_type}")
            
            if data_type == "json" and isinstance(data, dict):
                # This looks like the best option
                if not best_endpoint or len(data) > len(best_data if isinstance(best_data, dict) else {}):
                    best_endpoint = endpoint
                    best_data = data
                
                print("   ✅ JSON format - Good for integration!")
                print("   Data structure:")
                for key, value in data.items():
                    print(f"      {key}: {value}")
        
        if best_endpoint:
            print(f"\n🏆 RECOMMENDED ENDPOINT: {best_endpoint}")
            print(f"URL: http://{ESP32_IP}{best_endpoint}")
            
            print(f"\n🔧 To integrate with your backend:")
            print("1. Update your ESP32SensorManager in main.py")
            print(f"2. Change the endpoint from '/sensors' to '{best_endpoint}'")
            print("3. Map the JSON keys to temperature, humidity, vibration")
            
            if isinstance(best_data, dict):
                print(f"\n📋 Key mapping suggestions:")
                for key, value in best_data.items():
                    key_lower = key.lower()
                    if 'temp' in key_lower:
                        print(f"   temperature = data['{key}']  # Current value: {value}")
                    elif 'hum' in key_lower:
                        print(f"   humidity = data['{key}']     # Current value: {value}")
                    elif any(x in key_lower for x in ['vib', 'motion', 'shake', 'accel']):
                        print(f"   vibration = data['{key}']    # Current value: {value}")
                    else:
                        print(f"   # {key} = {value} (determine what this represents)")
        
        else:
            print("\n⚠️  No JSON endpoints found. You may need to:")
            print("1. Check your ESP32 code")
            print("2. Add a JSON endpoint that returns sensor data")
            print("3. Or parse the text format returned by your ESP32")
    
    else:
        print("❌ No working sensor endpoints found.")
        print("\n🔧 Possible solutions:")
        print("1. Check your ESP32 code - ensure it has sensor endpoints")
        print("2. Verify your ESP32 is running the correct sketch")
        print("3. Check if there are query parameters needed")
        
    print(f"\n💡 ESP32 Web Interface: http://{ESP32_IP}/")
    print("   Visit this URL in your browser to see what your ESP32 shows")

def main():
    print("ESP32 Endpoint Discovery")
    print("="*50)
    print(f"ESP32 IP: {ESP32_IP}")
    print()
    
    # Get main page
    main_content, links, potential_endpoints = get_main_page()
    
    # Test common endpoints
    working_endpoints = test_common_endpoints()
    
    # Test any endpoints found in the main page
    if potential_endpoints:
        print(f"\n🔍 Testing endpoints found in main page...")
        for endpoint in potential_endpoints[:10]:  # Test first 10
            if endpoint not in [ep[0] for ep in working_endpoints]:
                try:
                    response = requests.get(f"http://{ESP32_IP}{endpoint}", timeout=3)
                    if response.status_code == 200:
                        print(f"✅ {endpoint}: Working!")
                        try:
                            data = response.json()
                            working_endpoints.append((endpoint, data, "json"))
                        except:
                            content = response.text.strip()
                            working_endpoints.append((endpoint, content, "text"))
                except:
                    pass
    
    # Analyze what we found
    if working_endpoints:
        analyze_sensor_data(working_endpoints)
    
    # Provide integration guidance
    provide_integration_guidance(working_endpoints, main_content)

if __name__ == "__main__":
    main()