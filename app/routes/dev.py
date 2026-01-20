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
