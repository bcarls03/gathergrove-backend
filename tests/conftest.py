# tests/conftest.py
"""
Pytest bootstrap for GatherGrove.

- Puts repo root on sys.path so `from app ...` works.
- Forces dev auth + in-memory Firestore for tests (no real cloud needed).
- Provides a TestClient fixture and a set_claims helper.
"""

# --- Make repo importable ----------------------------------------------------
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Force dev mode BEFORE importing app.main --------------------------------
# These prevent firebase admin init and allow X-* headers in tests.
os.environ.setdefault("ALLOW_DEV_AUTH", "1")
os.environ.setdefault("SKIP_FIREBASE_INIT", "1")
os.environ.setdefault("CI", "true")  # harmless; mirrors CI behavior

# --- Now it's safe to import the app ----------------------------------------
import pytest
from fastapi.testclient import TestClient
from app.main import app, verify_token

# Optional: handy dev headers if a test wants to use header-based auth instead
DEV_HEADERS = {"X-Uid": "brian", "X-Email": "brian@example.com", "X-Admin": "false"}
ADMIN_HEADERS = {"X-Uid": "admin", "X-Email": "admin@example.com", "X-Admin": "true"}


@pytest.fixture
def client():
    """
    Default TestClient. If a test doesn't pass headers, we still supply a
    non-admin caller via dependency override so routes that require auth work.
    """
    def _claims():
        return {"uid": "brian", "email": "brian@example.com", "admin": False}

    app.dependency_overrides[verify_token] = _claims
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def set_claims():
    """
    Quickly change the caller identity inside a test.

    Usage:
        set_claims(uid="u2", admin=True)
        r = client.get("/users/me")  # now acts as that caller
    """
    def _setter(uid="brian", email=None, admin=False):
        def _claims():
            return {
                "uid": uid,
                "email": email or f"{uid}@example.com",
                "admin": bool(admin),
            }
        app.dependency_overrides[verify_token] = _claims
    return _setter
