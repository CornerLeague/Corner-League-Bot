#!/usr/bin/env python3
"""
Test script to verify the authentication fix.
"""

import requests
import json

def test_auth_endpoint():
    """Test the sports preferences endpoint with invalid token."""
    url = "http://localhost:8000/api/questionnaire/sports/preferences"
    
    # Test with invalid token
    headers = {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }
    
    payload = [
        {"sport_id": 1, "interest_level": 3}
    ]
    
    print("Testing sports preferences endpoint with invalid token...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: Got expected 401 Unauthorized")
        elif response.status_code == 422:
            print("❌ ISSUE: Still getting 422 instead of 401")
        else:
            print(f"❓ UNEXPECTED: Got status code {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_auth_endpoint()