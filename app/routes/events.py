# app/routes/events.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, ConfigDict, Field, constr, model_validator

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

def _attendee_stats(event_id: str, uid: str) -> Dict[str, Any]:
    """
    Scan event_attendees for this event.
    Returns: {"countGoing": int, "userStatus": Optional[str]}
    """
    coll = db.collection("event_attendees")
    count_going = 0
    user_status = None
    for rid, rec in _list_docs(coll):
        if not rec or rec.get("eventId") != event_id:
            continue
        status = rec.get("status")
        if status == "going":
            count_going += 1
        if rec.get("uid") == uid:
            user_status = status
    return {"countGoing": count_going, "userStatus": user_status}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

EventType = Literal["now", "future"]
Category  = Literal["neighborhood", "playdate", "help", "pet", "other"]

def _normalize_event_keys(v: Any) -> Any:
    """
    Accept common variants on incoming JSON:
      - startsAt -> startAt
      - endsAt   -> endAt
      - expireAt -> expiresAt
    """
    if isinstance(v, dict):
        if "startsAt" in v and "startAt" not in v:
            v["startAt"] = v.pop("startsAt")
        if "endsAt" in v and "endAt" not in v:
            v["endAt"] = v.pop("endsAt")
        if "expireAt" in v and "expiresAt" not in v:
            v["expiresAt"] = v.pop("expireAt")
    return v

