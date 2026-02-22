# app/routes/events.py
from __future__ import annotations

import base64
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field, constr, model_validator

from app.core.firebase import db
from app.deps.auth import verify_token  # ✅ avoid circular import

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


def _today() -> date:
    return _now().date()


def _parse_dt(v: Any) -> Optional[datetime]:
    """
    Accept datetime OR ISO string timestamps (dev fake often stores strings).
    Returns UTC-aware datetime or None.
    """
    if v is None:
        return None
    if isinstance(v, datetime):
        return _aware(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            # handle trailing "Z"
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            return _aware(dt)
        except Exception:
            return None
    return None


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


def _get_doc_by_id(coll_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Try Firestore document(doc_id).get() first; fallback to scanning (dev fake).
    Returns dict with "id" populated if found, else None.
    """
    coll = db.collection(coll_name)

    # real Firestore
    try:
        snap = coll.document(doc_id).get()
        if snap and getattr(snap, "exists", False):
            data = snap.to_dict() or {}
            data["id"] = snap.id
            return data
    except Exception:
        pass

    # dev fake scan
    for _id, rec in _list_docs(coll):
        if _id == doc_id:
            out = dict(rec or {})
            out["id"] = _id
            return out

    return None


def _lookup_household(uid: str) -> Dict[str, Any]:
    """
    ✅ IMPORTANT:
    Your people records may live in `households` (preferred) and sometimes `users` (legacy).
    Try households first, then users. Works in Firestore + dev fake.
    """
    # 1) households doc id == uid
    hh = _get_doc_by_id("households", uid)
    if hh:
        return hh

    # 2) users doc id == uid (legacy)
    usr = _get_doc_by_id("users", uid)
    if usr:
        return usr

    # 3) Scan households for matching uid field (dev/legacy)
    for _id, rec in _list_docs(db.collection("households")):
        if (rec or {}).get("uid") == uid:
            out = dict(rec or {})
            out.setdefault("id", _id)
            return out

    # 4) Scan users for matching uid field (dev/legacy)
    for _id, rec in _list_docs(db.collection("users")):
        if (rec or {}).get("uid") == uid:
            out = dict(rec or {})
            out.setdefault("id", _id)
            return out

    return {}


def _normalize_neighborhood(household: Dict[str, Any]) -> Optional[str]:
    """
    Try multiple likely keys; handle list values; return a single display string.
    """
    neighborhood = (
        household.get("neighborhood")
        or household.get("neighborhoodName")
        or household.get("neighborhood_name")
        or household.get("neighborhoodId")
        or household.get("neighborhood_id")
        or household.get("neighborhood_code")
        or household.get("neighborhoodCode")
    )

    # Sometimes neighborhood is stored as an array like ["Bayhill", "Eagles Pointe"]
    if isinstance(neighborhood, list):
        neighborhood = neighborhood[0] if neighborhood else None

    # Sometimes the only thing available is neighborhoods[] (plural)
    if neighborhood is None:
        nlist = household.get("neighborhoods")
        if isinstance(nlist, list) and nlist:
            neighborhood = str(nlist[0])

    if neighborhood is None:
        return None

    try:
        s = str(neighborhood).strip()
        return s or None
    except Exception:
        return None


def _attendee_stats(event_id: str, uid: str) -> Dict[str, Any]:
    """
    Scan event_attendees for this event.
    Returns: { countGoing, countDeclined, userStatus }
    """
    coll = db.collection("event_attendees")
    count_going = 0
    count_declined = 0
    user_status = None

    for _rid, rec in _list_docs(coll):
        if not rec:
            continue
        ev_key = rec.get("eventId") or rec.get("event_id")
        if ev_key != event_id:
            continue

        status = str(rec.get("status") or "").strip().lower()
        if status == "going":
            count_going += 1
        if status in ("declined", "cant"):
            count_declined += 1
        if rec.get("uid") == uid:
            user_status = status

    return {
        "countGoing": count_going,
        "countDeclined": count_declined,
        "userStatus": user_status,
    }


def _rsvp_summary(event_id: str, uid: str) -> Dict[str, Any]:
    """
    RSVP summary: counts + current user status.
    We store "declined" internally but surface as "cant".
    """
    coll = db.collection("event_attendees")
    counts_raw = {"going": 0, "maybe": 0, "declined": 0}
    user_status: Optional[str] = None

    for _rid, rec in _list_docs(coll):
        if not rec:
            continue
        ev_key = rec.get("eventId") or rec.get("event_id")
        if ev_key != event_id:
            continue

        status = str(rec.get("status") or "").strip().lower()
        if status in counts_raw:
            counts_raw[status] += 1
        if rec.get("uid") == uid:
            user_status = status

    return {
        "eventId": event_id,
        "counts": {
            "going": counts_raw["going"],
            "maybe": counts_raw["maybe"],
            "cant": counts_raw["declined"],
        },
        "userStatus": user_status,
    }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

EventType = Literal["now", "future"]
# ✅ UPDATED: Added 3 new categories (food, celebrations, sports) - now 8 total
Category = Literal["neighborhood", "playdate", "help", "pet", "food", "celebrations", "sports", "other"]

def _normalize_event_keys(v: Any) -> Any:
    if isinstance(v, dict):
        if "startsAt" in v and "startAt" not in v:
            v["startAt"] = v.pop("startsAt")
        if "endsAt" in v and "endAt" not in v:
            v["endAt"] = v.pop("endsAt")
        if "expireAt" in v and "expiresAt" not in v:
            v["expiresAt"] = v.pop("expireAt")
    return v


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: EventType
    title: constr(strip_whitespace=True, min_length=1)
    details: Optional[str] = None
    location: Optional[str] = None  # ✅ NEW: Event location field

    start_at: Optional[datetime] = Field(
        None, validation_alias="startAt", serialization_alias="startAt"
    )
    end_at: Optional[datetime] = Field(
        None, validation_alias="endAt", serialization_alias="endAt"
    )
    expires_at: Optional[datetime] = Field(
        None, validation_alias="expiresAt", serialization_alias="expiresAt"
    )

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: List[str] = Field(default_factory=list)

    category: Optional[Category] = Field(
        default=None,
        validation_alias="category",
        serialization_alias="category",
        description='One of: "neighborhood", "playdate", "help", "pet", "food", "celebrations", "sports", "other"',
    )
    
    # ✅ NEW: Visibility for viral loop (default: None, will be set to "private" in create)
    visibility: Optional[Literal["private", "link_only", "public"]] = Field(
        default=None,
        description="Who can see this event? private=host only, link_only=anyone with link, public=discovery"
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_aliases(cls, v: Any) -> Any:
        return _normalize_event_keys(v)


class EventPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: Optional[constr(strip_whitespace=True, min_length=1)] = None
    details: Optional[str] = None
    location: Optional[str] = None  # ✅ NEW: Can update event location

    start_at: Optional[datetime] = Field(
        None, validation_alias="startAt", serialization_alias="startAt"
    )
    end_at: Optional[datetime] = Field(
        None, validation_alias="endAt", serialization_alias="endAt"
    )
    expires_at: Optional[datetime] = Field(
        None, validation_alias="expiresAt", serialization_alias="expiresAt"
    )

    capacity: Optional[int] = Field(None, ge=1)
    neighborhoods: Optional[List[str]] = None
    category: Optional[Category] = Field(
        default=None, validation_alias="category", serialization_alias="category"
    )
    
    # ✅ NEW: Can update visibility
    visibility: Optional[Literal["private", "link_only", "public"]] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_aliases(cls, v: Any) -> Any:
        return _normalize_event_keys(v)


class RSVPIn(BaseModel):
    status: Literal["going", "maybe", "declined"]


class GuestRSVPIn(BaseModel):
    """Guest RSVP (no authentication required)"""
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    choice: Literal["going", "maybe", "cant"]


class EventRsvpHousehold(BaseModel):
    uid: str
    household_id: str
    last_name: Optional[str] = None
    neighborhood: Optional[str] = None
    household_type: Optional[str] = None
    child_ages: List[int] = []
    child_sexes: List[Optional[str]] = []
    # Guest fields
    is_guest: bool = False
    guest_name: Optional[str] = None
    guest_phone: Optional[str] = None


class EventRsvpBuckets(BaseModel):
    going: List[EventRsvpHousehold] = []
    maybe: List[EventRsvpHousehold] = []
    cant: List[EventRsvpHousehold] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/events", summary="Create an event (host = current user)")
def create_event(body: EventIn, claims=Depends(verify_token)):
    now = _now()

    # ✅ IMPORTANT FIX:
    # For "now" events we DO NOT set endAt to startAt (which would make the event instantly disappear).
    if body.type == "now":
        start_at = _aware(body.start_at or now)
        expires_at = (
            _aware(body.expires_at)
            if body.expires_at
            else start_at + timedelta(hours=24)
        )
        end_at = None
    else:
        if body.start_at is None:
            raise HTTPException(
                status_code=400,
                detail="startAt is required for future events",
            )
        start_at = _aware(body.start_at)
        expires_at = _aware(body.expires_at) if body.expires_at else None
        end_at = _aware(body.end_at) if body.end_at else None

    # Generate shareable link for link_only or public events
    event_id = uuid.uuid4().hex
    # ✅ SECURITY: Default to "private" if not specified (secure by default)
    visibility = body.visibility if body.visibility is not None else "private"
    shareable_link = None
    if visibility in ('link_only', 'public'):
        # Use full UUID for cryptographic security (128 bits entropy)
        # Format: /e/{32-char-hex} - unguessable and collision-resistant
        shareable_link = f"/e/{event_id}"

    payload: Dict[str, Any] = {
        "type": body.type,
        "title": body.title.strip(),
        "details": body.details,
        "location": body.location,  # ✅ NEW: Event location
        "startAt": start_at,
        "endAt": end_at,  # ✅ uses computed end_at
        "expiresAt": expires_at,
        "capacity": body.capacity,
        "neighborhoods": list(body.neighborhoods or []),
        "category": body.category or "other",
        "host_user_id": claims["uid"],  # ✅ Changed from hostUid to host_user_id (individual)
        "visibility": visibility,  # ✅ NEW: private/link_only/public
        "shareable_link": shareable_link,  # ✅ NEW: short link for viral loop
        "status": "active",  # ✅ default
        "createdAt": now,
        "updatedAt": now,
    }

    ref = db.collection("events").document(event_id)
    ref.set(payload, merge=False)

    snap = ref.get()
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)


@router.get("/events", summary="List upcoming and happening-now events")
def list_events(
    type: Optional[str] = Query(None, pattern="^(now|future)$"),
    neighborhood: Optional[str] = Query(None),
    category: Optional[Category] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    nextPageToken: Optional[str] = Query(None),
    claims: dict = Depends(verify_token),
):
    def _encode_token(start: datetime, eid: str) -> str:
        raw = f"{_aware(start).isoformat()}|{eid}".encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    def _decode_token(tok: str) -> Optional[Tuple[datetime, str]]:
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
        # “now” events rely on expiresAt; future events may have endAt or expiresAt.
        return _parse_dt(d.get("endAt") or d.get("expiresAt"))

    filtered: List[Dict[str, Any]] = []
    for eid, data in _list_docs(coll):
        if not data:
            continue

        # ✅ Skip canceled events (soft-cancel) — accept both spellings
        st = str(data.get("status") or "active").strip().lower()
        if st in ("canceled", "cancelled"):
            continue

        # ✅ Expiration check: supports datetime OR ISO string
        exp = _parse_dt(data.get("expiresAt"))
        if exp is not None and exp <= now:
            continue

        if neighborhood and neighborhood not in (data.get("neighborhoods") or []):
            continue
        if category and data.get("category") != category:
            continue

        start_at = _parse_dt(data.get("startAt"))
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

        stats = _attendee_stats(eid, claims["uid"])
        item["attendeeCount"] = stats["countGoing"]
        item["isAttending"] = stats["userStatus"] == "going"
        item["attendeeCounts"] = {
            "going": stats["countGoing"],
            "cant": stats["countDeclined"],
        }

        filtered.append(item)

    def _sort_key(d: Dict[str, Any]) -> datetime:
        sa = _parse_dt(d.get("startAt"))
        if sa is not None:
            return sa
        ca = _parse_dt(d.get("createdAt"))
        if ca is not None:
            return ca
        return now

    filtered.sort(key=_sort_key)

    start_index = 0
    if nextPageToken:
        decoded = _decode_token(nextPageToken)
        if decoded:
            tok_start, tok_id = decoded
            tok_key = (_aware(tok_start), tok_id)

            for i, d in enumerate(filtered):
                d_key = (_sort_key(d), str(d.get("id") or ""))
                if d_key > tok_key:
                    start_index = i
                    break
            else:
                return {"items": [], "nextPageToken": None}

    page = filtered[start_index : start_index + limit]

    next_token = None
    if start_index + limit < len(filtered):
        last = page[-1]
        last_start = (
            _parse_dt(last.get("startAt")) or _parse_dt(last.get("createdAt")) or now
        )
        next_token = _encode_token(last_start, last["id"])

    return {"items": _jsonify(page), "nextPageToken": next_token}


@router.get("/events/{event_id}", summary="Get an event by ID")
def get_event(event_id: str = Path(...), claims=Depends(verify_token)):
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)


@router.get("/events/public/{event_id}", summary="Get public/link_only event (no auth)")
def get_public_event(event_id: str = Path(...)):
    """
    Public endpoint for viral loop: allows anyone to view link_only or public events.
    Returns 404 for private events or non-existent events (privacy protection).
    Returns snake_case keys and SAFE fields only (no host_user_id, neighborhoods).
    """
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    data = snap.to_dict() or {}
    visibility = data.get("visibility", "private")
    
    # Only allow public or link_only events to be viewed
    if visibility not in ("public", "link_only"):
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Return safe fields only in snake_case
    safe_data = {
        "id": snap.id,
        "type": data.get("type"),
        "title": data.get("title"),
        "details": data.get("details"),
        "location": data.get("location"),
        "visibility": visibility,
        "category": data.get("category"),
        "capacity": data.get("capacity"),
        "status": data.get("status"),
    }
    
    # Normalize timestamp fields to snake_case
    if "startAt" in data:
        safe_data["start_at"] = data["startAt"]
    if "endAt" in data:
        safe_data["end_at"] = data["endAt"]
    if "expiresAt" in data:
        safe_data["expires_at"] = data["expiresAt"]
    if "createdAt" in data:
        safe_data["created_at"] = data["createdAt"]
    
    return _jsonify(safe_data)


@router.patch("/events/{event_id}", summary="Edit an event (host-only)")
def patch_event(event_id: str, body: EventPatch, claims=Depends(verify_token)):
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    current = snap.to_dict() or {}
    
    # ✅ EXPLICIT HOST FIELD PRECEDENCE (prevents partial-migration edge cases)
    # Priority: 1) host_user_id (new individual-first) → 2) hostUid (legacy) → 3) reject
    host_uid = current.get("host_user_id")
    if not host_uid:
        host_uid = current.get("hostUid")  # Backward compatibility fallback
    if not host_uid:
        raise HTTPException(status_code=500, detail="Event missing host identifier")
    
    if host_uid != claims["uid"] and not claims.get("admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    updates: Dict[str, Any] = {}

    if body.title is not None:
        updates["title"] = body.title.strip()
    if body.details is not None:
        updates["details"] = body.details
    if body.start_at is not None:
        updates["startAt"] = _aware(body.start_at)
    if body.end_at is not None:
        updates["endAt"] = _aware(body.end_at)
    
    # ✅ VALIDATION: Ensure endAt > startAt (422 if violated)
    # Compute final startAt and endAt after patches
    final_start_at = updates.get("startAt") or current.get("startAt")
    final_end_at = updates.get("endAt") or current.get("endAt")
    if final_end_at is not None and final_start_at is not None:
        # Both are aware datetimes at this point
        if final_end_at <= final_start_at:
            raise HTTPException(
                status_code=422,
                detail="endAt must be strictly greater than startAt"
            )
    
    if body.expires_at is not None:
        updates["expiresAt"] = _aware(body.expires_at)
    if body.capacity is not None:
        updates["capacity"] = body.capacity
    if body.neighborhoods is not None:
        updates["neighborhoods"] = list(body.neighborhoods)
    if body.category is not None:
        updates["category"] = body.category
    
    # ✅ NEW: Support visibility updates
    if body.visibility is not None:
        updates["visibility"] = body.visibility
        # Regenerate shareable_link if changing to link_only or public
        if body.visibility in ('link_only', 'public'):
            if not current.get("shareable_link"):
                updates["shareable_link"] = f"/e/{event_id}"
        elif body.visibility == 'private':
            updates["shareable_link"] = None

    if updates:
        updates["updatedAt"] = _now()
        ref.set(updates, merge=True)

    snap = ref.get()
    out = snap.to_dict() or {}
    out["id"] = snap.id
    return _jsonify(out)


# ✅ Soft-cancel an event (host-only)
@router.patch(
    "/events/{event_id}/cancel",
    summary="Cancel an event (host-only, soft cancel)",
)
def cancel_event(event_id: str, claims=Depends(verify_token)):
    ref = db.collection("events").document(event_id)
    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    current = snap.to_dict() or {}
    
    # ✅ EXPLICIT HOST FIELD PRECEDENCE (prevents partial-migration edge cases)
    # Priority: 1) host_user_id (new individual-first) → 2) hostUid (legacy) → 3) reject
    host_uid = current.get("host_user_id")
    if not host_uid:
        host_uid = current.get("hostUid")  # Backward compatibility fallback
    if not host_uid:
        raise HTTPException(status_code=500, detail="Event missing host identifier")
    
    if host_uid != claims["uid"] and not claims.get("admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    now = _now()
    updates: Dict[str, Any] = {
        "status": "canceled",
        "canceledAt": now,
        "canceledBy": claims["uid"],
        "updatedAt": now,
    }

    ref.set(updates, merge=True)

    snap2 = ref.get()
    out = snap2.to_dict() or {}
    out["id"] = snap2.id
    return _jsonify(out)


@router.get("/events/{event_id}/rsvp", summary="Get RSVP summary for current user")
def get_my_rsvp(event_id: str, claims=Depends(verify_token)):
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    return _jsonify(_rsvp_summary(event_id, claims["uid"]))


@router.post("/events/{event_id}/rsvp", summary="RSVP to an event (going/maybe/declined)")
def rsvp_event(event_id: str, body: RSVPIn, claims=Depends(verify_token)):
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    ev = ev_snap.to_dict() or {}

    # ✅ Don't allow RSVPs on canceled events
    st = str(ev.get("status") or "active").strip().lower()
    if st in ("canceled", "cancelled"):
        raise HTTPException(status_code=409, detail="Event is canceled")

    uid = claims["uid"]
    now = _now()

    # Capacity applies to "going" only
    cap = ev.get("capacity")
    stats = _attendee_stats(event_id, uid)
    already_status = stats["userStatus"]

    if body.status == "going" and isinstance(cap, int) and cap >= 1:
        is_already_going = already_status == "going"
        if not is_already_going and stats["countGoing"] >= cap:
            raise HTTPException(status_code=409, detail="Event is at capacity")

    rid = f"{event_id}_{uid}"
    payload = {"eventId": event_id, "uid": uid, "status": body.status, "rsvpAt": now}
    ref = db.collection("event_attendees").document(rid)
    ref.set(payload, merge=True)

    snap = ref.get()
    data = snap.to_dict() or {}
    data["id"] = snap.id
    return _jsonify(data)


@router.delete("/events/{event_id}/rsvp", summary="Leave an event (remove RSVP)")
def leave_event(event_id: str, claims=Depends(verify_token)):
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    uid = claims["uid"]
    rid = f"{event_id}_{uid}"
    coll = db.collection("event_attendees")
    ref = coll.document(rid)

    if hasattr(ref, "delete"):
        ref.delete()
    elif hasattr(coll, "_docs"):
        coll._docs.pop(rid, None)

    return {"ok": True}


@router.post("/events/{event_id}/rsvp/guest", summary="Guest RSVP (no auth required)")
def guest_rsvp_event(event_id: str, body: GuestRSVPIn):
    """
    **PUBLIC ENDPOINT** - No authentication required.
    
    Allows anyone with the event link to RSVP as a guest.
    Stores guest name and optional phone number.
    """
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    ev = ev_snap.to_dict() or {}

    # Don't allow RSVPs on canceled events
    st = str(ev.get("status") or "active").strip().lower()
    if st in ("canceled", "cancelled"):
        raise HTTPException(status_code=409, detail="Event is canceled")

    now = _now()
    
    # Check capacity for "going" status
    cap = ev.get("capacity")
    if body.choice == "going" and isinstance(cap, int) and cap >= 1:
        stats = _attendee_stats(event_id, "")  # Pass empty uid for guest
        if stats["countGoing"] >= cap:
            raise HTTPException(status_code=409, detail="Event is at capacity")

    # Generate unique guest ID
    guest_id = str(uuid.uuid4())
    rid = f"{event_id}_guest_{guest_id}"
    
    payload = {
        "eventId": event_id,
        "guest_id": guest_id,
        "guest_name": body.name.strip(),
        "guest_phone": body.phone.strip() if body.phone else None,
        "status": body.choice,
        "rsvpAt": now,
        "is_guest": True,  # Flag to identify guest RSVPs
    }
    
    ref = db.collection("event_attendees").document(rid)
    ref.set(payload, merge=True)

    return {
        "success": True,
        "rsvp_id": rid,
        "guest_id": guest_id,
        "message": "RSVP received! Thank you."
    }


@router.get(
    "/events/{event_id}/rsvps",
    summary="Get RSVP buckets (going/maybe/can't go) with household info",
    response_model=EventRsvpBuckets,
)
def get_event_rsvps(event_id: str, claims=Depends(verify_token)):
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    ev = ev_snap.to_dict() or {}
    st = str(ev.get("status") or "active").strip().lower()
    if st in ("canceled", "cancelled"):
        return EventRsvpBuckets(going=[], maybe=[], cant=[])

    coll = db.collection("event_attendees")
    buckets: Dict[str, List[EventRsvpHousehold]] = {"going": [], "maybe": [], "cant": []}
    today = _today()

    for rid, rec in _list_docs(coll):
        if not rec:
            continue
        ev_key = rec.get("eventId") or rec.get("event_id")
        if ev_key != event_id:
            continue

        # Check if this is a guest RSVP
        is_guest = rec.get("is_guest", False)
        
        if is_guest:
            # Handle guest RSVP
            guest_name = rec.get("guest_name", "Guest")
            guest_phone = rec.get("guest_phone")
            guest_id = rec.get("guest_id", rid)
            
            status_raw = str(rec.get("status") or "").strip().lower()
            if status_raw not in ("going", "maybe", "cant"):
                status_raw = "going"
            bucket_key = status_raw
            
            buckets[bucket_key].append(
                EventRsvpHousehold(
                    uid=f"guest_{guest_id}",
                    household_id=f"guest_{guest_id}",
                    is_guest=True,
                    guest_name=guest_name,
                    guest_phone=guest_phone,
                )
            )
            continue

        # Handle authenticated user RSVP
        raw_uid = rec.get("uid")
        uid_str = str(raw_uid) if raw_uid is not None else f"anon-{rid}"

        status_raw = str(rec.get("status") or "").strip().lower()
        if status_raw not in ("going", "maybe", "declined"):
            status_raw = "going"

        bucket_key = "cant" if status_raw == "declined" else status_raw

        household = _lookup_household(uid_str) if raw_uid else {}

        last_name = (
            household.get("displayLastName")
            or household.get("display_last_name")
            or household.get("display_lastName")
            or household.get("lastName")
            or household.get("last_name")
            or None
        )

        household_type = (
            household.get("householdType")
            or household.get("type")
            or household.get("household_type")
            or None
        )

        neighborhood = _normalize_neighborhood(household)

        child_ages: List[int] = []
        child_sexes: List[Optional[str]] = []

        kids = household.get("kids") or []
        if isinstance(kids, list):
            for kid in kids:
                if not isinstance(kid, dict):
                    continue
                by = kid.get("birthYear") or kid.get("birth_year")
                bm = kid.get("birthMonth") or kid.get("birth_month") or 1
                sex_raw = kid.get("sex") or kid.get("gender")
                try:
                    by = int(by)
                    bm = int(bm)
                    dob = date(by, bm, 1)
                except Exception:
                    continue

                age = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day)
                )
                if age >= 0:
                    child_ages.append(age)
                    if isinstance(sex_raw, str) and sex_raw:
                        s = sex_raw.strip().upper()
                        if s.startswith("M"):
                            child_sexes.append("M")
                        elif s.startswith("F"):
                            child_sexes.append("F")
                        else:
                            child_sexes.append(s[:1])
                    else:
                        child_sexes.append(None)

        household_id = household.get("id") or household.get("household_id") or uid_str

        buckets[bucket_key].append(
            EventRsvpHousehold(
                uid=uid_str,
                household_id=str(household_id),
                last_name=last_name,
                neighborhood=neighborhood,
                household_type=household_type,
                child_ages=child_ages,
                child_sexes=child_sexes,
            )
        )

    return EventRsvpBuckets(
        going=buckets["going"], maybe=buckets["maybe"], cant=buckets["cant"]
    )


@router.get(
    "/events/{event_id}/attendees",
    summary="List attendees (optional filter) with household info",
)
def list_event_attendees(
    event_id: str,
    status: Optional[str] = Query(None, pattern="^(going|maybe|declined)$"),
    claims=Depends(verify_token),
):
    ev_ref = db.collection("events").document(event_id)
    ev_snap = ev_ref.get()
    if not ev_snap or not ev_snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    coll = db.collection("event_attendees")
    items: List[Dict[str, Any]] = []

    for rid, rec in _list_docs(coll):
        if not rec:
            continue
        ev_key = rec.get("eventId") or rec.get("event_id")
        if ev_key != event_id:
            continue
        if status and rec.get("status") != status:
            continue

        uid = rec.get("uid")
        household = _lookup_household(str(uid)) if uid else {}

        last_name = (
            household.get("displayLastName")
            or household.get("display_last_name")
            or household.get("lastName")
            or household.get("last_name")
            or None
        )

        items.append(
            {
                "id": rid,
                "uid": uid,
                "status": rec.get("status"),
                "householdLastName": last_name,
                "neighborhood": _normalize_neighborhood(household),
                "householdType": household.get("householdType")
                or household.get("household_type"),
                "kids": household.get("kids") or [],
            }
        )

    return _jsonify({"items": items})


@router.delete("/events/{event_id}", summary="Delete an event (host or admin)")
def delete_event(event_id: str, claims=Depends(verify_token)):
    coll = db.collection("events")
    ref = coll.document(event_id)

    snap = ref.get()
    if not snap or not snap.exists:
        raise HTTPException(status_code=404, detail="Event not found")

    data = snap.to_dict() or {}
    
    # ✅ EXPLICIT HOST FIELD PRECEDENCE (prevents partial-migration edge cases)
    # Priority: 1) host_user_id (new individual-first) → 2) hostUid (legacy) → 3) reject
    host_uid = data.get("host_user_id")
    if not host_uid:
        host_uid = data.get("hostUid")  # Backward compatibility fallback
    if not host_uid:
        raise HTTPException(status_code=500, detail="Event missing host identifier")
    
    if not (host_uid == claims["uid"] or bool(claims.get("admin"))):
        raise HTTPException(status_code=403, detail="Forbidden")

    if hasattr(ref, "delete"):
        ref.delete()
    elif hasattr(coll, "_docs"):
        coll._docs.pop(event_id, None)

    # Cascade delete RSVPs for this event
    rsvp_coll = db.collection("event_attendees")
    for rid, rec in _list_docs(rsvp_coll):
        if (rec or {}).get("eventId") == event_id or (rec or {}).get("event_id") == event_id:
            dref = rsvp_coll.document(rid)
            if hasattr(dref, "delete"):
                dref.delete()
            elif hasattr(rsvp_coll, "_docs"):
                rsvp_coll._docs.pop(rid, None)

    return {"ok": True, "id": event_id}
