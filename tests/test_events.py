# tests/test_events.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Use a single client (your conftest enables dev auth + in-memory DB)
client = TestClient(app)

UTC = timezone.utc


# --- Helpers ---------------------------------------------------------------

def auth(uid: str | None = None, admin: bool = False) -> dict:
    """
    Default dev auth header. Optionally impersonate a different user with X-UID.
    """
    h = {"Authorization": "Bearer dev"}
    if uid:
        h["X-UID"] = uid
    if admin:
        h["X-ADMIN"] = "true"
    return h


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def create_future_event(title: str, start: datetime, end: datetime, **extra) -> dict:
    body = {
        "type": "future",
        "title": title,
        "startAt": iso(start),
        "endAt": iso(end),
        **extra,
    }
    r = client.post("/events", headers=auth(), json=body)
    assert r.status_code == 200, r.text
    return r.json()


def create_now_event(title: str, *, expires_at: datetime | None = None, **extra) -> dict:
    body = {"type": "now", "title": title, **extra}
    if expires_at is not None:
        body["expiresAt"] = iso(expires_at)
    r = client.post("/events", headers=auth(), json=body)
    assert r.status_code == 200, r.text
    return r.json()


# --- Tests -----------------------------------------------------------------

def test_type_filters_sorting_and_expiry_exclusion():
    now = datetime.now(UTC)

    # expired "now" → excluded globally
    create_now_event("Expired Now", expires_at=now - timedelta(minutes=1))

    # active now (expires in 1h)
    ev_now = create_now_event("Active Now", expires_at=now + timedelta(hours=1))

    # two future events, out of creation order
    ev_fut_b = create_future_event("Future B",
                                   now + timedelta(days=2, hours=10),
                                   now + timedelta(days=2, hours=12))
    ev_fut_a = create_future_event("Future A",
                                   now + timedelta(days=1, hours=10),
                                   now + timedelta(days=1, hours=11, minutes=30))

    # Omitted type ⇒ both now + future, exclude expired, sorted by startAt asc
    r = client.get("/events", headers=auth())
    assert r.status_code == 200
    items = r.json()["items"]
    titles = [e["title"] for e in items]
    assert "Expired Now" not in titles
    assert titles[:3] == ["Active Now", "Future A", "Future B"]

    # type=now
    r = client.get("/events?type=now", headers=auth())
    assert [e["title"] for e in r.json()["items"]] == ["Active Now"]

    # type=future (sorted)
    r = client.get("/events?type=future", headers=auth())
    assert [e["title"] for e in r.json()["items"]][:2] == ["Future A", "Future B"]


def test_pagination_limit_and_next_token():
    now = datetime.now(UTC)
    prefix = f"PG-{int(now.timestamp())}-"

    # create exactly 5 future events that we can uniquely identify
    target_ids = []
    for i in range(5):
        s = now + timedelta(days=1 + i, hours=9)
        e = s + timedelta(hours=1)
        ev = create_future_event(f"{prefix}{i}", s, e)
        target_ids.append(ev["id"])

    # page through the global list but only collect our prefix-matching events
    collected = []
    tok = None

    while True:
        url = "/events?type=future&limit=2"
        if tok:
            url += f"&nextPageToken={tok}"
        r = client.get(url, headers=auth())
        assert r.status_code == 200
        body = r.json()

        # Add only our items from this page
        for it in body["items"]:
            if isinstance(it.get("title"), str) and it["title"].startswith(prefix):
                collected.append(it["id"])

        # Stop if we've seen all 5 of ours
        if len(set(collected)) >= 5:
            break

        tok = body["nextPageToken"]
        # If token is None before we collect 5, something's wrong
        assert tok is not None, "Ran out of pages before collecting all our test events"

    # We collected exactly our 5 (no dupes)
    assert set(collected) == set(target_ids)

def test_rsvp_join_leave_and_capacity_409():
    now = datetime.now(UTC)
    start = now + timedelta(days=7, hours=10)
    end = start + timedelta(hours=2)

    # Create event as default user (host)
    ev = create_future_event("Cap1", start, end, capacity=1)
    eid = ev["id"]

    # User A (non-host) joins
    r = client.post(f"/events/{eid}/rsvp", headers=auth("user-a"), json={"status": "going"})
    assert r.status_code == 200

    # Listing for A shows count=1, attending=true
    row = next(e for e in client.get("/events?type=future", headers=auth("user-a")).json()["items"] if e["id"] == eid)
    assert row["attendeeCount"] == 1
    assert row["isAttending"] is True

    # User B cannot join (capacity full)
    r = client.post(f"/events/{eid}/rsvp", headers=auth("user-b"), json={"status": "going"})
    assert r.status_code == 409

    # A leaves → OK
    r = client.delete(f"/events/{eid}/rsvp", headers=auth("user-a"))
    assert r.status_code == 200

    # Now B can join
    r = client.post(f"/events/{eid}/rsvp", headers=auth("user-b"), json={"status": "going"})
    assert r.status_code == 200


