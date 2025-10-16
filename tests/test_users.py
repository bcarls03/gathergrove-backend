# tests/test_users.py
from http import HTTPStatus

# ---------------------------------------------------------------------------
# Existing tests (kept as-is)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New tests: PATCH /users/{id} (owner/admin)
# ---------------------------------------------------------------------------

def test_patch_user_id_owner_200_updates_name(client, set_claims):
    """
    Owner patches their own user doc via /users/{id} and updates name.
    """
    set_claims(uid="p1", admin=False)
    # ensure doc exists
    create = client.post("/users", json={"name": "Old Name"})
    assert create.status_code == HTTPStatus.OK

    resp = client.patch("/users/p1", json={"name": "New Name"})
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert body["uid"] == "p1"
    assert body["name"] == "New Name"
    assert "updatedAt" in body


def test_patch_user_id_owner_200_updates_email(client, set_claims):
    """
    Owner can update email (validated by EmailStr).
    """
    set_claims(uid="p2", admin=False)
    client.post("/users", json={"name": "Person Two"})
    resp = client.patch("/users/p2", json={"email": "new@example.com"})
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["email"] == "new@example.com"


def test_patch_user_id_forbidden_403_other_user(client, set_claims):
    """
    Non-admin cannot patch someone else's doc.
    """
    # create target user p3
    set_claims(uid="p3", admin=False)
    client.post("/users", json={"name": "Target User"})

    # switch identity to different user
    set_claims(uid="intruder", admin=False)
    resp = client.patch("/users/p3", json={"name": "Hacker Rename"})
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_patch_user_id_400_empty_body(client, set_claims):
    """
    Empty JSON object should 400 (no valid fields to update).
    """
    set_claims(uid="p4", admin=False)
    client.post("/users", json={"name": "Seed"})
    resp = client.patch("/users/p4", json={})
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_patch_user_id_422_unknown_field_rejected(client, set_claims):
    """
    extra='forbid' on the model should reject unknown fields → FastAPI returns 422.
    """
    set_claims(uid="p5", admin=False)
    client.post("/users", json={"name": "Seed"})
    resp = client.patch("/users/p5", json={"notAField": "x"})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
