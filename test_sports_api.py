#!/usr/bin/env python3

import json

import requests

# Test the sports preferences API endpoint
url = "http://localhost:8000/api/questionnaire/sports/preferences"

# Test data - this should match what the frontend is sending
test_data = [
    {
        "sport_id": 1,
        "interest_level": 3
    }
]

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test-token"
}

print("Testing sports preferences API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(test_data, indent=2)}")
print(f"Headers: {headers}")
print()

try:
    response = requests.post(url, json=test_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")

    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            json_response = response.json()
            print(f"Response JSON: {json.dumps(json_response, indent=2)}")
        except json.JSONDecodeError:
            print("Failed to parse JSON response")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
