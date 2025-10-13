# tests/conftest.py

# --- Ensure the repo root is on sys.path so `from app ...` works -------------
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -----------------------------------------------------------------------------

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app and the module that contains the routes
from app.main import app, verify_token
import app.routes.users as users_routes


# ------------------------------
# Minimal in-memory Firestore
# ------------------------------
class _FakeSnap:
    def __init__(self, data, doc_id):
        self._data = data
        self.id = doc_id

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return self._data


class _FakeDoc:
    def __init__(self, col_dict, doc_id):
        self._col = col_dict
        self.id = doc_id

    def get(self):
        return _FakeSnap(self._col.get(self.id), self.id)

    def set(self, data, merge=False):
        if merge and self.id in self._col:
            self._col[self.id].update(data)
        else:
            base = self._col.get(self.id, {}) if merge else {}
            base.update(data)
            self._col[self.id] = base


class _FakeCollection:
    def __init__(self, db_data, name):
        self._db_data = db_data
        self._name = name

    def document(self, doc_id):
        col = self._db_data.setdefault(self._name, {})
        return _FakeDoc(col, doc_id)


class FakeDB:
    def __init__(self):
        self._data = {}  # {collection_name: {doc_id: dict}}

    def collection(self, name: str):
        return _FakeCollection(self._data, name)


# ------------------------------
# Pytest fixtures
# ------------------------------
@pytest.fixture
def fake_db(monkeypatch):
    """
    Replace Firestore 'db' used inside app.routes.users with an in-memory fake.
    """
    db = FakeDB()
    # IMPORTANT: patch the symbol where it is used (app.routes.users.db)
    monkeypatch.setattr(users_routes, "db", db, raising=True)
    return db


@pytest.fixture
def client(fake_db, monkeypatch):
    """
    Provide a TestClient with a default non-admin user; tests can override.
    """
    def _override_verify_token():
        return {"uid": "u1", "email": "u1@example.com", "admin": False}

    app.dependency_overrides[verify_token] = _override_verify_token
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def set_claims():
    """
    Helper to switch the caller identity/claims within a test.
    Usage:
        set_claims(uid="u2", admin=True)
    """
    def _setter(uid="u1", email=None, admin=False):
        from app.main import app, verify_token  # re-import to be safe
        def _override():
            return {
                "uid": uid,
                "email": email or f"{uid}@example.com",
                "admin": admin,
            }
        app.dependency_overrides[verify_token] = _override
    return _setter