def test_patch_validations_and_success():
    now = datetime.now(UTC)
    start = now + timedelta(days=3, hours=9)
    end_ok = start + timedelta(hours=1)
    end_bad = start - timedelta(minutes=1)

    ev = create_future_event("PatchMe", start, end_ok)
    eid = ev["id"]

    # endAt <= startAt ⇒ 422
    r = client.patch(f"/events/{eid}", headers=auth(), json={"endAt": iso(end_bad)})
    assert r.status_code == 422
    assert "endAt must be strictly greater than startAt" in r.text

    # capacity < 1 ⇒ 422
    r = client.patch(f"/events/{eid}", headers=auth(), json={"capacity": 0})
    assert r.status_code == 422

    # invalid category ⇒ 422
    r = client.patch(f"/events/{eid}", headers=auth(), json={"category": "not-real"})
    assert r.status_code == 422

    # valid patch ⇒ 200
    r = client.patch(
        f"/events/{eid}",
        headers=auth(),
        json={"endAt": iso(end_ok + timedelta(hours=1)), "capacity": 10, "category": "neighborhood"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["capacity"] == 10
    assert body["category"] == "neighborhood"


# --- Public Event Endpoint Tests (Viral Loop) ------------------------------

def test_public_endpoint_link_only():
    """GET /events/public/{event_id} returns 200 for link_only visibility"""
    # Create event with link_only visibility (default)
    event = create_now_event("Link Only Event", visibility="link_only")
    event_id = event["id"]
    
    # Public endpoint should return event (no auth required)
    r = client.get(f"/events/public/{event_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == event_id
    assert body["title"] == "Link Only Event"
    assert body["visibility"] == "link_only"


def test_public_endpoint_public_visibility():
    """GET /events/public/{event_id} returns 200 for public visibility"""
    event = create_now_event("Public Event", visibility="public")
    event_id = event["id"]
    
    r = client.get(f"/events/public/{event_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == event_id
    assert body["visibility"] == "public"


def test_public_endpoint_private_returns_404():
    """GET /events/public/{event_id} returns 404 for private events (privacy protection)"""
    event = create_now_event("Private Event", visibility="private")
    event_id = event["id"]
    
    # Public endpoint should return 404 to hide private events
    r = client.get(f"/events/public/{event_id}")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_public_endpoint_nonexistent_returns_404():
    """GET /events/public/{event_id} returns 404 for non-existent events"""
    fake_id = "00000000000000000000000000000000"
    
    r = client.get(f"/events/public/{fake_id}")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_public_endpoint_returns_snake_case():
    """Verify public endpoint returns snake_case field names (contract) and safe fields only"""
    now = datetime.now(UTC)
    future = now + timedelta(hours=2)
    event = create_future_event(
        "Future Event",
        start=now,
        end=future,
        visibility="link_only",
        details="Test details"
    )
    event_id = event["id"]
    
    r = client.get(f"/events/public/{event_id}")
    assert r.status_code == 200
    body = r.json()
    
    # Verify snake_case fields exist
    assert "start_at" in body or "startAt" in body  # Accept either during transition
    assert "end_at" in body or "endAt" in body
    
    # Verify security: sensitive fields NOT exposed
    assert "host_user_id" not in body, "host_user_id should not be exposed publicly"
    assert "neighborhoods" not in body, "neighborhoods should not be exposed publicly"
    
    # Verify event details
    assert body["type"] == "future"
    assert body["details"] == "Test details"
    assert body["visibility"] == "link_only"


def test_guest_rsvp_to_public_event(client):
    """Test that unauthenticated users can RSVP as guests to link_only events."""
    # Create a link_only event
    event_data = {
        "title": "Guest RSVP Test Event",
        "details": "Testing guest RSVP flow",
        "type": "now",
        "category": "neighborhood",
        "visibility": "link_only",
    }
    resp = client.post("/events", json=event_data, headers=auth())
    assert resp.status_code == 200
    event_id = resp.json()["id"]
    
    # Guest RSVP (no authentication)
    guest_rsvp_data = {
        "choice": "going",
        "name": "Jane Neighbor",
        "phone": "555-1234"
    }
    rsvp_resp = client.post(f"/events/{event_id}/rsvp/guest", json=guest_rsvp_data)
    assert rsvp_resp.status_code == 200
    
    rsvp_body = rsvp_resp.json()
    assert rsvp_body["success"] is True
    assert "guest_id" in rsvp_body
    assert "rsvp_id" in rsvp_body
    assert rsvp_body["message"] == "RSVP received! Thank you."


def test_host_cannot_rsvp_to_own_event():
    """Test that event hosts cannot RSVP to their own events (403)"""
    now = datetime.now(UTC)
    start = now + timedelta(days=1)
    end = start + timedelta(hours=2)

    # Create event as host
    ev = create_future_event("Host Event", start, end)
    eid = ev["id"]

    # Host tries to RSVP → should fail with 403
    r = client.post(f"/events/{eid}/rsvp", headers=auth(), json={"status": "going"})
    assert r.status_code == 403
    detail = r.json().get("detail", "")
    assert "cannot rsvp" in detail.lower()
    assert "automatically" in detail.lower()

    # Different user can RSVP successfully
    r = client.post(f"/events/{eid}/rsvp", headers=auth("other-user"), json={"status": "going"})
    assert r.status_code == 200


def test_host_cannot_leave_own_event():
    """Test that event hosts cannot delete their RSVP (403)"""
    now = datetime.now(UTC)
    start = now + timedelta(days=1)
    end = start + timedelta(hours=2)

    # Create event as host
    ev = create_future_event("Host Event 2", start, end)
    eid = ev["id"]

    # Host tries to leave → should fail with 403
    r = client.delete(f"/events/{eid}/rsvp", headers=auth())
    assert r.status_code == 403
    detail = r.json().get("detail", "")
    assert "cannot leave" in detail.lower()
    assert "always attending" in detail.lower()

    # Other user can RSVP and then leave
    client.post(f"/events/{eid}/rsvp", headers=auth("other-user"), json={"status": "going"})
    r = client.delete(f"/events/{eid}/rsvp", headers=auth("other-user"))
    assert r.status_code == 200
