# tests/test_people.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def seed_households_for_people():
    coll = db.collection("households")
    coll.document("p1").set({"lastName": "Adams", "type": "family", "neighborhood": "Bay Hill",
                             "adults": ["A1"], "children": [{"age": 4}]} )
    coll.document("p2").set({"lastName": "Baker", "type": "emptyNest", "neighborhood": "Bay Hill",
                             "adults": ["B1","B2"], "children": []})
    coll.document("p3").set({"lastName": "Clark", "type": "family", "neighborhood": "Eagles Point",
                             "adults": ["C1"], "children": [{"age": 9}, {"age": 12}]})

def test_people_filters_and_pagination():
    seed_households_for_people()

    r = client.get("/people?neighborhood=Bay%20Hill&type=family", headers=DEV)
    assert r.status_code == 200
    data = r.json()
    assert all(it["neighborhood"] == "Bay Hill" for it in data["items"])
    assert all(it["type"] == "family" for it in data["items"])

    r = client.get("/people?ageMin=5&ageMax=10", headers=DEV)
    assert r.status_code == 200
    ages_ok = all(any(5 <= a <= 10 for a in it["childAges"]) for it in r.json()["items"])
    assert ages_ok

    r = client.get("/people?limit=1", headers=DEV)
    first = r.json()
    assert "nextPageToken" in first
    token = first["nextPageToken"]

    if token:
        r2 = client.get(f"/people?limit=2&pageToken={token}", headers=DEV)
        assert r2.status_code == 200
