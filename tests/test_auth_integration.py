#!/usr/bin/env python3
"""
Integrated authentication test suite.
Consolidates authentication testing for both direct backend and frontend proxy endpoints.
"""

import json

import requests


def test_auth_endpoint_direct():
    """Test the sports preferences endpoint with invalid token (direct backend)."""
    url = "http://localhost:8000/api/questionnaire/sports/preferences"

    # Test with invalid token
    headers = {
        "Authorization": "Bearer invalid-token",
        "Content-Type": "application/json"
    }

    payload = [
        {"sport_id": 1, "interest_level": 3}
    ]

    print("Testing sports preferences endpoint with invalid token (direct backend)...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        print()

        # Should return 401 Unauthorized
        if response.status_code == 401:
            print("✅ Direct backend auth test PASSED - Got expected 401")
            return True
        else:
            print(f"❌ Direct backend auth test FAILED - Expected 401, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Direct backend auth test FAILED - Request error: {e}")
        return False


def test_auth_endpoint_frontend_proxy():
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
        response = requests.post(frontend_url, headers=headers, json=payload, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        print()

        # Should return 401 Unauthorized
        if response.status_code == 401:
            print("✅ Frontend proxy auth test PASSED - Got expected 401")
            return True
        else:
            print(f"❌ Frontend proxy auth test FAILED - Expected 401, got {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend proxy auth test FAILED - Request error: {e}")
        return False


def run_all_auth_tests():
    """Run all authentication tests."""
    print("Running Integrated Authentication Tests")
    print("=" * 50)
    print()

    results = []
    results.append(test_auth_endpoint_direct())
    results.append(test_auth_endpoint_frontend_proxy())

    print("\nTest Summary:")
    print("=" * 20)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All authentication tests PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} authentication test(s) FAILED")
        return False


if __name__ == "__main__":
    success = run_all_auth_tests()
    exit(0 if success else 1)
