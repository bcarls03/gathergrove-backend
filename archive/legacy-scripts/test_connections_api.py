#!/usr/bin/env python3
"""
Quick test script for Connections API
Tests the basic CRUD operations for household connections.
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
# For testing, you'll need a valid Firebase auth token
# Get it from browser dev tools after logging in
AUTH_TOKEN = "YOUR_TOKEN_HERE"  # Replace with actual token

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_list_connections():
    """Test GET /api/connections"""
    print("\n1. Testing GET /api/connections...")
    response = requests.get(f"{API_BASE}/api/connections", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Connections: {len(data)}")
        for conn in data:
            print(f"   - {conn['householdId']} ({conn['status']})")
    else:
        print(f"   Error: {response.text}")
    return response

def test_send_connection_request(household_id):
    """Test POST /api/connections"""
    print(f"\n2. Testing POST /api/connections (to {household_id})...")
    body = {"household_id": household_id}
    response = requests.post(
        f"{API_BASE}/api/connections",
        headers=headers,
        json=body
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Connection ID: {data.get('id')}")
        print(f"   Status: {data.get('status')}")
        return data.get('id')
    else:
        print(f"   Error: {response.text}")
    return None

def test_accept_connection(connection_id):
    """Test PATCH /api/connections/:id"""
    print(f"\n3. Testing PATCH /api/connections/{connection_id}...")
    body = {"status": "accepted"}
    response = requests.patch(
        f"{API_BASE}/api/connections/{connection_id}",
        headers=headers,
        json=body
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   New Status: {data.get('status')}")
    else:
        print(f"   Error: {response.text}")
    return response

def test_list_accepted_connections():
    """Test GET /api/connections?status=accepted"""
    print("\n4. Testing GET /api/connections?status=accepted...")
    response = requests.get(
        f"{API_BASE}/api/connections?status=accepted",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Accepted Connections: {len(data)}")
        for conn in data:
            print(f"   - {conn['householdId']}")
    else:
        print(f"   Error: {response.text}")
    return response

def test_remove_connection(connection_id):
    """Test DELETE /api/connections/:id"""
    print(f"\n5. Testing DELETE /api/connections/{connection_id}...")
    response = requests.delete(
        f"{API_BASE}/api/connections/{connection_id}",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Message: {data.get('message')}")
    else:
        print(f"   Error: {response.text}")
    return response

def main():
    print("=" * 60)
    print("Testing Connections API")
    print("=" * 60)
    
    # Check if auth token is configured
    if AUTH_TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️  Error: Please set AUTH_TOKEN in the script")
        print("   1. Open browser and login to GatherGrove")
        print("   2. Open DevTools → Network tab")
        print("   3. Make any API request")
        print("   4. Copy the Authorization header token")
        print("   5. Set it in this script")
        return
    
    # Run tests
    test_list_connections()
    
    # Note: You'll need to replace 'household_xxx' with an actual household ID
    # from your database to test connection creation
    print("\n" + "=" * 60)
    print("To test connection creation:")
    print("1. Get a household ID from /api/households")
    print("2. Call test_send_connection_request('household_id')")
    print("3. Call test_accept_connection('connection_id')")
    print("4. Call test_remove_connection('connection_id')")
    print("=" * 60)

if __name__ == "__main__":
    main()
