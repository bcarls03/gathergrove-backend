#!/usr/bin/env python3
"""
Test Data Migration Script

Creates test fixtures in old household-first format, runs migration,
and verifies the transformation worked correctly.

Usage:
    python3 scripts/test_migration.py
"""

import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, '/Users/briancarlberg/dev/gathergrove-backend')

from app.core.firebase import db


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_test_fixtures():
    """Create test data in old household-first format."""
    print("=" * 80)
    print("Creating test fixtures in OLD format...")
    print("=" * 80)
    
    # OLD FORMAT: Household with uid as doc ID (1:1 coupling)
    test_households = [
        {
            "id": "user_alice_123",
            "uid": "user_alice_123",
            "email": "alice@example.com",
            "adultNames": ["Alice Smith"],
            "lastName": "Smith",
            "householdType": "Family w/ Kids",
            "kids": [
                {"name": "Emma", "ageRange": "6-10", "okToSitFor": True},
                {"name": "Oliver", "ageRange": "0-2", "okToSitFor": False}
            ],
            "address": "123 Maple St",
            "lat": 37.7749,
            "lng": -122.4194,
            "neighborhood": "Bayhill",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        },
        {
            "id": "user_bob_456",
            "uid": "user_bob_456",
            "email": "bob@example.com",
            "adultNames": ["Bob Johnson", "Carol Johnson"],
            "lastName": "Johnson",
            "householdType": "Empty Nesters",
            "kids": [],
            "address": "456 Oak Ave",
            "lat": 37.7750,
            "lng": -122.4195,
            "neighborhood": "Bayhill",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        },
        {
            "id": "user_charlie_789",
            "uid": "user_charlie_789",
            "email": "charlie@example.com",
            "adultNames": ["Charlie Brown"],
            "lastName": "Brown",
            "householdType": "Singles/Couples",
            "kids": [],
            "address": "789 Pine Rd",
            "lat": 37.7751,
            "lng": -122.4196,
            "neighborhood": "Terrace",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        }
    ]
    
    # Create households (old format)
    households_coll = db.collection("households")
    for household in test_households:
        doc_id = household["uid"]
        households_coll.document(doc_id).set(household, merge=False)
        print(f"✅ Created household: households/{doc_id}")
    
    # OLD FORMAT: Events with hostUid (not host_user_id)
    test_events = [
        {
            "type": "future",
            "title": "Neighborhood BBQ",
            "details": "Bring your favorite dish!",
            "hostUid": "user_alice_123",  # OLD FIELD
            "startAt": now_iso(),
            "neighborhoods": ["Bayhill"],
            "category": "food",
            "capacity": 20,
            "status": "active",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        },
        {
            "type": "future",
            "title": "Kids Playdate",
            "details": "Ages 6-10",
            "hostUid": "user_alice_123",  # OLD FIELD
            "startAt": now_iso(),
            "neighborhoods": ["Bayhill"],
            "category": "playdate",
            "capacity": 10,
            "status": "active",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        },
        {
            "type": "now",
            "title": "Walking the dog",
            "details": "Anyone want to join?",
            "hostUid": "user_charlie_789",  # OLD FIELD
            "neighborhoods": ["Terrace"],
            "category": "pet",
            "status": "active",
            "createdAt": now_iso(),
            "updatedAt": now_iso()
        }
    ]
    
    # Create events (old format)
    events_coll = db.collection("events")
    for event in test_events:
        event_id = f"event_{event['title'].replace(' ', '_').lower()}"
        events_coll.document(event_id).set(event, merge=False)
        print(f"✅ Created event: events/{event_id}")
    
    print(f"\n📊 Test fixtures created:")
    print(f"   Households: {len(test_households)}")
    print(f"   Events: {len(test_events)}")


