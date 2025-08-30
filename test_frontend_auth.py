#!/usr/bin/env python3
"""
Test script to verify the frontend can receive proper 401 errors.
"""

import requests
import json

def test_frontend_proxy():
    """Test the sports preferences endpoint through the frontend proxy."""
    # Test through frontend proxy (port 3000)
    frontend_url = "http://localhost:3000/api/questionnaire/sports/preferences"
    
    # Test with invalid token
    headers = {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }
    
    payload = [
        {"sport_id": 1, "interest_level": 3}
    ]
    
    print("Testing sports preferences endpoint through frontend proxy...")
    print(f"URL: {frontend_url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(frontend_url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: Frontend proxy correctly returns 401 Unauthorized")
        elif response.status_code == 422:
            print("❌ ISSUE: Frontend proxy still returning 422 instead of 401")
        else:
            print(f"❓ UNEXPECTED: Got status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_direct_backend():
    """Test the sports preferences endpoint directly on backend."""
    # Test direct backend (port 8000)
    backend_url = "http://localhost:8000/api/questionnaire/sports/preferences"
    
    # Test with invalid token
    headers = {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }
    
    payload = [
        {"sport_id": 1, "interest_level": 3}
    ]
    
    print("\nTesting sports preferences endpoint directly on backend...")
    print(f"URL: {backend_url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(backend_url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: Backend correctly returns 401 Unauthorized")
        elif response.status_code == 422:
            print("❌ ISSUE: Backend still returning 422 instead of 401")
        else:
            print(f"❓ UNEXPECTED: Got status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_direct_backend()
    test_frontend_proxy()