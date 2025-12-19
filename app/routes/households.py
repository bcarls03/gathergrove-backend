# app/routes/households.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.firebase import db
from app.deps.auth import verify_token  # dev/prod auth (avoid circular import)

router = APIRouter(tags=["households"])


# ---------------- helpers ----------------

def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonify(x):
    if isinstance(x, datetime):
        return _aware(x).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x


def _list_docs(coll):
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


# ---------------- routes ----------------

@router.get("/households", summary="List households (filterable)")
def list_households(
    neighborhood: Optional[str] = Query(None, description="Neighborhood name"),
    # ✅ TESTS call: /households?type=singleCouple
    hh_type: Optional[str] = Query(
        None,
        alias="type",
        description="Filter household by legacy 'type' (family/emptyNest/singleCouple).",
    ),
    # ✅ Keep backward-compat for any clients using household_type=
    household_type: Optional[str] = Query(
        None,
        description="Backward-compatible alias for type; also matches newer 'householdType'.",
    ),
    claims=Depends(verify_token),
):
    """
    Returns household docs stored in Firestore collection 'households'.

    Notes:
    - Older docs may use field 'type' (family/emptyNest/singleCouple).
    - Newer docs / frontend may use field 'householdType' (e.g., 'Family w/ Kids' or similar).
    Filtering supports both, but tests specifically require ?type=...
    """
    coll = db.collection("households")
    items: List[Dict[str, Any]] = []

    wanted_type = hh_type or household_type

    for hid, doc in _list_docs(coll):
        if not doc:
            continue

        doc_neighborhood = doc.get("neighborhood")
        doc_type = doc.get("type")
        doc_household_type = doc.get("householdType")

        if neighborhood and doc_neighborhood != neighborhood:
            continue

        if wanted_type:
            if (doc_type != wanted_type) and (doc_household_type != wanted_type):
                continue

        row: Dict[str, Any] = dict(doc)
        row["id"] = hid

        # Ensure adultNames always present as a list
        adult_names = row.get("adultNames")
        if adult_names is None:
            row["adultNames"] = []
        elif not isinstance(adult_names, list):
            row["adultNames"] = [str(adult_names)]
        else:
            row["adultNames"] = [str(n) for n in adult_names]

        # Normalize Kids -> kids if someone posted wrong casing
        if "Kids" in row and "kids" not in row:
            row["kids"] = row.pop("Kids")

        items.append(row)

    items.sort(
        key=lambda d: (
            str(d.get("lastName") or "").lower(),
            str(d.get("id") or ""),
        )
    )
    return _jsonify(items)


@router.post("/households", summary="Create/update my household (by uid)")
def upsert_my_household(
    payload: Dict[str, Any] = Body(...),
    claims=Depends(verify_token),
):
    """
    Create/update the household for the currently-auth'd user.
    We key the household document by UID so Chrome + Safari become different households.

    Frontend expects saving to work via POST /households.
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing uid in auth claims")

    # Normalize Kids -> kids if payload came in wrong casing
    if "Kids" in payload and "kids" not in payload:
        payload["kids"] = payload.pop("Kids")

    # Always stamp uid/email from auth
    payload["uid"] = uid
    payload["email"] = claims.get("email")

    doc_ref = db.collection("households").document(uid)

    # Preserve createdAt if doc already exists
    existing = doc_ref.get().to_dict() or {}
    created_at = existing.get("createdAt") or payload.get("createdAt") or _now_iso()

    payload["createdAt"] = created_at
    payload["updatedAt"] = _now_iso()

    doc_ref.set(payload, merge=True)

    saved = doc_ref.get().to_dict() or {}
    saved["id"] = uid
    return _jsonify(saved)
