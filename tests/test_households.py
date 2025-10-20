# tests/test_households.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def seed_households():
    coll = db.collection("households")
    coll.document("h1").set({
        "lastName": "Carlberg",
        "type": "family",
        "neighborhood": "Bay Hill",
        "adults": ["Brian", "Alex"],
        "children": [{"age": 6, "sex": "M"}],
        "createdAt": __import__("datetime").datetime.now(),
    })
    coll.document("h2").set({
        "lastName": "Nguyen",
        "type": "singleCouple",
        "neighborhood": "Eagles Point",
        "adults": ["Kim"],
        "children": [],
        "createdAt": __import__("datetime").datetime.now(),
    })

def test_households_list_filters():
    seed_households()
    r = client.get("/households", headers=DEV)
    assert r.status_code == 200
    assert len(r.json()) >= 2

    r = client.get("/households?neighborhood=Bay%20Hill", headers=DEV)
    assert r.status_code == 200
    data = r.json()
    assert all(h["neighborhood"] == "Bay Hill" for h in data)

    r = client.get("/households?type=singleCouple", headers=DEV)
    assert r.status_code == 200
    data = r.json()
    assert all(h["type"] == "singleCouple" for h in data)
