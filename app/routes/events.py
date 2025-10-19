# app/routes/events.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, ConfigDict, Field, constr, AliasChoices

from app.core.firebase import db
from app.main import verify_token  # reuse dev/prod auth from main.py

router = APIRouter(tags=["events"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aware(dt: datetime) -> datetime:
    """Return a UTC-aware datetime (assumes naive = UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _jsonify(x):
    """Recursively convert datetimes to ISO strings for JSON responses."""
    if isinstance(x, datetime):
        return _aware(x).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x

def _list_docs(coll):
    """
    Works with real Firestore (stream) and our in-memory fake (._docs).
    Returns list[(id, dict)].
    """
    if hasattr(coll, "stream"):
        return [(doc.id, doc.to_dict() or {}) for doc in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake path
        return list(coll._docs.items())
    return []

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

EventType = Literal["now", "future"]

class EventIn(BaseModel):
    """
    Input model. Accept camelCase variants on input, emit canonical camelCase
    on output, while using snake_case in Python code.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: EventType
    title: constr(strip_whitespace=True, min_length=1)
    details: Optional[str] = None

    # Accept either startAt OR startsAt on input, serialize as startAt
    start_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("startAt", "startsAt"),
        serialization_alias="startAt",
    )
    # Accept endAt OR endsAt, serialize as endAt
    end_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("endAt", "endsAt"),
        serialization_alias="endAt",
    )
    # Accept expiresAt OR expireAt, serialize as expiresAt
    expires_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("expiresAt", "expireAt"),
        serialization_alias="expiresAt",
    )

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: List[str] = Field(default_factory=list)

class EventPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: Optional[constr(strip_whitespace=True, min_length=1)] = None
    details: Optional[str] = None

    start_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("startAt", "startsAt"),
        serialization_alias="startAt",
    )
    end_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("endAt", "endsAt"),
        serialization_alias="endAt",
    )
    expires_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("expiresAt", "expireAt"),
        serialization_alias="expiresAt",
    )

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: Optional[List[str]] = None

class RSVPIn(BaseModel):
    status: Literal["going", "maybe", "declined"]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/events", summary="Create an event (host = current user)")
def create_event(body: EventIn, claims=Depends(verify_token)):
    now = _now()

    # --- Time rules (explicit & defensive) ---
    if body.type == "now":
        # start_at defaults to now for "now" events
        start_at = _aware(body.start_at or now)
        # expires_at defaults to +24h if not provided
        expires_at = _aware(body.expires_at) if body.expires_at else (start_at + timedelta(hours=24))
    else:  # body.type == "future"
        if body.start_at is None:
            raise HTTPException(status_code=400, detail="startAt is required for future events")
        start_at = _aware(body.start_at)
        # future events don't require expires_at
        expires_at = _aware(body.expires_at) if body.expires_at else None

    payload: Dict[str, Any] = {
        "type": body.type,
        "title": body.title.strip(),
        "details": body.details,
        # store camelCase in Firestore / JSON
        "startAt": start_at,
        "endAt": _aware(body.end_at) if body.end_at else None,
        "expiresAt": expires_at,
        "capacity": body.capacity,
        "neighborhoods": list(body.neighborhoods or []),
        "hostUid": claims["uid"],
        "createdAt": now,
        "updatedAt": now,
    }

    event_id = uuid.uuid4().hex
    ref = db.collection("events").document(event_id)
    ref.set(payload, merge=False)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)

@router.get("/events", summary="List upcoming and happening-now events")
def list_events(
    neighborhood: Optional[str] = Query(None, description="Filter to a single neighborhood"),
    type: Optional[EventType] = Query(None, description='Filter by "now" or "future"'),
    claims=Depends(verify_token),
):
    now = _now()
    coll = db.collection("events")
    items = []
    for eid, data in _list_docs(coll):
        if not data:
            continue

        # filters
        if neighborhood and neighborhood not in (data.get("neighborhoods") or []):
            continue
        if type and data.get("type") != type:
            continue

        ev_type = data.get("type")
        start_at: Optional[datetime] = data.get("startAt")
        expires_at: Optional[datetime] = data.get("expiresAt")

        keep = False
        if ev_type == "now":
            keep = bool(expires_at and _aware(expires_at) >= now)
        else:  # "future"
            keep = bool(start_at and _aware(start_at) >= now)

        if keep:
            item = dict(data)
            item["id"] = eid
            items.append(item)

    # Sort roughly by when it happens (fallback to createdAt/now)
    def _key(d):
        return _aware(d.get("startAt") or d.get("createdAt") or now)

    items.sort(key=_key)
    return _jsonify(items)

@router.get("/events/{event_id}", summary="Get an event by ID")
def get_event(
    event_id: str = Path(..., description="Event document id"),
    claims=Depends(verify_token),
):
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)

@router.post("/events/{event_id}/rsvp", summary="RSVP to an event (going/maybe/declined)")
def rsvp_event(event_id: str, body: RSVPIn, claims=Depends(verify_token)):
    # ensure event exists
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    uid = claims["uid"]
    rid = f"{event_id}_{uid}"
    now = _now()

    payload = {
        "eventId": event_id,
        "uid": uid,
        "status": body.status,
        "rsvpAt": now,
    }

    ref = db.collection("event_attendees").document(rid)
    ref.set(payload, merge=True)

    doc = ref.get()
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return _jsonify(data)
