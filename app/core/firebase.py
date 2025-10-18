# app/core/firebase.py
import os
import os.path
from typing import Dict, Any, Optional

# Dev mode toggle (supports either env var)
_DEV = os.getenv("SKIP_FIREBASE") == "1" or os.getenv("SKIP_FIREBASE_INIT") == "1"

# ---------- Dev: simple in-memory Firestore clone ----------
if _DEV:
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
        def __init__(self, coll: "._FakeColl", doc_id: str):
            self._coll = coll
            self.id = doc_id

        def get(self) -> _FakeSnap:
            return _FakeSnap(self.id, self._coll._docs.get(self.id))

        def set(self, data: Dict[str, Any], merge: bool = False) -> None:
            if merge and self.id in self._coll._docs and self._coll._docs[self.id] is not None:
                base = dict(self._coll._docs[self.id])
                base.update(dict(data))
                self._coll._docs[self.id] = base
            else:
                self._coll._docs[self.id] = dict(data)

    class _FakeColl:
        def __init__(self, name: str, root: Dict[str, Dict[str, Any]]):
            self.name = name
            self._root = root
            self._docs = root.setdefault(name, {})

        def document(self, doc_id: str) -> _FakeDoc:
            return _FakeDoc(self, doc_id)

    class _FakeDB:
        def __init__(self):
            self._data: Dict[str, Dict[str, Any]] = {}

        def collection(self, name: str) -> _FakeColl:
            return _FakeColl(name, self._data)

        # for /firebase ping
        def collections(self):
            return [_FakeColl(k, self._data) for k in self._data.keys()]

    db = _FakeDB()

# ---------- Prod: real Firebase Admin SDK ----------
else:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("FIREBASE_CRED_PATH")
        or ""
    )
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(f"Service account JSON not found at: {cred_path!r}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
