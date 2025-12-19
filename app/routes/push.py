# app/routes/push.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.firebase import db
from app.deps.auth import verify_token  # ✅ IMPORTANT: avoid importing from app.main

router = APIRouter(prefix="/push", tags=["push"])

# ---------- helpers ----------

def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ---------- models ----------

class PushRegisterIn(BaseModel):
    # from frontend: { uid, token, platform }
    uid: Optional[str] = Field(
        default=None,
        description="Optional; we normally trust the authenticated user instead.",
    )
    token: str = Field(..., min_length=10, description="Device push token")
    platform: Optional[str] = Field(default=None, description="ios | android | web | unknown")


class PushRegisterOut(BaseModel):
    ok: bool
    uid: str
    tokens: List[str]
    updatedAt: datetime


class PushTokensOut(BaseModel):
    ok: bool
    uid: str
    tokens: List[str]
    platforms: Dict[str, str]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# ---------- routes ----------

@router.post(
    "/register",
    response_model=PushRegisterOut,
    summary="Register a device push token for the current user",
)
def register_push_token(
    body: PushRegisterIn,
    claims: Dict[str, Any] = Depends(verify_token),
):
    """
    Stores tokens under:
      collection("pushTokens").document(uid)

    {
      uid,
      tokens: [token1, token2, ...],
      platforms: { token: platform },
      createdAt,
      updatedAt
    }
    """
    uid = claims.get("uid") or body.uid
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing uid for push registration",
        )

    token = (body.token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="token is required",
        )

    platform = (body.platform or "").strip().lower() or "unknown"
    now = _aware(datetime.utcnow())

    ref = db.collection("pushTokens").document(uid)
    snap = ref.get()
    existing: Dict[str, Any] = snap.to_dict() or {}

    old_tokens: List[str] = list(existing.get("tokens") or [])
    tokens_set = set(t for t in old_tokens if isinstance(t, str) and t.strip())
    tokens_set.add(token)
    tokens = sorted(tokens_set)

    platforms: Dict[str, str] = dict(existing.get("platforms") or {})
    platforms[token] = platform

    payload: Dict[str, Any] = {
        "uid": uid,
        "tokens": tokens,
        "platforms": platforms,
        "updatedAt": now,
    }
    if not getattr(snap, "exists", False):
        payload["createdAt"] = now

    ref.set(payload, merge=True)

    return PushRegisterOut(ok=True, uid=uid, tokens=tokens, updatedAt=now)


@router.get(
    "/tokens",
    response_model=PushTokensOut,
    summary="Debug: return the current user's registered push tokens",
)
def get_my_push_tokens(
    claims: Dict[str, Any] = Depends(verify_token),
):
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing uid")

    ref = db.collection("pushTokens").document(uid)
    snap = ref.get()
    data: Dict[str, Any] = snap.to_dict() or {}

    return PushTokensOut(
        ok=True,
        uid=uid,
        tokens=list(data.get("tokens") or []),
        platforms=dict(data.get("platforms") or {}),
        createdAt=data.get("createdAt"),
        updatedAt=data.get("updatedAt"),
    )


@router.delete(
    "/tokens",
    response_model=PushRegisterOut,
    summary="Debug: clear the current user's registered push tokens",
)
def clear_my_push_tokens(
    claims: Dict[str, Any] = Depends(verify_token),
):
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing uid")

    now = _aware(datetime.utcnow())
    ref = db.collection("pushTokens").document(uid)

    ref.set(
        {"uid": uid, "tokens": [], "platforms": {}, "updatedAt": now, "createdAt": now},
        merge=False,
    )

    return PushRegisterOut(ok=True, uid=uid, tokens=[], updatedAt=now)
