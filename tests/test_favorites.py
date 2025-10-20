# tests/test_favorites.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def ensure_user():
    db.collection("users").document("brian").set({"uid":"brian","email":"brian@example.com"}, merge=True)
    db.collection("households").document("favH").set({"lastName":"Fav","type":"family","neighborhood":"Bay Hill"})

def test_favorite_toggle():
    ensure_user()

    r = client.post("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    assert "favH" in r.json()["favorites"]

    r = client.delete("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    assert "favH" not in r.json()["favorites"]