class EventIn(BaseModel):
    """
    Input model. We accept a few alias spellings on input, and always serialize
    with canonical camelCase on output. Internally, we use snake_case.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: EventType
    title: constr(strip_whitespace=True, min_length=1)
    details: Optional[str] = None

    # Canonical names we serialize with:
    start_at: Optional[datetime]   = Field(None, validation_alias="startAt",   serialization_alias="startAt")
    end_at: Optional[datetime]     = Field(None, validation_alias="endAt",     serialization_alias="endAt")
    expires_at: Optional[datetime] = Field(None, validation_alias="expiresAt", serialization_alias="expiresAt")

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: List[str] = Field(default_factory=list)

    # category (optional on input; default set server-side to "other")
    category: Optional[Category] = Field(
        default=None,
        validation_alias="category",
        serialization_alias="category",
        description='One of: "neighborhood", "playdate", "help", "pet", "other"',
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_aliases(cls, v: Any) -> Any:
        return _normalize_event_keys(v)

class EventPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: Optional[constr(strip_whitespace=True, min_length=1)] = None
    details: Optional[str] = None

    start_at: Optional[datetime]   = Field(None, validation_alias="startAt",   serialization_alias="startAt")
    end_at: Optional[datetime]     = Field(None, validation_alias="endAt",     serialization_alias="endAt")
    expires_at: Optional[datetime] = Field(None, validation_alias="expiresAt", serialization_alias="expiresAt")

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: Optional[List[str]] = None

    category: Optional[Category] = Field(
        default=None,
        validation_alias="category",
        serialization_alias="category",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_aliases(cls, v: Any) -> Any:
        return _normalize_event_keys(v)

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
        "category": body.category or "other",
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
    # Time window; omitted = both
    type: Optional[str] = Query(None, pattern="^(now|future)$", description="Filter by time window"),
    neighborhood: Optional[str] = Query(None, description="Filter to a single neighborhood"),
    category: Optional[Category] = Query(None, description='Filter by category (neighborhood|playdate|help|pet|other)'),
    # Pagination
    limit: int = Query(20, ge=1, le=50),
    nextPageToken: Optional[str] = Query(None, description="Opaque cursor from previous page"),
    claims: dict = Depends(verify_token),
):
    """
    - Excludes expired events (expiresAt <= now)
    - Time-window logic (independent of stored `type` field):
        * type=now     -> startAt <= now < endAt|expiresAt
        * type=future  -> startAt > now
        * omitted      -> both of the above; still excludes past/expired
    - Sorted by startAt ascending (fallback: createdAt, then now)
    - Pagination via nextPageToken (URL-safe base64 of 'ISO_START|ID')
    - Enrich each item with attendeeCount and isAttending
    """
    import base64

    def _encode_token(start: datetime, eid: str) -> str:
        raw = f"{_aware(start).isoformat()}|{eid}".encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    def _decode_token(tok: str) -> Optional[tuple[datetime, str]]:
        try:
            raw = base64.urlsafe_b64decode(tok.encode("utf-8")).decode("utf-8")
            iso, eid = raw.split("|", 1)
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            return (datetime.fromisoformat(iso), eid)
        except Exception:
            return None

    now = _now()
    coll = db.collection("events")

    def _end_boundary(d: Dict[str, Any]) -> Optional[datetime]:
        """Prefer endAt; fall back to expiresAt; return aware or None."""
        end = d.get("endAt") or d.get("expiresAt")
        if isinstance(end, datetime):
            return _aware(end)
        return None

    # --- Pull + filter ------------------------------------------------------
    filtered: List[Dict[str, Any]] = []
    for eid, data in _list_docs(coll):
        if not data:
            continue

        # Exclude globally expired (explicit requirement)
        exp = data.get("expiresAt")
        if isinstance(exp, datetime) and _aware(exp) <= now:
            continue

        # Field filters
        if neighborhood and neighborhood not in (data.get("neighborhoods") or []):
            continue
        if category and data.get("category") != category:
            continue

        # Window logic
        start_raw = data.get("startAt")
        start_at = _aware(start_raw) if isinstance(start_raw, datetime) else None
        end_at = _end_boundary(data)

        is_now = bool(start_at and end_at and (start_at <= now < end_at))
        is_future = bool(start_at and (start_at > now))

        if type == "now" and not is_now:
            continue
        if type == "future" and not is_future:
            continue
        if type is None and not (is_now or is_future):
            continue

        item = dict(data)
        item["id"] = eid

        # Enrich with RSVP stats for the caller
        stats = _attendee_stats(eid, claims["uid"])
        item["attendeeCount"] = stats["countGoing"]
        item["isAttending"] = (stats["userStatus"] == "going")

        filtered.append(item)

    # --- Sort ---------------------------------------------------------------
    def _sort_key(d: Dict[str, Any]) -> datetime:
        sa = d.get("startAt")
        if isinstance(sa, datetime):
            return _aware(sa)
        ca = d.get("createdAt")
        if isinstance(ca, datetime):
            return _aware(ca)
        return now

    filtered.sort(key=_sort_key)

    # --- Apply cursor -------------------------------------------------------
    start_index = 0
    if nextPageToken:
        decoded = _decode_token(nextPageToken)
        if decoded:
            tok_start, tok_id = decoded
            for i, d in enumerate(filtered):
                d_start = d.get("startAt")
                d_id = d.get("id")
                d_key = (_aware(d_start) if isinstance(d_start, datetime) else now, d_id)
                tok_key = (_aware(tok_start), tok_id)
                if d_key > tok_key:
                    start_index = i
                    break
            else:
                return {"items": [], "nextPageToken": None}
        else:
            start_index = 0  # bad token ⇒ treat as first page

    page = filtered[start_index:start_index + limit]

    # --- Compute next token -------------------------------------------------
    next_token = None
    if start_index + limit < len(filtered):
        last = page[-1]
        last_start = last.get("startAt") or last.get("createdAt") or now
        if not isinstance(last_start, datetime):
            last_start = now
        next_token = _encode_token(last_start, last["id"])

    return {"items": _jsonify(page), "nextPageToken": next_token}

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

@router.patch("/events/{event_id}", summary="Edit an event (host-only)")
def patch_event(
    event_id: str,
    body: EventPatch,
    claims=Depends(verify_token),
):
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    current = snap.to_dict() or {}
    if current.get("hostUid") != claims["uid"] and not claims.get("admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # --- Compute effective values (overlay patch onto current) -------------
    def _as_dt(v):
        return _aware(v) if isinstance(v, datetime) else None

    effective_start = _as_dt(body.start_at) if body.start_at is not None else _as_dt(current.get("startAt"))
    effective_end   = _as_dt(body.end_at)   if body.end_at   is not None else _as_dt(current.get("endAt"))

    # --- Validations --------------------------------------------------------
    # capacity
    if body.capacity is not None and body.capacity < 1:
        raise HTTPException(status_code=422, detail="capacity must be ≥ 1")

    # category
    if body.category is not None:
        allowed = {"neighborhood", "playdate", "help", "pet", "other"}
        if body.category not in allowed:
            raise HTTPException(status_code=422, detail=f"category must be one of {sorted(allowed)}")

    # times
    if effective_start is not None and effective_end is not None:
        if effective_end <= effective_start:
            raise HTTPException(status_code=422, detail="endAt must be strictly greater than startAt")

    # --- Build update payload (always store UTC-aware datetimes) -----------
    updates: Dict[str, Any] = {}
    if body.title is not None:
        updates["title"] = body.title.strip()
    if body.details is not None:
        updates["details"] = body.details
    if body.start_at is not None:
        updates["startAt"] = _aware(body.start_at)
    if body.end_at is not None:
        updates["endAt"] = _aware(body.end_at)
    if body.expires_at is not None:
        updates["ExpiresAt"] = _aware(body.expires_at)  # tolerate capitalization slip, then remove
        updates["expiresAt"] = _aware(body.expires_at)
        updates.pop("ExpiresAt", None)
    if body.capacity is not None:
        updates["capacity"] = body.capacity
    if body.neighborhoods is not None:
        updates["neighborhoods"] = list(body.neighborhoods)
    if body.category is not None:
        updates["category"] = body.category

    if updates:
        updates["updatedAt"] = _now()
        ref.set(updates, merge=True)
        snap = ref.get()

    out = snap.to_dict() or {}
    out["id"] = snap.id
    return _jsonify(out)

@router.post("/events/{event_id}/rsvp", summary="RSVP to an event (going/maybe/declined)")
def rsvp_event(event_id: str, body: RSVPIn, claims=Depends(verify_token)):
    # ensure event exists
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    ev = ev_snap.to_dict() or {}

    uid = claims["uid"]
    now = _now()

    # Capacity applies to "going" only
    cap = ev.get("capacity")
    stats = _attendee_stats(event_id, uid)
    already_status = stats["userStatus"]

    if body.status == "going" and isinstance(cap, int) and cap >= 1:
        is_already_going = (already_status == "going")
        if not is_already_going and stats["countGoing"] >= cap:
            raise HTTPException(status_code=409, detail="Event is at capacity")

    # Upsert RSVP row
    rid = f"{event_id}_{uid}"
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

@router.delete("/events/{event_id}/rsvp", summary="Leave an event (remove RSVP)")
def leave_event(event_id: str, claims=Depends(verify_token)):
    # ensure event exists
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    uid = claims["uid"]
    rid = f"{event_id}_{uid}"
    coll = db.collection("event_attendees")
    ref = coll.document(rid)

    # Delete record if present
    if hasattr(ref, "delete"):
        ref.delete()
    elif hasattr(coll, "_docs"):
        coll._docs.pop(rid, None)

    return {"ok": True}

@router.delete("/events/{event_id}", summary="Delete an event (host or admin)")
def delete_event(event_id: str, claims = Depends(verify_token)):
    coll = db.collection("events")
    ref = coll.document(event_id)

    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    data = snap.to_dict() or {}
    host_uid = data.get("hostUid")
    is_owner = host_uid == claims["uid"]
    is_admin = bool(claims.get("admin"))
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Delete the event
    if hasattr(ref, "delete"):
        ref.delete()
    elif hasattr(coll, "_docs"):
        coll._docs.pop(event_id, None)

    # Cascade delete RSVPs for this event
    rsvp_coll = db.collection("event_attendees")
    for rid, rec in _list_docs(rsvp_coll):
        if (rec or {}).get("eventId") == event_id:
            dref = rsvp_coll.document(rid)
            if hasattr(dref, "delete"):
                dref.delete()
            elif hasattr(rsvp_coll, "_docs"):
                rsvp_coll._docs.pop(rid, None)

    return {"ok": True, "id": event_id}
