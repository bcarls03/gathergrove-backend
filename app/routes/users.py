# app/routes/users.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Path
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
        if self.name is not None:  out["name"] = self.name.strip()
        if self.email is not None: out["email"] = str(self.email)
        if self.isAdmin is not None: out["isAdmin"] = bool(self.isAdmin)
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
    else:
        if claims.get("admin", False):
            payload["isAdmin"] = body.isAdmin

    ref.set(payload, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

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
    data["id"] = uid
    return _jsonify(data)

@router.get("/users/me", summary="Get my user (owner-only)")
def get_my_user(claims=Depends(verify_token)):
    uid = claims["uid"]
    snap = db.collection("users").document(uid).get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

@router.get("/users/{user_id}", summary="Get user by ID (owner or admin)")
def get_user_by_id(user_id: str, claims=Depends(verify_token)):
    if claims["uid"] != user_id and not claims.get("admin", False):
        raise HTTPException(status_code=403, detail="Forbidden")
    snap = db.collection("users").document(user_id).get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

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
    data["uid"] = uid
    return _jsonify(data)

@router.get("/users/me/favorites", summary="List my favorited households")
def list_my_favorites(claims=Depends(verify_token)):
    uid = claims["uid"]

    # Ensure the user document exists
    uref = db.collection("users").document(uid)
    usnap = uref.get()
    if not usnap or not usnap.exists:
        uref.set({"uid": uid, "email": claims.get("email"), "favorites": []}, merge=True)
        fav_ids: List[str] = []
    else:
        fav_ids = list((usnap.to_dict() or {}).get("favorites") or [])

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
