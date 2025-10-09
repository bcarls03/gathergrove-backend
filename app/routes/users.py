# app/routes/users.py
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.firebase import db
from app.main import verify_token  # adjust if you moved verify_token elsewhere

router = APIRouter(tags=["users"])

# ---------- helpers ----------------------------------------------------------

def _jsonify(x):
    if isinstance(x, datetime): return x.isoformat()
    if isinstance(x, list):     return [_jsonify(v) for v in x]
    if isinstance(x, dict):     return {k: _jsonify(v) for k, v in x.items()}
    return x

# ---------- models -----------------------------------------------------------

class User(BaseModel):
    uid: str
    name: str
    email: str
    isAdmin: bool = False

# ---------- routes -----------------------------------------------------------

@router.post("/users")
def create_user(user: User, claims = Depends(verify_token)):
    """
    Create/overwrite the caller's user doc. Enforces uid == token.uid.
    """
    if user.uid != claims["uid"]:
        raise HTTPException(status_code=403, detail="Forbidden (uid mismatch)")

    doc_ref = db.collection("users").document(user.uid)
    doc_ref.set({
        "uid": user.uid,
        "name": user.name,
        "email": user.email,
        "isAdmin": user.isAdmin,
        "createdAt": datetime.utcnow(),
    })
    return {"message": f"User {user.name} created successfully.", "id": user.uid}

@router.get("/users/me")
def get_my_user(claims = Depends(verify_token)):
    """
    Convenience read for the caller's own doc.
    NOTE: This static route is placed BEFORE /users/{user_id} so it isn't shadowed.
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
