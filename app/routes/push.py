# app/routes/push.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.firebase import db
from app.deps.auth import verify_token  # ✅ IMPORTANT: avoid importing from app.main

router = APIRouter(prefix="/push", tags=["push"])

COLL = "pushTokens"


# ---------- helpers ----------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Return a UTC-aware datetime (assumes naive = UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _list_docs(coll):
    """Works with real Firestore (stream) and our in-memory fake (._docs)."""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


def _get_doc(coll_name: str, doc_id: str) -> Dict[str, Any]:
    """Get doc by id in real Firestore or dev fake."""
    coll = db.collection(coll_name)

    # real Firestore
    try:
        snap = coll.document(doc_id).get()
        if snap and getattr(snap, "exists", False):
            return snap.to_dict() or {}
    except Exception:
        pass

    # dev fake
    if hasattr(coll, "_docs"):
        return coll._docs.get(doc_id) or {}

    # fallback scan
    for _id, rec in _list_docs(coll):
        if _id == doc_id:
            return rec or {}
    return {}


def _set_doc(coll_name: str, doc_id: str, payload: Dict[str, Any], merge: bool = True) -> None:
    """Set doc by id in real Firestore or dev fake."""
    coll = db.collection(coll_name)
    ref = coll.document(doc_id)

    # real Firestore + dev fake typically support .set
    try:
        ref.set(payload, merge=merge)
        return
    except Exception:
        pass

    # dev fake fallback
    if hasattr(coll, "_docs"):
        if merge and isinstance(coll._docs.get(doc_id), dict):
            cur = dict(coll._docs.get(doc_id) or {})
            cur.update(payload)
            coll._docs[doc_id] = cur
        else:
            coll._docs[doc_id] = dict(payload)
        return

    raise HTTPException(status_code=500, detail="Unable to persist push token record")


# ---------- models ----------

class PushRegisterIn(BaseModel):
    # from frontend: { uid, token, platform }
    # NOTE: we *ignore* uid by default and trust authenticated claims instead.
    uid: Optional[str] = Field(
        default=None,
        description="Ignored unless allow_uid_override=true AND caller is admin (debug only).",
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
    allow_uid_override: bool = Query(
        False,
        description="Debug only. If true and caller is admin, allow body.uid override.",
    ),
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
    claim_uid = claims.get("uid")
    if not claim_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing uid in auth claims",
        )

    uid = claim_uid
    if allow_uid_override and bool(claims.get("admin")) and body.uid:
        uid = str(body.uid).strip() or claim_uid

    token = (body.token or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="token is required",
        )

    platform = (body.platform or "").strip().lower() or "unknown"
    now = _now_utc()

    existing: Dict[str, Any] = _get_doc(COLL, uid)

    old_tokens: List[str] = list(existing.get("tokens") or [])
    tokens_set = {t.strip() for t in old_tokens if isinstance(t, str) and t.strip()}
    tokens_set.add(token)
    tokens = sorted(tokens_set)

    platforms_map: Dict[str, str] = dict(existing.get("platforms") or {})
    platforms_map[token] = platform

    payload: Dict[str, Any] = {
        "uid": uid,
        "tokens": tokens,
        "platforms": platforms_map,
        "updatedAt": now,
    }
    if not existing:
        payload["createdAt"] = now

    _set_doc(COLL, uid, payload, merge=True)

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

    data: Dict[str, Any] = _get_doc(COLL, uid)

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

    now = _now_utc()
    payload = {"uid": uid, "tokens": [], "platforms": {}, "updatedAt": now, "createdAt": now}
    _set_doc(COLL, uid, payload, merge=False)

    return PushRegisterOut(ok=True, uid=uid, tokens=[], updatedAt=now)
