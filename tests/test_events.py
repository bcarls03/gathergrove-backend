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

    ev = create_future_event("Cap1", start, end, capacity=1)
    eid = ev["id"]

    # User A joins
    r = client.post(f"/events/{eid}/rsvp", headers=auth(), json={"status": "going"})
    assert r.status_code == 200

    # Listing for A shows count=1, attending=true
    row = next(e for e in client.get("/events?type=future", headers=auth()).json()["items"] if e["id"] == eid)
    assert row["attendeeCount"] == 1
    assert row["isAttending"] is True

    # User B cannot join (capacity full)
    r = client.post(f"/events/{eid}/rsvp", headers=auth("user-b"), json={"status": "going"})
    assert r.status_code == 409

    # A leaves → OK
    r = client.delete(f"/events/{eid}/rsvp", headers=auth())
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
