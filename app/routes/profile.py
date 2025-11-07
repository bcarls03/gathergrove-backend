# app/routes/profile.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone

# --- Firestore setup (use the app's shared Firestore handle) ---
try:
    from app.core.firebase import db as _db
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"Failed to import Firestore db from app.core.firebase: {e}")

router = APIRouter(prefix="/profile", tags=["profile"])

# ---------- Models ----------

class ProfileUpdate(BaseModel):
    # Top-level profile fields the user can change
    display_last_name: Optional[str] = Field(None, description="Household display last name override")
    visibility: Optional[str] = Field(
        None, description="One of: 'neighbors' (default), 'private', 'public'"
    )
    bio: Optional[str] = Field(None, max_length=500)

    # Relationship / feed tuning
    favorites: Optional[List[str]] = Field(default=None, description="Set full favorites list (overwrites)")
    neighbors_include: Optional[List[str]] = Field(default=None, description="Always include these household IDs")
    neighbors_exclude: Optional[List[str]] = Field(default=None, description="Hide these household IDs")

    # Any future flags
    notifications_enabled: Optional[bool] = None

    @validator("visibility")
    def validate_visibility(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"neighbors", "private", "public"}
        if v not in allowed:
            raise ValueError(f"visibility must be one of {allowed}")
        return v


class ProfileOut(BaseModel):
    uid: str
    email: str
    display_last_name: Optional[str] = None
    visibility: str = "neighbors"
    bio: Optional[str] = None
    favorites: List[str] = []
    neighbors_include: List[str] = []
    neighbors_exclude: List[str] = []
    notifications_enabled: bool = True
    created_at: datetime
    updated_at: datetime


# ---------- Helpers ----------

def _profiles_col():
    return _db.collection("profiles")

def _now() -> datetime:
    return datetime.now(timezone.utc)

def require_identity(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_uid: Optional[str] = Header(default=None, alias="X-Uid"),
    x_email: Optional[str] = Header(default=None, alias="X-Email"),
) -> Dict[str, str]:
    """
    Minimal identity guard that matches your dev/prod header pattern.
    """
    if not x_uid or not x_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Uid or X-Email headers",
        )
    # In dev, you may send a dummy Authorization; in prod you'll validate before reaching here.
    if not authorization:
        pass
    return {"uid": x_uid, "email": x_email}


def _default_profile(uid: str, email: str) -> Dict[str, Any]:
    now = _now()
    return {
        "uid": uid,
        "email": email,
        "display_last_name": None,
        "visibility": "neighbors",
        "bio": None,
        "favorites": [],
        "neighbors_include": [],
        "neighbors_exclude": [],
        "notifications_enabled": True,
        "created_at": now,
        "updated_at": now,
    }


def _doc_to_out(doc: Dict[str, Any]) -> ProfileOut:
    return ProfileOut(**doc)


# ---------- Routes ----------

@router.get("", response_model=ProfileOut)
def get_my_profile(identity = Depends(require_identity)):
    """
    Return the caller's profile; creates a default document if missing.
    """
    uid = identity["uid"]
    email = identity["email"]
    ref = _profiles_col().document(uid)
    snap = ref.get()
    if not getattr(snap, "exists", False):
        data = _default_profile(uid, email)
        ref.set(data)
        return _doc_to_out(data)

    data = snap.to_dict() or {}
    # Backfill any newly added fields without breaking old docs
    changed = False
    for k, v in _default_profile(uid, email).items():
        if k not in data:
            data[k] = v
            changed = True
    if changed:
        data["updated_at"] = _now()
        ref.update({"updated_at": data["updated_at"], **{k: data[k] for k in data.keys()}})

    return _doc_to_out(data)


