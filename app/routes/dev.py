"""
Development-only routes for testing and seeding data.
Only available when SKIP_FIREBASE_INIT=1 (in-memory fake DB).
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from typing import Literal
from app.core.firebase import db
import uuid

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/seed-events", status_code=status.HTTP_201_CREATED)
def seed_happening_now_events():
    """
    Seed 3 test "Happening Now" events into the database.
    
    DEV MODE ONLY: This endpoint only works with in-memory fake Firestore.
    Use this to quickly populate test events for the Discovery page.
    
    Events are created with fresh timestamps each time you call this,
    so they'll always appear as "happening now" for testing.
    """
    
    # First, clear any existing test events to avoid duplicates
    existing = db.collection("events").stream()
    for event in existing:
        event.reference.delete()
    
    now = datetime.utcnow()
    
    # Event 1: Playground Meetup (just started)
    event1_id = f"event_{uuid.uuid4().hex[:12]}"
    event1 = {
        "id": event1_id,
        "type": "now",  # ✅ Critical: This makes it show in "Happening Now"
        "title": "Playground Meetup at Oak Hill Park",
        "details": "Bring the kids! We'll be at the big playground near the swings. Look for the blue umbrella.",
        "category": "playdate",
        "hostUid": "demo_user_1",
        "hostLabel": "The Johnson Family",
        "neighborhoods": ["oak-hill", "riverside"],
        "startAt": (now - timedelta(minutes=10)).isoformat(),  # Started 10 min ago
        "expiresAt": (now + timedelta(hours=3)).isoformat(),  # Expires in 3 hours (long window)
        "status": "active",
        "visibility": "neighbors",
        "goingCount": 3,
        "maybeCount": 1,
        "createdAt": (now - timedelta(minutes=15)).isoformat(),
        "updatedAt": now.isoformat(),
    }
    
    # Event 2: Coffee & Chat (started 5 min ago)
    event2_id = f"event_{uuid.uuid4().hex[:12]}"
    event2 = {
        "id": event2_id,
        "type": "now",
        "title": "Coffee & Chat at Starbucks",
        "details": "Grabbing coffee for the next hour. Join if you're nearby! Inside seating.",
        "category": "neighborhood",
        "hostUid": "demo_user_2",
        "hostLabel": "Sarah Miller",
        "neighborhoods": ["downtown", "oak-hill"],
        "startAt": (now - timedelta(minutes=5)).isoformat(),  # Started 5 min ago
        "expiresAt": (now + timedelta(hours=2)).isoformat(),  # Expires in 2 hours
        "status": "active",
        "visibility": "neighbors",
        "goingCount": 2,
        "maybeCount": 0,
        "createdAt": (now - timedelta(minutes=10)).isoformat(),
        "updatedAt": now.isoformat(),
    }
    
    # Event 3: Dog Walk (just started)
    event3_id = f"event_{uuid.uuid4().hex[:12]}"
    event3 = {
        "id": event3_id,
        "type": "now",
        "title": "Dog Walk Around The Block",
        "details": "Taking Max for a walk. Other pups welcome to join!",
        "category": "pet",
        "hostUid": "demo_user_3",
        "hostLabel": "Mike Chen",
        "neighborhoods": ["riverside"],
        "startAt": (now - timedelta(minutes=2)).isoformat(),  # Started 2 min ago
        "expiresAt": (now + timedelta(hours=1)).isoformat(),  # Expires in 1 hour
        "status": "active",
        "visibility": "neighbors",
        "goingCount": 1,
        "maybeCount": 1,
        "createdAt": (now - timedelta(minutes=5)).isoformat(),
        "updatedAt": now.isoformat(),
    }
    
    # Save to fake Firestore
    db.collection("events").document(event1_id).set(event1)
    db.collection("events").document(event2_id).set(event2)
    db.collection("events").document(event3_id).set(event3)
    
    return {
        "message": "✨ Successfully seeded 3 'Happening Now' events (fresh timestamps)",
        "events": [
            {"id": event1_id, "title": event1["title"], "expiresIn": "3 hours"},
            {"id": event2_id, "title": event2["title"], "expiresIn": "2 hours"},
            {"id": event3_id, "title": event3["title"], "expiresIn": "1 hour"},
        ],
        "note": "Events cleared and re-created with fresh timestamps. Call this endpoint anytime to refresh."
    }


@router.delete("/clear-events", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_events():
    """
    Delete all events from the database.
    
    DEV MODE ONLY: Use this to reset test data.
    """
    
    # Get all event documents
    events = db.collection("events").stream()
    
    count = 0
    for event in events:
        event.reference.delete()
        count += 1
    
    return {"message": f"Deleted {count} events"}


@router.post("/seed-households", status_code=status.HTTP_201_CREATED)
def seed_test_households():
    """
    Seed 12 diverse test households for Discovery page testing.
    
    DEV MODE ONLY: This endpoint only works with in-memory fake Firestore.
    Creates households with:
    - Different household types (families, couples, singles)
    - Various kid ages and configurations
    - Different neighborhoods
    - Mix of location_precision values (street vs zipcode)
    """
    
    from datetime import datetime, timezone, timedelta
    
    def generate_birth_date(age_years):
        """Generate a birth date for a kid of given age"""
        now = datetime.now(timezone.utc)
        birth_date = now - timedelta(days=age_years * 365)
        return {
            "birthMonth": birth_date.month,
            "birthYear": birth_date.year
        }
    
    now = datetime.now(timezone.utc).isoformat()
    
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
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
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
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
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
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
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
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
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
                {**generate_birth_date(6), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(4), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "234 Hill Crest Road",
                "city": "Portland",
                "state": "OR",
                "zip": "97203"
            },
            "latitude": 45.517,
            "longitude": -122.677,
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
        },
        
        # ============= SINGLE PARENT =============
        {
            "id": "household-wilson-006",
            "uid": "user-wilson-006",
            "email": "amanda.wilson@example.com",
            "lastName": "Wilson",
            "adultNames": ["Amanda"],
            "neighborhood": "Oak Ridge",
            "householdType": "single_parent",
            "kids": [
                {**generate_birth_date(8), "sex": "boy", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "321 Cedar Street",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.516,
            "longitude": -122.679,
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
        },
        
        # ============= MORE FAMILIES =============
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
            "latitude": 45.518,
            "longitude": -122.676,
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
        },
        
        # ============= COUPLES =============
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
            "latitude": 45.5125,
            "longitude": -122.683,
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
        },
        
        {
            "id": "household-martinez-009",
            "uid": "user-martinez-009",
            "email": "sophia.martinez@example.com",
            "lastName": "Martinez",
            "adultNames": ["Sophia", "Daniel"],
            "neighborhood": "Oak Ridge",
            "householdType": "couple",
            "kids": [],
            "address": {
                "street": "890 Park Avenue",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.517,
            "longitude": -122.678,
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
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
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
        },
        
        {
            "id": "household-lee-011",
            "uid": "user-lee-011",
            "email": "kevin.lee@example.com",
            "lastName": "Lee",
            "adultNames": ["Kevin"],
            "neighborhood": "Riverside",
            "householdType": "single",
            "kids": [],
            "address": {
                "street": "901 Bridge Street",
                "city": "Portland",
                "state": "OR",
                "zip": "97202"
            },
            "latitude": 45.513,
            "longitude": -122.684,
            "location_precision": "street",
            "createdAt": now,
            "updatedAt": now
        },
        
        {
            "id": "household-robinson-012",
            "uid": "user-robinson-012",
            "email": "ashley.robinson@example.com",
            "lastName": "Robinson",
            "adultNames": ["Ashley", "Chris"],
            "neighborhood": "Oak Ridge",
            "householdType": "family_with_kids",
            "kids": [
                {**generate_birth_date(11), "sex": "boy", "awayAtCollege": False, "canBabysit": True},
                {**generate_birth_date(9), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
                {**generate_birth_date(7), "sex": "girl", "awayAtCollege": False, "canBabysit": False},
            ],
            "address": {
                "street": "567 Forest Drive",
                "city": "Portland",
                "state": "OR",
                "zip": "97201"
            },
            "latitude": 45.5175,
            "longitude": -122.6785,
            "location_precision": "zipcode",
            "createdAt": now,
            "updatedAt": now
        },
    ]
    
    # Save all households to Firestore
    for household in households:
        db.collection("households").document(household["id"]).set(household)
    
    # Count by type
    type_counts = {}
    precision_counts = {"street": 0, "zipcode": 0}
    for h in households:
        htype = h.get("householdType", "unknown")
        type_counts[htype] = type_counts.get(htype, 0) + 1
        precision = h.get("location_precision")
        if precision in precision_counts:
            precision_counts[precision] += 1
    
    return {
        "message": f"✨ Successfully seeded {len(households)} test households!",
        "household_types": type_counts,
        "location_precision": precision_counts,
        "note": "Households include mix of street-level and ZIP-only location precision for testing."
    }
