# tests/test_users.py
from http import HTTPStatus


def test_post_creates_user_non_admin(client, set_claims):
    # Non-admin creates their own doc; attempted isAdmin=true is ignored
    set_claims(uid="u1", admin=False)
    resp = client.post("/users", json={"name": "Brian Carlberg", "isAdmin": True})
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["uid"] == "u1"
    assert data["name"] == "Brian Carlberg"
    assert data["isAdmin"] is False
    assert "createdAt" in data and "updatedAt" in data


def test_get_me(client, set_claims):
    # Ensure the user exists first
    set_claims(uid="u2", admin=False)
    create = client.post("/users", json={"name": "User Two"})
    assert create.status_code == HTTPStatus.OK

    resp = client.get("/users/me")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["uid"] == "u2"
    assert data["name"] == "User Two"


def test_patch_me_updates_name_only(client, set_claims):
    # Ensure the user exists first
    set_claims(uid="u3", admin=False)
    create = client.post("/users", json={"name": "Original Name"})
    assert create.status_code == HTTPStatus.OK

    resp = client.patch("/users/me", json={"name": "Brian C."})
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["name"] == "Brian C."
    assert data["isAdmin"] is False  # non-admin cannot elevate


def test_owner_only_get_forbidden_for_other_uid(client, set_claims):
    # Create u4
    set_claims(uid="u4", admin=False)
    client.post("/users", json={"name": "User Four"})

    # u5 tries to fetch u4 -> 403
    set_claims(uid="u5", admin=False)
    resp = client.get("/users/u4")
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_get_specific_user_404_when_missing(client, set_claims):
    # Brand-new identity with no doc -> 404
    set_claims(uid="u6", admin=False)
    resp = client.get("/users/u6")
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_admin_can_set_isAdmin(client, set_claims):
    set_claims(uid="admin1", admin=True)
    resp = client.post("/users", json={"name": "Site Admin", "isAdmin": True})
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["uid"] == "admin1"
    assert data["isAdmin"] is True

    resp2 = client.patch("/users/me", json={"isAdmin": True})
    assert resp2.status_code == HTTPStatus.OK
    assert resp2.json()["isAdmin"] is True
