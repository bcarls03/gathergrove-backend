# app/core/firebase.py
import os
import os.path
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Dev mode toggle (supports either env var)
# If SKIP_FIREBASE or SKIP_FIREBASE_INIT is "1", we force the fake DB.
_FORCE_DEV = (
    os.getenv("SKIP_FIREBASE") == "1"
    or os.getenv("SKIP_FIREBASE_INIT") == "1"
)

# ---------- Dev: simple in-memory Firestore clone ----------


class _FakeSnap:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return dict(self._data) if self._data is not None else None


class _FakeDoc:
    def __init__(self, coll: "_FakeColl", doc_id: str):
        self._coll = coll
        self.id = doc_id

    def get(self) -> _FakeSnap:
        return _FakeSnap(self.id, self._coll._docs.get(self.id))

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if (
            merge
            and self.id in self._coll._docs
            and self._coll._docs[self.id] is not None
        ):
            base = dict(self._coll._docs[self.id])
            base.update(dict(data))
            self._coll._docs[self.id] = base
        else:
            self._coll._docs[self.id] = dict(data)
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update specific fields in the document"""
        if self.id in self._coll._docs and self._coll._docs[self.id] is not None:
            self._coll._docs[self.id].update(data)
        else:
            self._coll._docs[self.id] = dict(data)


class _FakeColl:
    def __init__(self, name: str, root: Dict[str, Dict[str, Any]]):
        self.name = name
        self._root = root
        self._docs = root.setdefault(name, {})
        self._where_filters = []

    def document(self, doc_id: str) -> _FakeDoc:
        return _FakeDoc(self, doc_id)
    
    def where(self, field: str, op: str, value: Any):
        """Simple where clause for filtering documents"""
        new_coll = _FakeColl(self.name, self._root)
        new_coll._where_filters = self._where_filters + [(field, op, value)]
        return new_coll
    
    def stream(self):
        """Stream documents matching where filters"""
        for doc_id, doc_data in self._docs.items():
            if doc_data is None:
                continue
            
            # Apply where filters
            matches = True
            for field, op, value in self._where_filters:
                doc_value = doc_data.get(field)
                if op == "==":
                    if doc_value != value:
                        matches = False
                        break
                # Add other operators as needed
            
            if matches:
                yield _FakeSnap(doc_id, doc_data)


class _FakeDB:
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}

    def collection(self, name: str) -> _FakeColl:
        return _FakeColl(name, self._data)

    # for /firebase ping
    def collections(self):
        return [_FakeColl(k, self._data) for k in self._data.keys()]


def _make_fake_db() -> _FakeDB:
    logger.warning("Using in-memory fake Firestore (dev mode).")
    return _FakeDB()


# ---------- Prod: real Firebase Admin SDK, with graceful fallback ----------


def _make_real_db():
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("FIREBASE_CRED_PATH")
        or ""
    )

    if not cred_path or not os.path.exists(cred_path):
        # No usable credentials → fall back to fake DB
        logger.warning(
            "Firebase credentials not found at %r; falling back to fake Firestore.",
            cred_path,
        )
        return _make_fake_db()

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    logger.info("Initialized real Firestore with credentials at %r", cred_path)
    return firestore.client()


# Decide which DB to expose
if _FORCE_DEV:
    db = _make_fake_db()
else:
    db = _make_real_db()
