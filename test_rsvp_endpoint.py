#!/usr/bin/env python3
"""
Test script to debug the public RSVP endpoint.
Simulates the exact flow to see full error traceback.
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.firebase import db
from datetime import datetime, timezone

# Create test data
print("=== Setting up test data ===")

# 1. Create a test event
event_id = "test-event-123"
event_data = {
    "id": event_id,
    "title": "Test Event",
    "details": "Testing RSVP",
    "startAt": "2026-02-01T18:00:00+00:00",
    "endAt": None,
    "category": "food",
    "visibility": "public",
    "host_user_id": "test-host",
    "status": "active"
}

db.collection("events").document(event_id).set(event_data)
print(f"✅ Created event: {event_id}")

# 2. Create a test invitation
token = "test-token-abc123"
invitation_id = f"inv_{event_id}_{token}"
invitation_data = {
    "id": invitation_id,
    "event_id": event_id,
    "invitee_type": "phone_number",
    "invitee_id": None,
    "phone_number": "+15551234567",
    "invited_by": "test-host",
    "status": "pending",
    "rsvp_token": token,
    "guest_name": None,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "sms_sent_at": None,
    "sms_delivered_at": None,
    "sms_failed_at": None
}

db.collection("invitations").document(invitation_id).set(invitation_data)
print(f"✅ Created invitation with token: {token}")

# 3. Try to retrieve the event via the token (simulate the endpoint logic)
print("\n=== Testing public RSVP endpoint logic ===")

try:
    # Find invitation by token
    invitations_ref = db.collection("invitations")
    
    invitation = None
    if hasattr(invitations_ref, "_docs"):
        # Fake Firestore
        print("Using fake Firestore")
        for inv_data in invitations_ref._docs.values():
            if inv_data.get("rsvp_token") == token:
                invitation = inv_data
                print(f"✅ Found invitation: {invitation['id']}")
                break
    
    if not invitation:
        print("❌ ERROR: Invitation not found!")
        sys.exit(1)
    
    # Get event details
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        print("❌ ERROR: Event not found!")
        sys.exit(1)
    
    event_data_retrieved = event_doc.to_dict()
    print(f"✅ Retrieved event: {event_data_retrieved['title']}")
    
    # Get host name
    host_id = invitation["invited_by"]
    print(f"Looking up host: {host_id}")
    
    host_household = db.collection("households").document(host_id).get()
    host_name = "A neighbor"
    
    if host_household.exists:
        host_data = host_household.to_dict()
        last_name = host_data.get("lastName", "")
        adult_names = host_data.get("adultNames", [])
        if last_name:
            host_name = f"The {last_name} Family"
        elif adult_names:
            host_name = adult_names[0]
        print(f"✅ Host found: {host_name}")
    else:
        print(f"⚠️  Host household not found, using default: {host_name}")
    
    # Handle both camelCase and snake_case field names
    start_at = event_data_retrieved.get("startAt") or event_data_retrieved.get("start_at")
    end_at = event_data_retrieved.get("endAt") or event_data_retrieved.get("end_at")
    
    print(f"✅ start_at: {start_at}")
    print(f"✅ end_at: {end_at}")
    
    # Try to create PublicEventView
    from app.models.invitation import PublicEventView
    
    public_view = PublicEventView(
        id=event_id,
        title=event_data_retrieved.get("title", "Event"),
        details=event_data_retrieved.get("details"),
        start_at=start_at,
        end_at=end_at,
        host_name=host_name,
        category=event_data_retrieved.get("category", "other"),
        visibility=event_data_retrieved.get("visibility", "public")
    )
    
    print(f"\n✅ SUCCESS! PublicEventView created:")
    print(f"   ID: {public_view.id}")
    print(f"   Title: {public_view.title}")
    print(f"   Host: {public_view.host_name}")
    print(f"   Start: {public_view.start_at}")
    print(f"\n🎉 Public RSVP endpoint logic works correctly!")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
