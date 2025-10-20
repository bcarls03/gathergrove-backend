# app/routes/households.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.firebase import db
from app.main import verify_token  # dev/prod auth

router = APIRouter(tags=["households"])

HouseholdType = Literal["family", "emptyNest", "singleCouple"]

def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def _jsonify(x):
    if isinstance(x, datetime): return _aware(x).isoformat()
    if isinstance(x, list):     return [_jsonify(v) for v in x]
    if isinstance(x, dict):     return {k: _jsonify(v) for k,v in x.items()}
    return x

def _list_docs(coll):
    if hasattr(coll, "stream"):     # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):      # dev fake
        return list(coll._docs.items())
    return []

@router.get("/households", summary="List households (filterable)")
def list_households(
    neighborhood: Optional[str] = Query(None, description="Neighborhood name"),
    type: Optional[HouseholdType] = Query(None, description='family | emptyNest | singleCouple'),
    claims = Depends(verify_token),
):
    coll = db.collection("households")
    items: List[Dict[str, Any]] = []
    for hid, doc in _list_docs(coll):
        if not doc: continue
        if neighborhood and doc.get("neighborhood") != neighborhood:
            continue
        if type and doc.get("type") != type:
            continue
        row = dict(doc)
        row["id"] = hid
        items.append(row)

    # stable-ish sort
    def _key(d): return (str(d.get("lastName") or "").lower(), d["id"])
    items.sort(key=_key)
    return _jsonify(items)
