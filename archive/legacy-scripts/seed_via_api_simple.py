#!/usr/bin/env python3
"""
Seed test households directly via API (works with in-memory backend)
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def create_household(uid, data):
    """Create a household via API"""
    headers = {
        "X-Uid": uid,
        "X-Email": f"{uid}@example.com",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE}/households",
        headers=headers,
        json=data
    )
    
    return response

# Test households
households = [
    {
        "uid": "user-miller-001",
        "data": {
            "lastName": "Miller",
            "adultNames": ["Sarah", "Mike"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {"birthMonth": 1, "birthYear": 2018, "sex": "girl"},
                {"birthMonth": 6, "birthYear": 2021, "sex": "boy"},
            ],
            "address": {
                "street": "456 Oak Lane",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5155,
            "longitude": -122.6789,
            "location_precision": "street"
        }
    },
    {
        "uid": "user-johnson-002",
        "data": {
            "lastName": "Johnson",
            "adultNames": ["Emily", "David"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {"birthMonth": 3, "birthYear": 2019, "sex": "girl"},
                {"birthMonth": 8, "birthYear": 2022, "sex": "girl"},
                {"birthMonth": 11, "birthYear": 2023, "sex": "boy"},
            ],
            "address": {
                "street": "789 Maple Drive",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5165,
            "longitude": -122.6799,
            "location_precision": "zipcode"
        }
    },
    {
        "uid": "user-garcia-003",
        "data": {
            "lastName": "Garcia",
            "adultNames": ["Maria", "Carlos"],
            "neighborhood": "Riverside",
            "householdType": "family_with_kids",
            "kids": [
                {"birthMonth": 5, "birthYear": 2017, "sex": "boy"},
            ],
            "address": {
                "street": "321 River Road",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.5145,
            "longitude": -122.6750,
            "location_precision": "street"
        }
    }
]

print("=" * 60)
print("SEEDING HOUSEHOLDS VIA API (In-Memory Backend)")
print("=" * 60)
print()

for household in households:
    uid = household["uid"]
    data = household["data"]
    last_name = data["lastName"]
    
    print(f"Creating household: {last_name} (uid: {uid})...")
    
    try:
        response = create_household(uid, data)
        if response.status_code in [200, 201]:
            print(f"  ✅ SUCCESS - {last_name} created!")
        else:
            print(f"  ❌ ERROR - Status {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ EXCEPTION: {e}")
    
    print()

# Verify
print("=" * 60)
print("VERIFICATION - Fetching households from API")
print("=" * 60)
print()

try:
    response = requests.get(
        f"{API_BASE}/households",
        headers={"X-Uid": "dev-test", "X-Email": "dev-test@example.com"}
    )
    
    if response.status_code == 200:
        households_data = response.json()
        print(f"✅ Found {len(households_data)} households:")
        for h in households_data:
            print(f"  - {h.get('lastName', 'Unknown')} ({h.get('neighborhood', 'No neighborhood')})")
    else:
        print(f"❌ Error fetching households: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

print()
print("=" * 60)
print("✅ DONE! Refresh your browser to see the households.")
print("=" * 60)
