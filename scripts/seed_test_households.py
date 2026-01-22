#!/usr/bin/env python3
"""
Seed dummy households for Discovery page testing.

Creates realistic test households with:
- Different household types (families, couples, singles)
- Various kid ages and configurations
- Different neighborhoods
- Mix of nearby and connected households

Usage:
    python scripts/seed_test_households.py
    
    # Or to clear and reseed:
    python scripts/seed_test_households.py --reset
"""

import sys
import os
from datetime import datetime, timezone, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

def generate_birth_date(age_years):
    """Generate a birth date for a kid of given age"""
    now = datetime.now(timezone.utc)
    # Approximate: 365 days per year
    birth_date = now - timedelta(days=age_years * 365)
    return {
        "birthMonth": birth_date.month,
        "birthYear": birth_date.year
    }

def seed_test_households():
    """Create diverse test households in Firestore"""
    
    print("🌱 Seeding test households for Discovery...")
    
    # List of realistic household data
    households = [
        # ============= FAMILIES WITH KIDS =============
        {
            "id": "household-miller-001",
            "uid": "user-miller-001",
            "email": "sarah.miller@example.com",
            "lastName": "Miller",
            "adultNames": ["Sarah", "Mike"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(7), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(4), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "456 Oak Lane",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5155,
            "longitude": -122.6789,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-johnson-002",
            "uid": "user-johnson-002",
            "email": "emily.johnson@example.com",
            "lastName": "Johnson",
            "adultNames": ["Emily", "David"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(5), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(3), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(1), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "789 Maple Drive",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5165,
            "longitude": -122.6799,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-garcia-003",
            "uid": "user-garcia-003",
            "email": "maria.garcia@example.com",
            "lastName": "Garcia",
            "adultNames": ["Maria", "Carlos"],
            "neighborhood": "Riverside",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(10), "sex": "boy", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(8), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(6), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "123 River Street",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.5145,
            "longitude": -122.6810,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-chen-004",
            "uid": "user-chen-004",
            "email": "lisa.chen@example.com",
            "lastName": "Chen",
            "adultNames": ["Lisa", "James"],
            "neighborhood": "Riverside",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(12), "sex": "girl", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(9), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "567 Riverfront Ave",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.5135,
            "longitude": -122.6820,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-patel-005",
            "uid": "user-patel-005",
            "email": "priya.patel@example.com",
            "lastName": "Patel",
            "adultNames": ["Priya", "Raj"],
            "neighborhood": "Hillside",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(6), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(4), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "890 Hill Court",
                "city": "Portland",
                "state": "OR",
                "zip": "97203"
            },
            "latitude": 45.5175,
            "longitude": -122.6750,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-wilson-006",
            "uid": "user-wilson-006",
            "email": "amanda.wilson@example.com",
            "lastName": "Wilson",
            "adultNames": ["Amanda"],
            "neighborhood": "Oak Ridge",
            "householdType": "single_parent",
            "kids": [
                {**generate_birth_date(8), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(5), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "234 Oak Circle",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5160,
            "longitude": -122.6780,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        # ============= FAMILIES WITH OLDER KIDS =============
        {
            "id": "household-anderson-007",
            "uid": "user-anderson-007",
            "email": "jennifer.anderson@example.com",
            "lastName": "Anderson",
            "adultNames": ["Jennifer", "Robert"],
            "neighborhood": "Hillside",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(16), "sex": "boy", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(14), "sex": "girl", "awayAtCollege": False, "canBabysit": True},
            ],
            "address": {
                "street": "345 Summit Drive",
                "city": "Portland",
                "state": "OR",
                "zip": "97203"
            },
            "latitude": 45.5180,
            "longitude": -122.6760,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        # ============= COUPLES WITHOUT KIDS =============
        {
            "id": "household-taylor-008",
            "uid": "user-taylor-008",
            "email": "jessica.taylor@example.com",
            "lastName": "Taylor",
            "adultNames": ["Jessica", "Brian"],
            "neighborhood": "Riverside",
            "householdType": "couple",
            "kids": [],
            "address": {
                "street": "678 Waterfront Blvd",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.5140,
            "longitude": -122.6815,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-martinez-009",
            "uid": "user-martinez-009",
            "email": "sofia.martinez@example.com",
            "lastName": "Martinez",
            "adultNames": ["Sofia", "Diego"],
            "neighborhood": "Oak Ridge",
            "householdType": "couple",
            "kids": [],
            "address": {
                "street": "901 Oak Boulevard",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5170,
            "longitude": -122.6770,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        # ============= SINGLES =============
        {
            "id": "household-brown-010",
            "uid": "user-brown-010",
            "email": "michael.brown@example.com",
            "lastName": "Brown",
            "adultNames": ["Michael"],
            "neighborhood": "Hillside",
            "householdType": "single",
            "kids": [],
            "address": {
                "street": "456 Peak Lane",
                "city": "Portland",
                "state": "OR",
                "zip": "97203"
            },
            "latitude": 45.5185,
            "longitude": -122.6755,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        {
            "id": "household-lee-011",
            "uid": "user-lee-011",
            "email": "daniel.lee@example.com",
            "lastName": "Lee",
            "adultNames": ["Daniel"],
            "neighborhood": "Riverside",
            "householdType": "single",
            "kids": [],
            "address": {
                "street": "789 River Plaza",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.5150,
            "longitude": -122.6805,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
        
        # ============= FAMILIES WITH MIXED AGES =============
        {
            "id": "household-robinson-012",
            "uid": "user-robinson-012",
            "email": "ashley.robinson@example.com",
            "lastName": "Robinson",
            "adultNames": ["Ashley", "Chris"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(15), "sex": "girl", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(11), "sex": "boy", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(6), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "123 Oak Terrace",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5158,
            "longitude": -122.6785,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        },
    ]
    
    # Write to Firestore
    households_ref = db.collection("households")
    
    for household in households:
        household_id = household["id"]
        print(f"  ✓ Creating {household['lastName']} household ({household['householdType']}) in {household['neighborhood']}")
        
        # Use uid as document ID (matches backend pattern)
        doc_ref = households_ref.document(household["uid"])
        doc_ref.set(household)
    
    print(f"\n✅ Successfully created {len(households)} test households!")
    print("\n📊 Summary:")
    print(f"  • Families with kids: {sum(1 for h in households if h['householdType'] == 'family_with_kids')}")
    print(f"  • Single parents: {sum(1 for h in households if h['householdType'] == 'single_parent')}")
    print(f"  • Couples: {sum(1 for h in households if h['householdType'] == 'couple')}")
    print(f"  • Singles: {sum(1 for h in households if h['householdType'] == 'single')}")
    print(f"\n🏘️  Neighborhoods:")
    neighborhoods = {}
    for h in households:
        n = h['neighborhood']
        neighborhoods[n] = neighborhoods.get(n, 0) + 1
    for n, count in neighborhoods.items():
        print(f"  • {n}: {count} households")
    
    return households

def seed_connections(households):
    """Create some test connections between households"""
    print("\n🔗 Seeding test connections...")
    
    # Get current user's UID from localStorage simulation
    # For testing, we'll create connections for a specific test user
    current_uid = "dev-test-user-001"  # This should match your dev UID
    
    connections_ref = db.collection("connections")
    
    # Create connections (assuming current user connects with some households)
    connections = [
        {
            "uid": current_uid,
            "connected_household_ids": [
                "user-miller-001",
                "user-johnson-002",
                "user-garcia-003",
                "user-wilson-006",
            ]
        }
    ]
    
    for conn in connections:
        print(f"  ✓ Creating connections for {conn['uid']}")
        doc_ref = connections_ref.document(conn["uid"])
        doc_ref.set(conn)
    
    print(f"✅ Created {len(connections)} connection records!")
    print(f"   Connected households: {len(connections[0]['connected_household_ids'])}")

def reset_households():
    """Delete all test households"""
    print("🗑️  Resetting test households...")
    
    households_ref = db.collection("households")
    
    # Delete households that start with 'user-'
    docs = households_ref.stream()
    deleted = 0
    
    for doc in docs:
        if doc.id.startswith("user-") and doc.id.endswith(("001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "012")):
            doc.reference.delete()
            deleted += 1
            print(f"  ✗ Deleted {doc.id}")
    
    print(f"✅ Deleted {deleted} test households")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed test households")
    parser.add_argument("--reset", action="store_true", help="Delete existing test households first")
    args = parser.parse_args()
    
    if args.reset:
        reset_households()
        print()
    
    households = seed_test_households()
    seed_connections(households)
    
    print("\n🎉 Done! Test households are ready.")
    print("\n💡 Next steps:")
    print("  1. Start the backend: cd gathergrove-backend && python -m uvicorn app.main:app --reload")
    print("  2. Start the frontend: cd gathergrove-frontend && npm run dev")
    print("  3. Visit http://localhost:5174/discovery")
    print("  4. Test the Discovery page with nearby and connected households!")
