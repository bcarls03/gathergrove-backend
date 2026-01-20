#!/usr/bin/env python3
"""
Create test "Happening Now" events for Discovery page testing.
"""

import requests
import json
from datetime import datetime, timedelta, timezone

API_BASE = "http://localhost:8000"

# Test events to create
test_events = [
    {
        "type": "now",
        "title": "Playground Meetup at Oak Hill Park",
        "details": "Kids running around at the playground! Come join us for some spontaneous fun. Bring snacks to share!",
        "category": "playdate",
        "neighborhoods": ["Oak Hill"],
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
    },
    {
        "type": "now",
        "title": "Coffee & Chat at Starbucks",
        "details": "Impromptu coffee meetup for any neighbors who want to connect. I'll be at the corner table with a green GatherGrove tote.",
        "category": "neighborhood",
        "neighborhoods": ["Oak Hill"],
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    },
    {
        "type": "now",
        "title": "Dog Walk Around The Block",
        "details": "Taking my golden retriever for a walk. Other dogs welcome! Meeting at the corner of Oak St and Maple.",
        "category": "pet",
        "neighborhoods": ["Oak Hill"],
        "startAt": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(minutes=45)).isoformat(),
    }
]

def create_event(event_data):
    """Create a single event via the API"""
    # Note: This requires authentication. For dev mode, we'll use direct database access
    print(f"\n📅 Creating event: {event_data['title']}")
    print(f"   Type: {event_data['type']}")
    print(f"   Category: {event_data['category']}")
    print(f"   Started: {event_data['startAt']}")
    print(f"   Expires: {event_data['expiresAt']}")
    
    # For dev mode with fake DB, we need to post to the API
    # You'll need to get an auth token from the browser
    print("\n⚠️  To create events via API, you need an auth token.")
    print("   Alternative: Use the UI to create 'Happening Now' events")
    print("   Go to: http://localhost:5173/compose/happening")

def main():
    print("=" * 70)
    print("Test 'Happening Now' Events Creator")
    print("=" * 70)
    
    print("\n📋 Events to create:")
    for i, event in enumerate(test_events, 1):
        print(f"\n{i}. {event['title']}")
        print(f"   {event['details'][:60]}...")
        print(f"   Category: {event['category']}")
    
    print("\n" + "=" * 70)
    print("🔧 HOW TO CREATE THESE EVENTS:")
    print("=" * 70)
    print("\n1. Via UI (Recommended):")
    print("   a. Go to: http://localhost:5173")
    print("   b. Click 'Home' tab")
    print("   c. Click '⚡ Happening Now' button")
    print("   d. Fill in title, details, category")
    print("   e. Click 'Post Event'")
    print("   f. Refresh Discovery page")
    
    print("\n2. Via API (Requires auth token):")
    print("   POST /events")
    print("   Body: See test_events array in this script")
    
    print("\n3. Via Backend Script (If using fake DB):")
    print("   You can add events directly to the fake DB")
    print("   See: gathergrove-backend/app/core/firebase.py")
    
    print("\n" + "=" * 70)
    print("Sample Event JSON:")
    print("=" * 70)
    print(json.dumps(test_events[0], indent=2))
    
    print("\n✨ After creating events, refresh Discovery page to see them!")

if __name__ == "__main__":
    main()
