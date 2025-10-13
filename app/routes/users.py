# app/routes/users.py
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, constr
from app.core.firebase import db
from app.main import verify_token  # adjust if you moved verify_token elsewhere

router = APIRouter(tags=["users"])

# ---- Helpers ----------------------------------------------------------------
def _jsonify(x):
    if isinstance(x, datetime):
        return x.astimezone(timezone.utc).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x

# ---- Models -----------------------------------------------------------------
class UserIn(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    isAdmin: bool = False  # ignored unless caller has admin claim

class UserPatch(BaseModel):
    # All fields optional; only provided keys will be written
    name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    isAdmin: Optional[bool] = None  # ignored unless caller has admin claim

# ---- Routes -----------------------------------------------------------------
@router.post("/users", summary="Create or update my user record (owner-only upsert)")
def upsert_my_user(body: UserIn, claims = Depends(verify_token)):
    """
    Owner-only upsert to users/{uid}. Ignores any client-supplied UID/email.
    Sets createdAt only on first write, always refreshes updatedAt.
    """
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

    # If the user does not exist yet, set createdAt and default isAdmin to False
    if not snap.exists:
        payload["createdAt"] = now
        if claims.get("admin", False):
            payload["isAdmin"] = body.isAdmin
        else:
            payload["isAdmin"] = False  # ensure always present for first create
    else:
        # Existing user: only allow admin to modify isAdmin
        if claims.get("admin", False):
            payload["isAdmin"] = body.isAdmin
        # Non-admins: skip this field so merge=True preserves existing value

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

    # Only include provided, non-null fields
    updates = body.dict(exclude_unset=True, exclude_none=True)

    # 🔒 Prevent privilege escalation: ignore isAdmin for non-admins
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
    if claims["uid"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    snap = db.collection("users").document(user_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)
