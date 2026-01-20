# app/routes/connections.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.connection import ConnectionRequest, ConnectionResponse

router = APIRouter(tags=["connections"])


# ---------------- helpers ----------------

def _aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC)"""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _now_iso() -> str:
    """Get current UTC timestamp as ISO string"""
    return datetime.now(timezone.utc).isoformat()


def _jsonify(x):
    """Convert datetime objects to ISO strings for JSON serialization"""
    if isinstance(x, datetime):
        return _aware(x).isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x


def _list_docs(coll):
    """List documents from Firestore collection (works with real and fake DB)"""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


def _get_user_household_id(uid: str) -> Optional[str]:
    """Get the household ID for a user from the users collection"""
    try:
        user_ref = db.collection("users").document(uid)
        if hasattr(user_ref, "get"):  # real Firestore
            user_doc = user_ref.get()
            if user_doc.exists:
                return user_doc.to_dict().get("householdId")
        elif hasattr(user_ref, "_doc"):  # dev fake
            return user_ref._doc.get("householdId")
    except Exception as e:
        print(f"Error getting household ID for user {uid}: {e}")
    return None


# ---------------- routes ----------------

@router.get("/api/connections", summary="List connections for current user's household")
def list_connections(
    status: Optional[str] = None,
    claims=Depends(verify_token),
) -> List[Dict[str, Any]]:
    """
    Returns all connections for the current user's household.
    
    - By default, returns all connections (pending, accepted, declined)
    - Filter by status: ?status=accepted (or pending, declined)
    - Returns household IDs that are connected to the user's household
    
    Response format:
    [
        {
            "id": "conn_123",
            "householdId": "household_456",  // The OTHER household ID
            "status": "accepted",
            "requestedAt": "2026-01-19T10:00:00Z",
            "respondedAt": "2026-01-19T12:00:00Z",
            "initiatedByMe": true  // Did I send the request?
        }
    ]
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's household ID
    household_id = _get_user_household_id(uid)
    if not household_id:
        raise HTTPException(
            status_code=400, 
            detail="User does not have a household. Complete onboarding first."
        )
    
    coll = db.collection("connections")
    connections: List[Dict[str, Any]] = []
    
    for conn_id, doc in _list_docs(coll):
        if not doc:
            continue
        
        from_hh = doc.get("from_household_id")
        to_hh = doc.get("to_household_id")
        conn_status = doc.get("status", "pending")
        
        # Filter by status if provided
        if status and conn_status != status:
            continue
        
        # Only include connections where this household is involved
        if household_id == from_hh:
            # I initiated this connection
            connections.append({
                "id": conn_id,
                "householdId": to_hh,
                "status": conn_status,
                "requestedAt": _jsonify(doc.get("requested_at")),
                "respondedAt": _jsonify(doc.get("responded_at")),
                "initiatedByMe": True,
                "createdAt": _jsonify(doc.get("created_at")),
                "updatedAt": _jsonify(doc.get("updated_at")),
            })
        elif household_id == to_hh:
            # I received this connection request
            connections.append({
                "id": conn_id,
                "householdId": from_hh,
                "status": conn_status,
                "requestedAt": _jsonify(doc.get("requested_at")),
                "respondedAt": _jsonify(doc.get("responded_at")),
                "initiatedByMe": False,
                "createdAt": _jsonify(doc.get("created_at")),
                "updatedAt": _jsonify(doc.get("updated_at")),
            })
    
    # Sort by most recent first
    connections.sort(
        key=lambda x: x.get("updatedAt") or x.get("createdAt") or "", 
        reverse=True
    )
    
    return connections


