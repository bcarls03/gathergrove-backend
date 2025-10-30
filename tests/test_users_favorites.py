# tests/test_users_favorites.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

DEV    = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}
ADMIN  = {"X-Uid": "admin", "X-Email": "admin@example.com", "X-Admin": "true"}
ALICE  = {"X-Uid": "alice", "X-Email": "alice@example.com", "X-Admin": "false"}
BOB    = {"X-Uid": "bob", "X-Email": "bob@example.com", "X-Admin": "false"}

def _post_json(url, headers, json=None):
    return client.post(url, headers=headers, json=json or {})

def test_favorites_add_list_remove_happy_path():
    # seed a household
    r = client.post("/_dev/seed/household/H123", headers=DEV)
    assert r.status_code == 200

    # start empty
    r = client.get("/users/me/favorites", headers=DEV)
    assert r.status_code == 200
    assert r.json()["items"] == []

    # add
    r = client.post("/users/me/favorites/H123", headers=DEV)
    assert r.status_code == 200 and r.json()["ok"] is True

    # list shows normalized shape
    r = client.get("/users/me/favorites", headers=DEV)
    js = r.json()
    assert r.status_code == 200
    assert js["items"][0]["id"] == "H123"
    assert set(js["items"][0]).issuperset({"id","lastName","type","neighborhood","childAges"})

    # idempotent add (no dupes)
    r = client.post("/users/me/favorites/H123", headers=DEV)
    assert r.status_code == 200
    r = client.get("/users/me/favorites", headers=DEV)
    assert len(r.json()["items"]) == 1

    # remove
    r = client.delete("/users/me/favorites/H123", headers=DEV)
    assert r.status_code == 200 and r.json()["ok"] is True
    r = client.get("/users/me/favorites", headers=DEV)
    assert r.json()["items"] == []

def test_owner_vs_admin_permissions_and_upsert():
    # upsert self users
    assert _post_json("/users", DEV,   {"name":"Brian"}).status_code == 200
    assert _post_json("/users", ALICE, {"name":"Alice"}).status_code == 200
    assert _post_json("/users", BOB,   {"name":"Bob"}).status_code == 200

    # non-admin cannot read others
    r = client.get("/users/alice", headers=BOB)
    assert r.status_code == 403

    # admin can read list
    r = client.get("/users", headers=ADMIN)
    assert r.status_code == 200
    assert "items" in r.json()

def test_admin_list_pagination():
    # ensure at least 3 users exist
    _post_json("/users", DEV,   {"name":"Brian"})
    _post_json("/users", ALICE, {"name":"Alice"})
    _post_json("/users", BOB,   {"name":"Bob"})

    r1 = client.get("/users?page_size=2", headers=ADMIN)
    assert r1.status_code == 200
    js1 = r1.json()
    assert len(js1["items"]) <= 2
    token = js1.get("nextPageToken")

    if token:
        r2 = client.get(f"/users?page_size=2&page_token={token}", headers=ADMIN)
        assert r2.status_code == 200
        js2 = r2.json()
        # next page should not repeat the last id from page1
        first_page_ids = {u["id"] for u in js1["items"]}
        assert all(u["id"] not in first_page_ids for u in js2["items"])