def verify_migration():
    """Verify that migration transformed data correctly."""
    print("\n" + "=" * 80)
    print("Verifying migration results...")
    print("=" * 80)
    
    users_coll = db.collection("users")
    households_coll = db.collection("households")
    events_coll = db.collection("events")
    
    # List all users
    print("\n🧑 USERS:")
    user_docs = list(users_coll.stream()) if hasattr(users_coll, "stream") else []
    if hasattr(users_coll, "_docs"):
        user_docs = [(doc_id, data) for doc_id, data in users_coll._docs.items()]
    
    for doc_id, data in [(d.id, d.to_dict()) for d in user_docs] if isinstance(user_docs[0] if user_docs else None, type(lambda: None)) and hasattr(user_docs[0], 'id') else user_docs:
        print(f"  users/{doc_id}")
        print(f"    Name: {data.get('first_name')} {data.get('last_name')}")
        print(f"    Email: {data.get('email')}")
        print(f"    Household ID: {data.get('household_id')}")
        print(f"    Visibility: {data.get('visibility')}")
    
    # List all households
    print("\n🏠 HOUSEHOLDS:")
    household_docs = list(households_coll.stream()) if hasattr(households_coll, "stream") else []
    if hasattr(households_coll, "_docs"):
        household_docs = [(doc_id, data) for doc_id, data in households_coll._docs.items()]
    
    for doc_id, data in [(d.id, d.to_dict()) for d in household_docs] if isinstance(household_docs[0] if household_docs else None, type(lambda: None)) and hasattr(household_docs[0], 'id') else household_docs:
        print(f"  households/{doc_id}")
        print(f"    Name: {data.get('name')}")
        print(f"    Members: {data.get('member_uids')}")
        print(f"    Type: {data.get('household_type')}")
        print(f"    Kids: {len(data.get('kids', []))}")
    
    # List all events
    print("\n📅 EVENTS:")
    event_docs = list(events_coll.stream()) if hasattr(events_coll, "stream") else []
    if hasattr(events_coll, "_docs"):
        event_docs = [(doc_id, data) for doc_id, data in events_coll._docs.items()]
    
    for doc_id, data in [(d.id, d.to_dict()) for d in event_docs] if isinstance(event_docs[0] if event_docs else None, type(lambda: None)) and hasattr(event_docs[0], 'id') else event_docs:
        print(f"  events/{doc_id}")
        print(f"    Title: {data.get('title')}")
        print(f"    Host (old): {data.get('hostUid', 'N/A')}")
        print(f"    Host (new): {data.get('host_user_id', 'N/A')}")
        print(f"    Visibility: {data.get('visibility', 'N/A')}")
    
    # Validation checks
    print("\n" + "=" * 80)
    print("Validation Checks:")
    print("=" * 80)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: All users have household_id
    checks_total += 1
    users_with_household = sum(1 for _, data in ([(d.id, d.to_dict()) for d in user_docs] if isinstance(user_docs[0] if user_docs else None, type(lambda: None)) else user_docs) if data.get('household_id'))
    if users_with_household == len(user_docs):
        print(f"✅ All {len(user_docs)} users have household_id")
        checks_passed += 1
    else:
        print(f"❌ Only {users_with_household}/{len(user_docs)} users have household_id")
    
    # Check 2: All events have host_user_id
    checks_total += 1
    events_with_host_user_id = sum(1 for _, data in ([(d.id, d.to_dict()) for d in event_docs] if isinstance(event_docs[0] if event_docs else None, type(lambda: None)) else event_docs) if data.get('host_user_id'))
    if events_with_host_user_id == len(event_docs):
        print(f"✅ All {len(event_docs)} events have host_user_id")
        checks_passed += 1
    else:
        print(f"❌ Only {events_with_host_user_id}/{len(event_docs)} events have host_user_id")
    
    # Check 3: All events have visibility
    checks_total += 1
    events_with_visibility = sum(1 for _, data in ([(d.id, d.to_dict()) for d in event_docs] if isinstance(event_docs[0] if event_docs else None, type(lambda: None)) else event_docs) if data.get('visibility'))
    if events_with_visibility == len(event_docs):
        print(f"✅ All {len(event_docs)} events have visibility field")
        checks_passed += 1
    else:
        print(f"❌ Only {events_with_visibility}/{len(event_docs)} events have visibility")
    
    print(f"\n📊 Validation: {checks_passed}/{checks_total} checks passed")
    
    if checks_passed == checks_total:
        print("✅ Migration successful!")
        return True
    else:
        print("❌ Migration has issues")
        return False


def main():
    """Main test flow."""
    print("=" * 80)
    print("GatherGrove Migration Test")
    print("=" * 80)
    
    # Step 1: Create test fixtures
    create_test_fixtures()
    
    # Step 2: Run migration script
    print("\n" + "=" * 80)
    print("Running migration script...")
    print("=" * 80)
    
    from scripts.migrate_to_individual_first import DataMigrator
    
    migrator = DataMigrator(dry_run=False)  # Actually write changes
    migrator.run()
    
    # Step 3: Verify results
    success = verify_migration()
    
    if success:
        print("\n✅ ALL TESTS PASSED! Migration script works correctly.")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED! Migration script has issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
