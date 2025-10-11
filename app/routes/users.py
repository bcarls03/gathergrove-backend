# app/routes/users.py
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, constr
from app.core.firebase import db
from app.main import verify_token  # adjust if you moved verify_token elsewhere

router = APIRouter(tags=["users"])

# ---- Models ----------------------------------------------------------------
class UserIn(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    isAdmin: bool = False

# ---- Helpers (optional) ----------------------------------------------------
def _jsonify(x):
    if isinstance(x, datetime):
        return x.astimezone(timezone.utc).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x

# ---- Routes ----------------------------------------------------------------
@router.post("/users")
def upsert_my_user(body: UserIn, claims = Depends(verify_token)):
    """
    Owner-only upsert to users/{uid}. Ignores any client-supplied UID/email.
    - Sets createdAt only on first write
    - Always refreshes updatedAt
    """
    uid = claims["uid"]
    email = claims.get("email")
    now = datetime.now(timezone.utc)

    ref = db.collection("users").document(uid)
    snap = ref.get()
    payload = {
        "uid": uid,
        "name": body.name,
        "isAdmin": body.isAdmin,
        "email": email,
        "updatedAt": now,
    }
    if not snap.exists:
        payload["createdAt"] = now

    ref.set(payload, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

@router.get("/users/me")
def get_my_user(claims = Depends(verify_token)):
    """
    Convenience read for the caller's own doc.
    """
    uid = claims["uid"]
    snap = db.collection("users").document(uid).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

@router.get("/users/{user_id}")
def get_user_by_id(user_id: str, claims = Depends(verify_token)):
    """
    Owner-only read of a specific user document.
    """
    if claims["uid"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    snap = db.collection("users").document(user_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

# ---------- PATCH /users/me -------------------------------------------------
from typing import Optional
from pydantic import constr

class UserPatch(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=1)] = None
    isAdmin: Optional[bool] = None  # optional—can restrict later if needed

@router.patch("/users/me", summary="Partially update my user (owner-only)")
def patch_my_user(body: UserPatch, claims = Depends(verify_token)):
    uid = claims["uid"]
    ref = db.collection("users").document(uid)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {k: v for k, v in body.dict(exclude_unset=True).items() if v is not None}
    updates["updatedAt"] = datetime.now(timezone.utc)
    ref.set(updates, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

