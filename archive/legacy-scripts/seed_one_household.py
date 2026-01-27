#!/usr/bin/env python3
"""Simple script to seed one test household"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

print("=" * 60)
print("SEEDING TEST HOUSEHOLD")
print("=" * 60)

# Create one simple household
household_data = {
    "id": "household-test-001",
    "uid": "user-test-001",
    "email": "test@example.com",
    "lastName": "TestFamily",
    "adultNames": ["John", "Jane"],
    "neighborhood": "Test Neighborhood",
    "householdType": "family_with_kids",
    "kids": [
        {"birthMonth": 1, "birthYear": 2018, "sex": "boy", "awayAtCollege": False, "canBabysit": False},
        {"birthMonth": 6, "birthYear": 2020, "sex": "girl", "awayAtCollege": False, "canBabysit": False},
    ],
    "address": {
        "street": "123 Test Street",
        "city": "Portland",
        "state": "OR",
        "zip": "97201"
    },
    "latitude": 45.5152,
    "longitude": -122.6784,
    "location_precision": "street",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "updatedAt": datetime.now(timezone.utc).isoformat()
}

# Write to Firestore
doc_id = household_data["uid"]
print(f"\nWriting household to Firestore with ID: {doc_id}")
print(f"Data: {household_data}")

db.collection("households").document(doc_id).set(household_data)

print("\n✅ SUCCESS! Test household created.")
print(f"   Doc ID: {doc_id}")
print(f"   Name: {household_data['lastName']}")

# Verify it was written
print("\n" + "=" * 60)
print("VERIFICATION - Reading back from Firestore")
print("=" * 60)

all_docs = list(db.collection("households").stream())
print(f"\nTotal households in database: {len(all_docs)}")

for doc in all_docs:
    data = doc.to_dict()
    print(f"  - ID: {doc.id}")
    print(f"    Last Name: {data.get('lastName', 'N/A')}")
    print(f"    Neighborhood: {data.get('neighborhood', 'N/A')}")
    print()

print("=" * 60)
print("DONE! Now refresh your browser to see the household.")
print("=" * 60)
