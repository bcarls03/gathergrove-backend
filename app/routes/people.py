# app/routes/people.py
from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional, Tuple, Literal

from fastapi import APIRouter, Depends, Query, HTTPException
from app.main import verify_token
from app.core.firebase import db

router = APIRouter(tags=["people"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_docs(coll):
    """
    Works with real Firestore (stream) and our in-memory fake (._docs).
    Returns list[(id, dict)].
    """
    if hasattr(coll, "stream"):
        return [(doc.id, doc.to_dict() or {}) for doc in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake path
        return list(coll._docs.items())
    return []

def _normalize_household(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize field names so responses have stable keys expected by clients.
    Ensures: 'type', 'neighborhood', and builds 'childAges' from children.
    """
    out = dict(d)

    # household type (always present in output, may be None)
    out["type"] = (
        d.get("type")
        or d.get("householdType")
        or d.get("kind")
        or None
    )

    # neighborhood (always present in output, may be None)
    out["neighborhood"] = d.get("neighborhood") or d.get("neighborhoodCode") or None

    # children could be a list of objects like {"age": 7, "sex": "M"} or ints
    raw_children = d.get("children") or []
    child_ages: List[int] = []
    for kid in raw_children:
        if isinstance(kid, dict) and isinstance(kid.get("age"), int):
            child_ages.append(kid["age"])
        elif isinstance(kid, int):
            child_ages.append(kid)
    out["childAges"] = child_ages

    return out

def _child_ages(doc: Dict[str, Any]) -> List[int]:
    return list(doc.get("childAges") or [])

def _age_match_any(child_ages: List[int], min_age: Optional[int], max_age: Optional[int]) -> bool:
    """Return True if any child age falls within [min_age, max_age]."""
    if not child_ages:
        return False
    lo = 0 if min_age is None else min_age
    hi = 18 if max_age is None else max_age
    for age in child_ages:
        if lo <= age <= hi:
            return True
    return False

def _stable_sort(items: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
    """Deterministic order: lastName (casefold) then id."""
    def key_fn(it):
        _id, doc = it
        last = (doc.get("lastName") or doc.get("householdLastName") or "")
        return (last.casefold(), _id)
    return sorted(items, key=key_fn)

# --- pageToken helpers (base64url: {"cursor":"<docId>"}) ---

def _b64url_encode(d: Dict[str, Any]) -> str:
    raw = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def _b64url_decode(token: str) -> Dict[str, Any]:
    try:
        pad = "=" * ((4 - (len(token) % 4)) % 4)
        raw = base64.urlsafe_b64decode((token + pad).encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        cur = data.get("cursor")
        if not isinstance(cur, str) or not cur:
            raise ValueError
        return data
    except Exception:
        # What our tests/clients expect on malformed tokens
        raise HTTPException(status_code=400, detail="malformed pageToken")

# ---------------------------------------------------------------------------
# GET /people  (derived from households)  — filters + stable pagination
# ---------------------------------------------------------------------------

@router.get("/people", summary="People list (from households)")
def list_people(
    # filters
    neighborhood: Optional[str] = Query(None, description="Filter to a single neighborhood"),
    type: Optional[Literal["family", "empty_nesters", "singles_couples"]] = Query(
        None, description="Household type"
    ),
    minAge: Optional[int] = Query(None, ge=0, le=18, alias="ageMin"),
    maxAge: Optional[int] = Query(None, ge=0, le=18, alias="ageMax"),
    search: Optional[str] = Query(None, min_length=1, max_length=64, description="Last name starts-with"),
    # pagination
    pageToken: Optional[str] = Query(None, description="Opaque cursor token"),
    pageSize: int = Query(20, ge=1, le=50),
    # auth
    claims=Depends(verify_token),
):
    # 1) decode cursor safely (400 on malformed)
    cursor_id: Optional[str] = None
    if pageToken is not None:
        cursor_id = _b64url_decode(pageToken)["cursor"]

    # 2) fetch, normalize, and stable-sort
    docs = _list_docs(db.collection("households"))  # list[(id, dict)]
    # normalize now so filters can use normalized fields
    normed: List[Tuple[str, Dict[str, Any]]] = []
    for hid, data in docs:
        if not data:
            continue
        n = _normalize_household(data)
        n["id"] = hid
        normed.append((hid, n))

    normed = _stable_sort(normed)

    # 3) apply filters BEFORE pagination
    def _matches(doc: Dict[str, Any]) -> bool:
        if type and (doc.get("type") != type):
            return False
        if neighborhood and (str(doc.get("neighborhood") or "").casefold() != neighborhood.casefold()):
            return False
        if search:
            last = (doc.get("lastName") or doc.get("householdLastName") or "")
            if not last.casefold().startswith(search.casefold()):
                return False
        if (minAge is not None) or (maxAge is not None):
            if not _age_match_any(_child_ages(doc), minAge, maxAge):
                return False
        return True

    filtered = [(hid, d) for (hid, d) in normed if _matches(d)]

    # 4) cursor positioning AFTER filtering (cursor is a doc id)
    start_idx = 0
    if cursor_id:
        for i, (hid, _) in enumerate(filtered):
            if hid == cursor_id:
                start_idx = i + 1
                break

    page = filtered[start_idx : start_idx + pageSize]
    items = [
        {
            "id": d["id"],
            "type": d.get("type"),
            "neighborhood": d.get("neighborhood"),
            "childAges": list(d.get("childAges") or []),
        }
        for (_hid, d) in page
    ]

    next_token = None
    if start_idx + pageSize < len(filtered) and page:
        next_token = _b64url_encode({"cursor": page[-1][0]})

    return {"items": items, "nextPageToken": next_token}

# ---------------------------------------------------------------------------
# Favorites (on the user document) — fake+real Firestore compatible
# ---------------------------------------------------------------------------

def _utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)

def _ensure_user_doc(uid: str, email: Optional[str]) -> Dict[str, Any]:
    uref = db.collection("users").document(uid)
    snap = uref.get()
    if not snap or not getattr(snap, "exists", False):
        shell = {
            "uid": uid,
            "email": email,
            "favorites": [],
            "createdAt": _utcnow(),
            "updatedAt": _utcnow(),
        }
        uref.set(shell, merge=True)
        return shell
    return snap.to_dict() or {"uid": uid, "email": email, "favorites": []}

@router.post("/people/{household_id}/favorite", summary="Favorite a household (adds to user.favorites)")
def favorite_household(household_id: str, claims = Depends(verify_token)):
    uid = claims["uid"]
    uref = db.collection("users").document(uid)
    data = _ensure_user_doc(uid, claims.get("email"))
    favs = list(data.get("favorites") or [])
    if household_id not in favs:
        favs.append(household_id)
    uref.set({"favorites": favs, "updatedAt": _utcnow()}, merge=True)
    return {"ok": True, "favorites": favs}

@router.delete("/people/{household_id}/favorite", summary="Unfavorite a household (removes from user.favorites)")
def unfavorite_household(household_id: str, claims = Depends(verify_token)):
    uid = claims["uid"]
    uref = db.collection("users").document(uid)
    data = _ensure_user_doc(uid, claims.get("email"))
    favs = [f for f in list(data.get("favorites") or []) if f != household_id]
    uref.set({"favorites": favs, "updatedAt": _utcnow()}, merge=True)
    return {"ok": True, "favorites": favs}
