"""
Tests for updated events routes with individual-first architecture.

Tests the new event features:
- host_user_id instead of hostUid (individual hosts, not households)
- visibility field (private/link_only/public)
- shareable_link generation for viral loop
- visibility updates and shareable_link regeneration
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.core.firebase import db


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test data before each test."""
    # Clear events collection
    events_coll = db.collection("events")
    if hasattr(events_coll, "_docs"):
        events_coll._docs.clear()
    
    # Clear users collection
    users_coll = db.collection("users")
    if hasattr(users_coll, "_docs"):
        users_coll._docs.clear()
    
    yield


def test_create_event_with_individual_host(client, set_claims):
    """Test that events are created with host_user_id (individual), not hostUid (household)."""
    set_claims(uid="host_user_001", email="host@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    response = client.post("/events", json={
        "type": "future",
        "title": "Backyard BBQ",
        "details": "Bring your favorite dish!",
        "startAt": start_time.isoformat(),
        "endAt": end_time.isoformat(),
        "neighborhoods": ["Bayhill"],
        "category": "food"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # ✅ Should use host_user_id (individual)
    assert data["host_user_id"] == "host_user_001"
    assert "hostUid" not in data or data.get("hostUid") is None  # Old field should not exist


def test_create_event_with_default_visibility(client, set_claims):
    """Test that events default to 'public' visibility."""
    set_claims(uid="host_user_002", email="host2@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=1)
    
    response = client.post("/events", json={
        "type": "now",
        "title": "Quick Coffee Meetup",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Eagles Pointe"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["visibility"] == "public"  # Default


def test_create_event_with_public_visibility_generates_link(client, set_claims):
    """Test that public events automatically generate a shareable_link."""
    set_claims(uid="host_user_003", email="host3@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=2)
    
    response = client.post("/events", json={
        "type": "future",
        "title": "Community Yard Sale",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Bayhill"],
        "visibility": "public"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["visibility"] == "public"
    assert data["shareable_link"] is not None
    assert data["shareable_link"].startswith("/e/")
    # ✅ Full UUID (32 hex chars) for cryptographic security (128 bits entropy)
    assert len(data["shareable_link"]) == 35  # /e/ (3 chars) + 32 char UUID hex


def test_create_event_with_link_only_visibility(client, set_claims):
    """Test that link_only events generate shareable links."""
    set_claims(uid="host_user_004", email="host4@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=3)
    
    response = client.post("/events", json={
        "type": "now",
        "title": "Secret Book Club",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Bayhill"],
        "visibility": "link_only"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["visibility"] == "link_only"
    assert data["shareable_link"] is not None
    assert data["shareable_link"].startswith("/e/")


def test_create_event_with_private_visibility_no_link(client, set_claims):
    """Test that private events do NOT generate shareable links."""
    set_claims(uid="host_user_005", email="host5@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    
    response = client.post("/events", json={
        "type": "future",
        "title": "Private Family Dinner",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Eagles Pointe"],
        "visibility": "private"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["visibility"] == "private"
    assert data["shareable_link"] is None  # No link for private events


def test_update_event_visibility_from_private_to_public(client, set_claims):
    """Test that changing visibility from private to public generates a shareable link."""
    set_claims(uid="host_user_006", email="host6@example.com")
    
    # Create private event
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    
    create_response = client.post("/events", json={
        "type": "future",
        "title": "Neighborhood Potluck",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Bayhill"],
        "visibility": "private"
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    assert create_response.json()["shareable_link"] is None
    
    # Update to public
    update_response = client.patch(f"/events/{event_id}", json={
        "visibility": "public"
    })
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["visibility"] == "public"
    assert data["shareable_link"] is not None
    assert data["shareable_link"].startswith("/e/")


def test_update_event_visibility_from_public_to_private(client, set_claims):
    """Test that changing visibility from public to private removes shareable link."""
    set_claims(uid="host_user_007", email="host7@example.com")
    
    # Create public event
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=2)
    
    create_response = client.post("/events", json={
        "type": "now",
        "title": "Open Mic Night",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Eagles Pointe"],
        "visibility": "public"
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    assert create_response.json()["shareable_link"] is not None
    
    # Update to private
    update_response = client.patch(f"/events/{event_id}", json={
        "visibility": "private"
    })
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["visibility"] == "private"
    assert data["shareable_link"] is None  # Link removed


def test_only_host_can_update_event(client, set_claims):
    """Test that only the event host can update the event."""
    # Create event as host_user_008
    set_claims(uid="host_user_008", email="host8@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    
    create_response = client.post("/events", json={
        "type": "future",
        "title": "Garden Party",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Bayhill"]
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Try to update as different user
    set_claims(uid="other_user_009", email="other@example.com")
    
    update_response = client.patch(f"/events/{event_id}", json={
        "title": "Hacked Event"
    })
    
    assert update_response.status_code == 403  # Forbidden


def test_only_host_can_cancel_event(client, set_claims):
    """Test that only the event host can cancel the event."""
    # Create event as host_user_010
    set_claims(uid="host_user_010", email="host10@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(hours=3)
    
    create_response = client.post("/events", json={
        "type": "now",
        "title": "Impromptu Soccer Game",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Eagles Pointe"]
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Try to cancel as different user
    set_claims(uid="other_user_011", email="other2@example.com")
    
    cancel_response = client.patch(f"/events/{event_id}/cancel")
    
    assert cancel_response.status_code == 403  # Forbidden


def test_only_host_can_delete_event(client, set_claims):
    """Test that only the event host can delete the event."""
    # Create event as host_user_012
    set_claims(uid="host_user_012", email="host12@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=2)
    
    create_response = client.post("/events", json={
        "type": "future",
        "title": "Weekend Brunch",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Bayhill"]
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Try to delete as different user
    set_claims(uid="other_user_013", email="other3@example.com")
    
    delete_response = client.delete(f"/events/{event_id}")
    
    assert delete_response.status_code == 403  # Forbidden


def test_host_can_cancel_own_event(client, set_claims):
    """Test that the host can successfully cancel their own event."""
    set_claims(uid="host_user_014", email="host14@example.com")
    
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    
    # Create event
    create_response = client.post("/events", json={
        "type": "future",
        "title": "Morning Yoga",
        "startAt": start_time.isoformat(),
        "neighborhoods": ["Eagles Pointe"]
    })
    assert create_response.status_code == 200
    event_id = create_response.json()["id"]
    
    # Cancel as host
    cancel_response = client.patch(f"/events/{event_id}/cancel")
    
    assert cancel_response.status_code == 200
    data = cancel_response.json()
    assert data["status"] == "canceled"
    assert data["canceledBy"] == "host_user_014"


def test_backward_compatibility_with_hostUid(client, set_claims):
    """Test that events with old hostUid field still work for authorization."""
    set_claims(uid="host_user_015", email="host15@example.com")
    
    now = datetime.now(timezone.utc)
    
    # Manually create event with old hostUid field (simulating old data)
    event_id = "test_event_old_format"
    events_coll = db.collection("events")
    events_coll.document(event_id).set({
        "type": "now",
        "title": "Old Format Event",
        "startAt": now,
        "neighborhoods": ["Bayhill"],
        "hostUid": "host_user_015",  # Old field name
        "status": "active",
        "createdAt": now,
        "updatedAt": now
    })
    
    # Try to update event - should work with backward compatibility
    update_response = client.patch(f"/events/{event_id}", json={
        "title": "Updated Old Event"
    })
    
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Old Event"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
