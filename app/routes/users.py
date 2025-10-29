# app/routes/users.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, EmailStr, constr, field_validator

from app.core.firebase import db
from app.main import verify_token

router = APIRouter(tags=["users"])

# ----------------------------- Helpers --------------------------------
def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def _jsonify(x):
    if isinstance(x, datetime): return _aware(x).isoformat()
    if isinstance(x, list):     return [_jsonify(v) for v in x]
    if isinstance(x, dict):     return {k: _jsonify(v) for k, v in x.items()}
    return x

def _can_edit(target_uid: str, claims: dict) -> bool:
    return claims.get("uid") == target_uid or bool(claims.get("admin"))

def _child_ages(raw_children) -> List[int]:
    ages: List[int] = []
    for kid in (raw_children or []):
        if isinstance(kid, dict) and isinstance(kid.get("age"), int):
            ages.append(kid["age"])
        elif isinstance(kid, int):
            ages.append(kid)
    return ages

def _ensure_user_doc(uid: str, email: Optional[str]) -> Dict[str, Any]:
    """
    Ensure the user doc exists; create minimal shell if missing.
    Returns the dict form of the user (may be empty on first create).
    """
    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap or not getattr(snap, "exists", False):
        now = _aware(datetime.now(timezone.utc))
        payload = {
            "uid": uid,
            "email": email,
            "createdAt": now,
            "updatedAt": now,
            "isAdmin": False,
            "favorites": [],
        }
        ref.set(payload, merge=True)
        return payload
    return snap.to_dict() or {}

