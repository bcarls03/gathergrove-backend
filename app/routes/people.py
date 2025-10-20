# app/routes/people.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from app.main import verify_token
from app.core.firebase import db

router = APIRouter(tags=["people"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

def _normalize_household(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize field names so responses have stable keys expected by tests.
    Ensures: 'type', 'neighborhood', and builds 'childAges' from children.
    """
    out = dict(d)
    out["type"] = d.get("type") or d.get("householdType") or d.get("kind")
    out["neighborhood"] = d.get("neighborhood") or d.get("neighborhoodCode")

    # children could be a list of objects like {"age": 7, "sex": "M"}
    raw_children = d.get("children") or []
    child_ages: List[int] = []
    for kid in raw_children:
        if isinstance(kid, dict) and "age" in kid and isinstance(kid["age"], int):
            child_ages.append(kid["age"])
        elif isinstance(kid, int):
            child_ages.append(kid)
    out["childAges"] = child_ages

    return out

def _age_match_any(child_ages: List[int], min_age: Optional[int], max_age: Optional[int]) -> bool:
    if not child_ages:
        return False
    for age in child_ages:
        if min_age is not None and age < min_age:
            continue
        if max_age is not None and age > max_age:
            continue
        return True
    return False

# ---------------------------------------------------------------------------
# Route: GET /people
# ---------------------------------------------------------------------------

@router.get("/people", summary="People list (from households)")
def list_people(
    neighborhood: Optional[str] = Query(None, description="Filter to a single neighborhood"),
    type: Optional[str] = Query(None, description="Household type (e.g., family, emptyNest)"),
    age_min: Optional[int] = Query(None, alias="ageMin"),
    age_max: Optional[int] = Query(None, alias="ageMax"),
    page_token: Optional[str] = Query(None, alias="pageToken", description="Opaque id cursor"),
    page_size: int = Query(20, alias="pageSize", ge=1, le=50),
    claims=Depends(verify_token),
):
    # Load households
    docs = _list_docs(db.collection("households"))
    rows: List[Dict[str, Any]] = []
    for hid, data in docs:
        if not data:
            continue
        norm = _normalize_household(data)
        norm["id"] = hid

        # Filters
        if neighborhood and norm.get("neighborhood") != neighborhood:
            continue
        if type and norm.get("type") != type:
            continue
        if age_min is not None or age_max is not None:
            if not _age_match_any(norm["childAges"], age_min, age_max):
                continue

        rows.append(norm)

    # Sort for stable pagination (lastName then id)
    rows.sort(key=lambda x: ((x.get("lastName") or "").lower(), x.get("id")))

    # Cursor-based pagination (pageToken = last seen id)
    start_idx = 0
    if page_token:
        for i, it in enumerate(rows):
            if it["id"] == page_token:
                start_idx = i + 1
                break

    page = rows[start_idx:start_idx + page_size]
    next_token = page[-1]["id"] if (start_idx + page_size) < len(rows) else None

    # Minimal fields required by tests/clients
    items = [
        {
            "id": it["id"],
            "type": it.get("type"),
            "neighborhood": it.get("neighborhood"),
            "childAges": it.get("childAges", []),
        }
        for it in page
    ]

    return {"items": items, "nextPageToken": next_token}
