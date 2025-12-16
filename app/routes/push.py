# app/routes/push.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.firebase import db
from app.main import verify_token

router = APIRouter(prefix="/push", tags=["push"])

# ---------- helpers ----------

def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _jsonify(x):
    if isinstance(x, datetime):
        return _aware(x).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x


# ---------- models ----------

class PushRegisterIn(BaseModel):
    # from frontend: { uid, token, platform }
    uid: Optional[str] = Field(
        default=None,
        description="Optional; we normally trust the authenticated user instead.",
    )
    token: str = Field(..., min_length=10, description="Device push token")
    platform: Optional[str] = Field(
        default=None, description="ios | android | web | unknown"
    )


class PushRegisterOut(BaseModel):
    ok: bool
    uid: str
    tokens: List[str]
    updatedAt: datetime


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
    Saves the device push token under a per-user document:

      collection("pushTokens").document(uid) = {
        uid,
        tokens: [token1, token2, ...],
        platforms: { token: platform },
        createdAt,
        updatedAt
      }

    Works with both real Firestore and the in-memory fake.
    """

    # Auth wins; body.uid is just a fallback for dev tools if needed
    uid = claims.get("uid") or body.uid
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing uid for push registration",
        )

    token = body.token.strip()
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

    # maintain a de-duplicated token list
    old_tokens: List[str] = list(existing.get("tokens") or [])
    tokens_set = set(old_tokens)
    tokens_set.add(token)
    tokens = sorted(tokens_set)

    # map token → platform (optional but handy later)
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

    return PushRegisterOut(
        ok=True,
        uid=uid,
        tokens=tokens,
        updatedAt=now,
    )
