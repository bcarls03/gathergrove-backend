# tests/test_favorites.py
from fastapi.testclient import TestClient
from app.main import app
from app.core.firebase import db

client = TestClient(app)
DEV = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}

def ensure_user_and_household():
    db.collection("users").document("brian").set(
        {"uid": "brian", "email": "brian@example.com"},
        merge=True,
    )
    db.collection("households").document("favH").set(
        {"lastName": "Fav", "type": "family", "neighborhood": "Bay Hill"},
        merge=False,
    )

def test_favorite_toggle_and_idempotency():
    ensure_user_and_household()

    # add
    r = client.post("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert "favH" in body["favorites"]

    # idempotent add (no duplicates)
    r = client.post("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    favs = r.json()["favorites"]
    assert "favH" in favs and len(favs) == len(set(favs))

    # remove
    r = client.delete("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert "favH" not in body["favorites"]

    # idempotent remove
    r = client.delete("/people/favH/favorite", headers=DEV)
    assert r.status_code == 200
    assert "favH" not in r.json()["favorites"]
