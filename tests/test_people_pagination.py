# tests/test_people_pagination.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def seed_households(n=5):
    # deterministic IDs so ordering/cursors are stable
    for i in range(n):
        db.collection("households").document(f"H{i:02d}").set({
            "lastName": f"Last{i}",
            "type": "family",
            "neighborhood": "Bay Hill",
            "children": [i],  # simple ages [0..n-1]
        }, merge=True)

def test_people_pagination_basic():
    seed_households(5)

    # page 1
    r1 = client.get("/people?pageSize=2", headers=DEV)
    assert r1.status_code == 200
    j1 = r1.json()
    assert isinstance(j1["items"], list)
    assert len(j1["items"]) == 2
    token1 = j1["nextPageToken"]
    assert token1 is not None

    # page 2
    r2 = client.get(f"/people?pageSize=2&pageToken={token1}", headers=DEV)
    assert r2.status_code == 200
    j2 = r2.json()
    assert len(j2["items"]) == 2
    token2 = j2["nextPageToken"]

    # page 3 (leftover)
    r3 = client.get(f"/people?pageSize=2&pageToken={token2}", headers=DEV)
    assert r3.status_code == 200
    j3 = r3.json()
    assert len(j3["items"]) == 1
    assert j3["nextPageToken"] in (None, "")

def test_people_empty_or_bad_token_still_has_shape():
    seed_households(1)
    # Unknown token: implementation may restart or return empty—assert shape not error
    r = client.get("/people?pageSize=1&pageToken=__BAD__", headers=DEV)
    assert r.status_code == 200
    j = r.json()
    assert "items" in j and isinstance(j["items"], list)
    assert "nextPageToken" in j