@router.patch("", response_model=ProfileOut)
def patch_my_profile(payload: ProfileUpdate, identity = Depends(require_identity)):
    """
    Partial update of profile. If you pass favorites / neighbors_*,
    those arrays are replaced (not merged) to keep semantics simple.
    """
    uid = identity["uid"]
    ref = _profiles_col().document(uid)
    snap = ref.get()
    if not getattr(snap, "exists", False):
        base = _default_profile(uid, identity["email"])
        ref.set(base)
        current = base
    else:
        current = snap.to_dict() or {}

    update: Dict[str, Any] = {}
    # Simple scalar fields
    if payload.display_last_name is not None:
        update["display_last_name"] = payload.display_last_name
    if payload.visibility is not None:
        update["visibility"] = payload.visibility
    if payload.bio is not None:
        update["bio"] = payload.bio
    if payload.notifications_enabled is not None:
        update["notifications_enabled"] = bool(payload.notifications_enabled)

    # Replace-list semantics
    if payload.favorites is not None:
        seen, cleaned = set(), []
        for h in payload.favorites:
            if h not in seen:
                seen.add(h)
                cleaned.append(h)
        update["favorites"] = cleaned

    if payload.neighbors_include is not None:
        update["neighbors_include"] = sorted(set(payload.neighbors_include))
    if payload.neighbors_exclude is not None:
        update["neighbors_exclude"] = sorted(set(payload.neighbors_exclude))

    if not update:
        return _doc_to_out(current)

    update["updated_at"] = _now()
    ref.update(update)
    current.update(update)
    return _doc_to_out(current)


@router.get("/favorites", response_model=List[str])
def list_favorites(identity = Depends(require_identity)):
    uid = identity["uid"]
    snap = _profiles_col().document(uid).get()
    if not getattr(snap, "exists", False):
        return []
    data = snap.to_dict() or {}
    return data.get("favorites", [])


# ---- Non-transactional favorites (works in dev + prod) ----

@router.put("/favorites/{household_id}", response_model=List[str])
def add_favorite(household_id: str, identity = Depends(require_identity)):
    uid = identity["uid"]
    ref = _profiles_col().document(uid)
    snap = ref.get()

    if not getattr(snap, "exists", False):
        base = _default_profile(uid, identity["email"])
        base["favorites"] = [household_id]
        base["updated_at"] = _now()
        ref.set(base)
        return base["favorites"]

    data = snap.to_dict() or {}
    favs: List[str] = list(data.get("favorites", []))
    if household_id not in favs:
        favs.append(household_id)
        ref.update({"favorites": favs, "updated_at": _now()})
    return favs


@router.delete("/favorites/{household_id}", response_model=List[str])
def remove_favorite(household_id: str, identity = Depends(require_identity)):
    uid = identity["uid"]
    ref = _profiles_col().document(uid)
    snap = ref.get()

    # Handle both property and method forms of "exists"
    exists_attr = getattr(snap, "exists", False)
    exists = exists_attr() if callable(exists_attr) else bool(exists_attr)
    if not exists:
        return []

    data = snap.to_dict() or {}
    favs = [h for h in data.get("favorites", []) if h != household_id]

    # Try update; if the backend doesn't support update, merge with set()
    try:
        ref.update({"favorites": favs, "updated_at": _now()})
    except Exception:
        ref.set({"favorites": favs, "updated_at": _now()}, merge=True)

    return favs

@router.get("/overrides", response_model=Dict[str, List[str]])
def get_overrides(identity = Depends(require_identity)):
    uid = identity["uid"]
    snap = _profiles_col().document(uid).get()
    if not getattr(snap, "exists", False):
        return {"neighbors_include": [], "neighbors_exclude": []}
    data = snap.to_dict() or {}
    return {
        "neighbors_include": data.get("neighbors_include", []),
        "neighbors_exclude": data.get("neighbors_exclude", []),
    }


@router.put("/overrides", response_model=Dict[str, List[str]])
def put_overrides(
    body: Dict[str, List[str]], identity = Depends(require_identity)
):
    """
    Replace override lists. Body shape:
    { "neighbors_include": [...], "neighbors_exclude": [...] }
    """
    uid = identity["uid"]
    inc = body.get("neighbors_include", [])
    exc = body.get("neighbors_exclude", [])
    ref = _profiles_col().document(uid)
    updates = {
        "neighbors_include": sorted(set(inc)),
        "neighbors_exclude": sorted(set(exc)),
        "updated_at": _now(),
    }
    snap = ref.get()
    if not getattr(snap, "exists", False):
        base = _default_profile(uid, identity["email"])
        base.update(updates)
        ref.set(base)
    else:
        ref.update(updates)
    return {"neighbors_include": updates["neighbors_include"], "neighbors_exclude": updates["neighbors_exclude"]}