@router.post("/api/connections", summary="Send connection request")
def create_connection(
    request: ConnectionRequest = Body(...),
    claims=Depends(verify_token),
) -> Dict[str, Any]:
    """
    Send a connection request to another household.
    
    - Creates a pending connection between your household and the target household
    - Prevents duplicate connection requests
    - Returns the created connection
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's household ID
    from_household_id = _get_user_household_id(uid)
    if not from_household_id:
        raise HTTPException(
            status_code=400,
            detail="User does not have a household. Complete onboarding first."
        )
    
    to_household_id = request.household_id
    
    # Prevent connecting to yourself
    if from_household_id == to_household_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot connect to your own household"
        )
    
    # Verify target household exists
    target_ref = db.collection("households").document(to_household_id)
    if hasattr(target_ref, "get"):  # real Firestore
        target_doc = target_ref.get()
        if not target_doc.exists:
            raise HTTPException(status_code=404, detail="Target household not found")
    elif hasattr(target_ref, "_doc"):  # dev fake
        if not target_ref._doc:
            raise HTTPException(status_code=404, detail="Target household not found")
    
    # Check for existing connection (in either direction)
    coll = db.collection("connections")
    for conn_id, doc in _list_docs(coll):
        if not doc:
            continue
        
        from_hh = doc.get("from_household_id")
        to_hh = doc.get("to_household_id")
        
        # Check both directions
        if (from_hh == from_household_id and to_hh == to_household_id) or \
           (from_hh == to_household_id and to_hh == from_household_id):
            # Connection already exists
            return {
                "id": conn_id,
                "status": doc.get("status"),
                "message": f"Connection already exists with status: {doc.get('status')}",
                "existing": True
            }
    
    # Create new connection
    now = _now_iso()
    connection_data = {
        "from_household_id": from_household_id,
        "to_household_id": to_household_id,
        "status": "pending",
        "requested_at": now,
        "responded_at": None,
        "created_at": now,
        "updated_at": now,
    }
    
    # Add to Firestore
    new_conn_ref = coll.document()
    new_conn_ref.set(connection_data)
    conn_id = new_conn_ref.id
    
    return {
        "id": conn_id,
        "householdId": to_household_id,
        "status": "pending",
        "requestedAt": now,
        "createdAt": now,
        "message": "Connection request sent successfully"
    }


@router.patch("/api/connections/{connection_id}", summary="Accept or decline connection")
def update_connection(
    connection_id: str,
    response: ConnectionResponse = Body(...),
    claims=Depends(verify_token),
) -> Dict[str, Any]:
    """
    Accept or decline a connection request.
    
    - Only the recipient of the connection request can accept/decline
    - Updates the connection status and sets responded_at timestamp
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's household ID
    household_id = _get_user_household_id(uid)
    if not household_id:
        raise HTTPException(
            status_code=400,
            detail="User does not have a household. Complete onboarding first."
        )
    
    # Get connection document
    conn_ref = db.collection("connections").document(connection_id)
    
    if hasattr(conn_ref, "get"):  # real Firestore
        conn_doc = conn_ref.get()
        if not conn_doc.exists:
            raise HTTPException(status_code=404, detail="Connection not found")
        conn_data = conn_doc.to_dict()
    elif hasattr(conn_ref, "_doc"):  # dev fake
        conn_data = conn_ref._doc
        if not conn_data:
            raise HTTPException(status_code=404, detail="Connection not found")
    else:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verify user is the recipient of this connection request
    to_household_id = conn_data.get("to_household_id")
    if to_household_id != household_id:
        raise HTTPException(
            status_code=403,
            detail="You can only accept/decline connection requests sent to you"
        )
    
    # Update connection status
    now = _now_iso()
    updates = {
        "status": response.status,
        "responded_at": now,
        "updated_at": now,
    }
    
    conn_ref.update(updates) if hasattr(conn_ref, "update") else conn_ref.set({**conn_data, **updates})
    
    return {
        "id": connection_id,
        "status": response.status,
        "respondedAt": now,
        "message": f"Connection {response.status}"
    }


@router.delete("/api/connections/{connection_id}", summary="Remove connection")
def delete_connection(
    connection_id: str,
    claims=Depends(verify_token),
) -> Dict[str, Any]:
    """
    Remove a connection (disconnect from a household).
    
    - Either household in the connection can remove it
    - Deletes the connection document from Firestore
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get user's household ID
    household_id = _get_user_household_id(uid)
    if not household_id:
        raise HTTPException(
            status_code=400,
            detail="User does not have a household. Complete onboarding first."
        )
    
    # Get connection document
    conn_ref = db.collection("connections").document(connection_id)
    
    if hasattr(conn_ref, "get"):  # real Firestore
        conn_doc = conn_ref.get()
        if not conn_doc.exists:
            raise HTTPException(status_code=404, detail="Connection not found")
        conn_data = conn_doc.to_dict()
    elif hasattr(conn_ref, "_doc"):  # dev fake
        conn_data = conn_ref._doc
        if not conn_data:
            raise HTTPException(status_code=404, detail="Connection not found")
    else:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verify user is part of this connection
    from_hh = conn_data.get("from_household_id")
    to_hh = conn_data.get("to_household_id")
    
    if household_id not in [from_hh, to_hh]:
        raise HTTPException(
            status_code=403,
            detail="You can only remove your own connections"
        )
    
    # Delete the connection
    conn_ref.delete()
    
    return {
        "id": connection_id,
        "message": "Connection removed successfully",
        "deleted": True
    }
