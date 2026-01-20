#!/usr/bin/env python3
"""
Seed "Happening Now" events directly into the fake DB (dev mode only).
Run this with the backend server running.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from app.core.firebase import db

def seed_happening_now_events():
    """Seed test 'Happening Now' events"""
    
    print("🌱 Seeding 'Happening Now' events...")
    
    events_collection = db.collection("events")
    
    # Event 1: Playdate
    event1_id = "test_event_playdate_001"
    event1_data = {
        "type": "now",
        "title": "Playground Meetup at Oak Hill Park",
        "details": "Kids running around at the playground! Come join us for some spontaneous fun. Bring snacks to share!",
        "category": "playdate",
        "neighborhoods": ["Oak Hill"],
        "host_user_id": "dev-uid",
        "hostUid": "dev-uid",
        "visibility": "public",
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "status": "active",
        "goingCount": 3,
        "maybeCount": 1,
        "cantCount": 0,
    }
    events_collection.document(event1_id).set(event1_data)
    print(f"✅ Created: {event1_data['title']}")
    print(f"   Started {15} minutes ago")
    
    # Event 2: Neighborhood
    event2_id = "test_event_neighborhood_001"
    event2_data = {
        "type": "now",
        "title": "Coffee & Chat at Starbucks",
        "details": "Impromptu coffee meetup for any neighbors who want to connect. I'll be at the corner table with a green GatherGrove tote.",
        "category": "neighborhood",
        "neighborhoods": ["Oak Hill"],
        "host_user_id": "dev-uid",
        "hostUid": "dev-uid",
        "visibility": "public",
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "status": "active",
        "goingCount": 2,
        "maybeCount": 0,
        "cantCount": 0,
    }
    events_collection.document(event2_id).set(event2_data)
    print(f"✅ Created: {event2_data['title']}")
    print(f"   Started {45} minutes ago")
    
    # Event 3: Pet
    event3_id = "test_event_pet_001"
    event3_data = {
        "type": "now",
        "title": "Dog Walk Around The Block",
        "details": "Taking my golden retriever for a walk. Other dogs welcome! Meeting at the corner of Oak St and Maple.",
        "category": "pet",
        "neighborhoods": ["Oak Hill"],
        "host_user_id": "dev-uid",
        "hostUid": "dev-uid",
        "visibility": "public",
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(minutes=45)).isoformat(),
        "status": "active",
        "goingCount": 1,
        "maybeCount": 0,
        "cantCount": 0,
    }
    events_collection.document(event3_id).set(event3_data)
    print(f"✅ Created: {event3_data['title']}")
    print(f"   Just started")
    
    print("\n✨ Done! 3 'Happening Now' events created.")
    print("🔄 Refresh Discovery page to see them: http://localhost:5173/discovery")

if __name__ == "__main__":
    try:
        seed_happening_now_events()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Backend server is running")
        print("2. Using fake DB (SKIP_FIREBASE_INIT=1)")
        sys.exit(1)