def _safe_user_shape(doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize outgoing user shape for clients/tests.
    """
    out = {
        "id": doc_id,
        "uid": data.get("uid") or doc_id,
        "name": data.get("name"),
        "email": data.get("email"),
        "isAdmin": bool(data.get("isAdmin", False)),
        "createdAt": data.get("createdAt"),
        "updatedAt": data.get("updatedAt"),
    }
    return out

def _paginate_ids(ids: List[str], page_size: int, page_token: Optional[str]) -> Tuple[List[str], Optional[str]]:
    """
    Very simple pagination that sorts ids and slices by page_token (which is last seen id).
    """
    ids_sorted = sorted(ids)
    start = 0
    if page_token:
        try:
            start = ids_sorted.index(page_token) + 1
        except ValueError:
            start = 0
    end = start + page_size
    page = ids_sorted[start:end]
    next_token = page[-1] if end < len(ids_sorted) and page else None
    return page, next_token

# ----------------------------- Models ---------------------------------
class UserIn(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    isAdmin: bool = False  # ignored unless caller has admin claim

class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    email: Optional[EmailStr] = None
    isAdmin: Optional[bool] = None  # ignored unless caller has admin claim

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("name cannot be empty")
        return v

    def to_update_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if self.name is not None:     out["name"] = self.name.strip()
        if self.email is not None:    out["email"] = str(self.email)
        if self.isAdmin is not None:  out["isAdmin"] = bool(self.isAdmin)
        return out

# ------------------------------ Routes --------------------------------

@router.post("/users", summary="Create or update my user (owner-only upsert)")
def upsert_my_user(body: UserIn, claims=Depends(verify_token)):
    uid = claims["uid"]
    email = claims.get("email")
    now = _aware(datetime.now(timezone.utc))

    ref = db.collection("users").document(uid)
    snap = ref.get()

    payload: Dict[str, Any] = {
        "uid": uid,
        "name": body.name,
        "email": email,
        "updatedAt": now,
    }

    if not getattr(snap, "exists", False):
        payload["createdAt"] = now
        payload["isAdmin"] = body.isAdmin if claims.get("admin") else False
        payload.setdefault("favorites", [])
    else:
        if claims.get("admin", False):
            payload["isAdmin"] = body.isAdmin

    ref.set(payload, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    return _jsonify(_safe_user_shape(doc.id, data))

@router.patch("/users/me", summary="Partially update my user (owner-only)")
def patch_my_user(body: UserPatch, claims=Depends(verify_token)):
    uid = claims["uid"]
    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = body.to_update_dict()
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    if "isAdmin" in updates and not claims.get("admin", False):
        updates.pop("isAdmin")

    updates["updatedAt"] = _aware(datetime.now(timezone.utc))
    ref.set(updates, merge=True)

    data = ref.get().to_dict() or {}
    return _jsonify(_safe_user_shape(uid, data))

@router.get("/users/me", summary="Get my user (owner-only)")
def get_my_user(claims=Depends(verify_token)):
    uid = claims["uid"]
    snap = db.collection("users").document(uid).get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    return _jsonify(_safe_user_shape(snap.id, data))

@router.get("/users/{user_id}", summary="Get user by ID (owner or admin)")
def get_user_by_id(user_id: str, claims=Depends(verify_token)):
    if claims["uid"] != user_id and not claims.get("admin", False):
        raise HTTPException(status_code=403, detail="Forbidden")
    snap = db.collection("users").document(user_id).get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    return _jsonify(_safe_user_shape(snap.id, data))

@router.patch("/users/{uid}", summary="PATCH by UID (owner or admin)")
def patch_user_by_id(
    uid: str = Path(..., description="User document id (uid)"),
    payload: UserPatch = None,
    claims: dict = Depends(verify_token),
):
    if not _can_edit(uid, claims):
        raise HTTPException(status_code=403, detail="Forbidden")
    if payload is None:
        raise HTTPException(status_code=400, detail="Missing JSON body")

    updates = payload.to_update_dict()
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    if "isAdmin" in updates and not claims.get("admin", False):
        updates.pop("isAdmin")

    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates["updatedAt"] = _aware(datetime.now(timezone.utc))
    ref.set(updates, merge=True)

    data = ref.get().to_dict() or {}
    return _jsonify(_safe_user_shape(uid, data))

# ------------------------- Favorites (MVP) ------------------------------

@router.get("/users/me/favorites", summary="List my favorited households")
def list_my_favorites(claims=Depends(verify_token)):
    uid = claims["uid"]

    u = _ensure_user_doc(uid, claims.get("email"))
    fav_ids: List[str] = list(u.get("favorites") or [])
    if not fav_ids:
        return {"items": [], "nextPageToken": None}

    items: List[Dict[str, Any]] = []
    hcoll = db.collection("households")
    for hid in fav_ids:
        hsnap = hcoll.document(hid).get()
        if not hsnap or not hsnap.exists:
            continue
        h = hsnap.to_dict() or {}
        items.append({
            "id": hsnap.id,
            "lastName": h.get("lastName"),
            "type": h.get("type") or h.get("householdType") or h.get("kind"),
            "neighborhood": h.get("neighborhood") or h.get("neighborhoodCode"),
            "childAges": _child_ages(h.get("children")),
        })

    items.sort(key=lambda x: ((x.get("lastName") or "").lower(), x.get("id")))
    return {"items": _jsonify(items), "nextPageToken": None}

@router.post(
    "/users/me/favorites/{household_id}",
    summary="Add a household to my favorites (idempotent)"
)
def add_favorite(household_id: str, claims=Depends(verify_token)):
    uid = claims["uid"]
    email = claims.get("email")

    # Ensure both docs exist
    _ensure_user_doc(uid, email)
    hsnap = db.collection("households").document(household_id).get()
    if not hsnap or not hsnap.exists:
        raise HTTPException(status_code=404, detail="Household not found")

    uref = db.collection("users").document(uid)
    usnap = uref.get()
    udata = usnap.to_dict() or {}
    favs = set(udata.get("favorites") or [])
    if household_id not in favs:
        favs.add(household_id)
        uref.set({
            "favorites": list(sorted(favs)),
            "updatedAt": _aware(datetime.now(timezone.utc))
        }, merge=True)

    return {"ok": True}

@router.delete(
    "/users/me/favorites/{household_id}",
    summary="Remove a household from my favorites (idempotent)"
)
def remove_favorite(household_id: str, claims=Depends(verify_token)):
    uid = claims["uid"]
    uref = db.collection("users").document(uid)
    usnap = uref.get()
    if not usnap or not usnap.exists:
        # Treat as success; nothing to remove
        return {"ok": True}

    udata = usnap.to_dict() or {}
    favs = set(udata.get("favorites") or [])
    if household_id in favs:
        favs.remove(household_id)
        uref.set({
            "favorites": list(sorted(favs)),
            "updatedAt": _aware(datetime.now(timezone.utc))
        }, merge=True)

    return {"ok": True}

# ---------------------------- Admin List -------------------------------

@router.get("/users", summary="Admin: list users", description="Admin-only, simple pagination.")
def admin_list_users(
    claims=Depends(verify_token),
    page_size: int = Query(default=50, ge=1, le=200),
    page_token: Optional[str] = Query(default=None, description="Return results after this last seen user id"),
):
    if not claims.get("admin", False):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Works with real Firestore (stream) and local in-memory fake
    coll = db.collection("users")
    ids: List[str] = []
    if hasattr(coll, "stream"):  # real Firestore
        for doc in coll.stream():
            ids.append(doc.id)
    elif hasattr(coll, "_docs"):  # dev fake path
        ids = list(coll._docs.keys())

    page_ids, next_token = _paginate_ids(ids, page_size, page_token)

    items: List[Dict[str, Any]] = []
    for uid in page_ids:
        snap = coll.document(uid).get()
        if not snap or not snap.exists:
            continue
        data = snap.to_dict() or {}
        items.append(_safe_user_shape(uid, data))

    return _jsonify({"items": items, "nextPageToken": next_token})

# --------------------------- DEV Utilities ----------------------------

import os

@router.post("/_dev/seed/household/{hid}", summary="[DEV] create a dummy household")
def dev_seed_household(hid: str, claims=Depends(verify_token)):
    # Only allow when dev auth is enabled (your tests set ALLOW_DEV_AUTH=1)
    if os.getenv("ALLOW_DEV_AUTH") != "1":
        raise HTTPException(status_code=403, detail="Dev seeding disabled")

    now = _aware(datetime.now(timezone.utc))
    db.collection("households").document(hid).set({
        "lastName": "Testers",
        "type": "family",
        "neighborhood": "BAYHILL",
        "children": [{"age": 10}, {"age": 7}],
        "createdAt": now,
        "updatedAt": now,
    }, merge=True)
    return {"ok": True, "id": hid}
