# tests/test_people_pagination.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def _make_household(hid: str, last: str, typ: str = "family", hood: str = "Bay Hill", ages=None):
    doc = {
        "lastName": last,
        "type": typ,
        "neighborhood": hood,
        "children": [{"age": a} for a in (ages or [])],
    }
    db.collection("households").document(hid).set(doc, merge=False)

def _reset():
    # wipe only the collections we touch in this file (works with dev fake DB)
    for colname in ("households", "users"):
        coll = db.collection(colname)
        if hasattr(coll, "_docs"):
            coll._docs.clear()

def test_people_pagination_basic_and_bad_token_shape():
    _reset()

    # Seed 3 households; stable IDs ensure deterministic order
    _make_household("H001", "Alpha", ages=[4])
    _make_household("H002", "Bravo", ages=[6])
    _make_household("H003", "Charlie", ages=[8])

    # Page size 2 => first call returns 2 items + nextPageToken
    r1 = client.get("/people?pageSize=2", headers=DEV)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert isinstance(body1, dict)
    assert "items" in body1 and isinstance(body1["items"], list)
    assert len(body1["items"]) == 2
    next_token = body1.get("nextPageToken")
    assert next_token is not None

    # Second page should return the remaining 1 item and no further token
    r2 = client.get(f"/people?pageSize=2&pageToken={next_token}", headers=DEV)
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert len(body2["items"]) == 1
    assert body2.get("nextPageToken") is None

    # Bad token shape should return 400 (defensive)
    r_bad = client.get("/people?pageSize=2&pageToken=%7B%22oops%22%3Atrue%7D", headers=DEV)  # '{"oops":true}'
    assert r_bad.status_code in (400, 422)
