from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_event_lifecycle():
    # create
    payload = {
        "type": "future",
        "title": "Neighborhood hot cocoa night",
        "details": "Bring your favorite mug!",
        "startAt": "2025-12-15T23:00:00Z",
        "neighborhoods": ["Bay Hill", "Eagles Point"],
    }
    r = client.post("/events", json=payload, headers=DEV)
    assert r.status_code in (200, 201)
    data = r.json()
    assert "id" in data
    event_id = data["id"]

    # get by id
    r = client.get(f"/events/{event_id}", headers=DEV)
    assert r.status_code == 200
    assert r.json()["title"] == payload["title"]

    # list
    r = client.get("/events", params={"type": "future"}, headers=DEV)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # rsvp
    r = client.post(f"/events/{event_id}/rsvp", json={"status": "going"}, headers=DEV)
    assert r.status_code in (200, 201, 204)
