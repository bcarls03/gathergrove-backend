# app/core/firebase.py
import os
import os.path

# Allow CI/tests to skip real Firebase initialization.
if os.getenv("SKIP_FIREBASE_INIT") == "1":
    class _PlaceholderDB:
        """Minimal placeholder; tests will monkeypatch app.routes.users.db."""
        def collection(self, *_args, **_kwargs):
            raise RuntimeError("DB not initialized (SKIP_FIREBASE_INIT=1).")
    db = _PlaceholderDB()
else:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or
        os.getenv("FIREBASE_CRED_PATH") or
        ""
    )
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(f"Service account JSON not found at: {cred_path!r}")

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
