# app/routes/users.py
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, constr, EmailStr, field_validator, ConfigDict

from app.core.firebase import db
from app.main import verify_token  # adjust if moved

router = APIRouter(tags=["users"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jsonify(x):
    if isinstance(x, datetime):
        return x.astimezone(timezone.utc).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x

def _can_edit(target_uid: str, claims: dict) -> bool:
    """Allow edit if caller owns the doc or has admin claim."""
    return claims.get("uid") == target_uid or bool(claims.get("admin"))

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class UserIn(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    isAdmin: bool = False  # ignored unless caller has admin claim

class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unknown keys

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
        updates: Dict[str, Any] = {}
        if self.name is not None:
            updates["name"] = self.name.strip()
        if self.email is not None:
            updates["email"] = str(self.email)
        if self.isAdmin is not None:
            updates["isAdmin"] = bool(self.isAdmin)
        return updates

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/users", summary="Create or update my user record (owner-only upsert)")
def upsert_my_user(body: UserIn, claims = Depends(verify_token)):
    """Owner-only upsert to users/{uid}. Ignores client-supplied UID/email."""
    uid = claims["uid"]
    email = claims.get("email")
    now = datetime.now(timezone.utc)

    ref = db.collection("users").document(uid)
    snap = ref.get()

    payload = {
        "uid": uid,
        "name": body.name,
        "email": email,
        "updatedAt": now,
    }

    # First create
    if not snap.exists:
        payload["createdAt"] = now
        payload["isAdmin"] = body.isAdmin if claims.get("admin") else False
    else:
        # Existing user: only admin can toggle isAdmin
        if claims.get("admin", False):
            payload["isAdmin"] = body.isAdmin

    ref.set(payload, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

@router.patch("/users/me", summary="Partially update my user (owner-only)")
def patch_my_user(body: UserPatch, claims = Depends(verify_token)):
    uid = claims["uid"]
    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = body.to_update_dict()
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    if "isAdmin" in updates and not claims.get("admin", False):
        updates.pop("isAdmin")

    updates["updatedAt"] = datetime.now(timezone.utc)
    ref.set(updates, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

@router.get("/users/me", summary="Get my user record (owner-only)")
def get_my_user(claims = Depends(verify_token)):
    uid = claims["uid"]
    snap = db.collection("users").document(uid).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

@router.get("/users/{user_id}", summary="Get user by ID (owner-only)")
def get_user_by_id(user_id: str, claims = Depends(verify_token)):
    if claims["uid"] != user_id and not claims.get("admin", False):
        raise HTTPException(status_code=403, detail="Forbidden")
    snap = db.collection("users").document(user_id).get()
    if not snap.exists:
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
    """Owner or admin can patch any user document by UID."""
    if not _can_edit(uid, claims):
        raise HTTPException(status_code=403, detail="Forbidden")

    if payload is None:
        raise HTTPException(status_code=400, detail="Missing JSON body")

    updates = payload.to_update_dict()
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent privilege escalation
    if "isAdmin" in updates and not claims.get("admin", False):
        updates.pop("isAdmin")

    updates["updatedAt"] = datetime.now(timezone.utc)
    ref.set(updates, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["uid"] = doc.id
    return _jsonify(data)
