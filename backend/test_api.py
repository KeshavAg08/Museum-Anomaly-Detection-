#!/usr/bin/env python3
"""
Test script to verify the backend API is working correctly
Run this after starting your backend server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_get_exhibits():
    """Test getting all exhibits"""
    try:
        response = requests.get(f"{BASE_URL}/exhibits")
        print(f"\nGet Exhibits: {response.status_code}")
        data = response.json()
        print(f"Number of exhibits: {len(data.get('exhibits', []))}")
        for exhibit in data.get('exhibits', []):
            print(f"  - {exhibit['name']} (ID: {exhibit['id']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Get exhibits failed: {e}")
        return False

def test_create_exhibit():
    """Test creating a new exhibit"""
    try:
        new_exhibit = {
            "name": "Test Exhibit",
            "description": "This is a test exhibit created by the test script",
            "location": "Test Gallery",
            "temperature_min": 19.0,
            "temperature_max": 23.0,
            "humidity_min": 45.0,
            "humidity_max": 55.0,
            "vibration_max": 0.3
        }
        
        response = requests.post(f"{BASE_URL}/exhibits", json=new_exhibit)
        print(f"\nCreate Exhibit: {response.status_code}")
        if response.status_code == 200:
            created = response.json()
            print(f"Created exhibit ID: {created['id']}")
            print(f"Created exhibit name: {created['name']}")
            return created['id']
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Create exhibit failed: {e}")
        return None

def test_update_exhibit(exhibit_id):
    """Test updating an exhibit"""
    try:
        updates = {
            "description": "Updated description via test script",
            "temperature_max": 25.0
        }
        
        response = requests.put(f"{BASE_URL}/exhibits/{exhibit_id}", json=updates)
        print(f"\nUpdate Exhibit: {response.status_code}")
        if response.status_code == 200:
            updated = response.json()
            print(f"Updated description: {updated['description']}")
            print(f"Updated temp_max: {updated['temperature_max']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Update exhibit failed: {e}")
        return False

def test_delete_exhibit(exhibit_id):
    """Test deleting an exhibit"""
    try:
        response = requests.delete(f"{BASE_URL}/exhibits/{exhibit_id}")
        print(f"\nDelete Exhibit: {response.status_code}")
        if response.status_code == 200:
            print("Exhibit deleted successfully")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Delete exhibit failed: {e}")
        return False

def main():
    print("Testing Museum Anomaly Detection Backend API")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("Backend is not running or not accessible!")
        return
    
    # Test get exhibits
    test_get_exhibits()
    
    # Test create exhibit
    new_exhibit_id = test_create_exhibit()
    if not new_exhibit_id:
        print("Failed to create exhibit!")
        return
    
    # Test get exhibits again to see the new one
    print("\nAfter creating exhibit:")
    test_get_exhibits()
    
    # Test update exhibit
    test_update_exhibit(new_exhibit_id)
    
    # Test get specific exhibit
    try:
        response = requests.get(f"{BASE_URL}/exhibits/{new_exhibit_id}")
        print(f"\nGet Specific Exhibit: {response.status_code}")
        if response.status_code == 200:
            exhibit = response.json()
            print(f"Exhibit: {exhibit['name']}")
            print(f"Description: {exhibit['description']}")
    except Exception as e:
        print(f"Get specific exhibit failed: {e}")
    
    # Test delete exhibit
    test_delete_exhibit(new_exhibit_id)
    
    # Final check
    print("\nFinal state:")
    test_get_exhibits()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()