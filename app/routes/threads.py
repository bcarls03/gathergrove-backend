# app/routes/threads.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.thread import ThreadCreateRequest, ThreadResponse, ThreadListResponse

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_user_household_id(uid: str) -> str:
    """Get household ID for a user, checking both householdId and household_id fields"""
    users_ref = db.collection("users")
    
    # Try real Firestore
    if hasattr(users_ref, "stream"):
        for doc in users_ref.stream():
            data = doc.to_dict() or {}
            if data.get("uid") == uid:
                hh_id = data.get("householdId") or data.get("household_id")
                if not hh_id:
                    raise HTTPException(status_code=400, detail="User does not have a household")
                return hh_id
    # Try fake Firestore
    elif hasattr(users_ref, "_docs"):
        for doc_id, data in users_ref._docs.items():
            if data.get("uid") == uid:
                hh_id = data.get("householdId") or data.get("household_id")
                if not hh_id:
                    raise HTTPException(status_code=400, detail="User does not have a household")
                return hh_id
    
    raise HTTPException(status_code=404, detail="User not found")


def _list_docs(coll):
    """List documents from Firestore collection (works with real and fake DB)"""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


def _thread_id_for(hh1: str, hh2: str) -> str:
    """Generate deterministic thread ID from two household IDs"""
    sorted_ids = sorted([hh1, hh2])
    return f"thread_{sorted_ids[0]}_{sorted_ids[1]}"


def _are_households_connected(hh1: str, hh2: str) -> bool:
    """
    Check if two households are mutually connected.
    Returns True only if there exists an accepted connection between them.
    """
    coll = db.collection("connections")
    
    for conn_id, doc in _list_docs(coll):
        if not doc:
            continue
        
        from_hh = doc.get("from_household_id")
        to_hh = doc.get("to_household_id")
        
        # Check if this connection involves both households (either direction)
        is_match = (
            (from_hh == hh1 and to_hh == hh2) or
            (from_hh == hh2 and to_hh == hh1)
        )
        
        if not is_match:
            continue
        
        # Found connection - check if it's accepted
        conn_status = doc.get("status", "pending")
        if conn_status == "accepted":
            return True
    
    return False


@router.post("", response_model=ThreadResponse)
def create_or_get_thread(
    body: ThreadCreateRequest,
    claims=Depends(verify_token)
):
    """
    Get or create a thread between the current user's household and target household.
    Returns existing thread if one exists between these households.
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing uid in token")
    
    my_household_id = _get_user_household_id(uid)
    target_household_id = body.household_id
    
    if my_household_id == target_household_id:
        raise HTTPException(status_code=400, detail="Cannot create thread with yourself")
    
    # BLOCKER 1 FIX: Verify households are mutually connected
    if not _are_households_connected(my_household_id, target_household_id):
        raise HTTPException(
            status_code=403,
            detail="Cannot create thread: households must be mutually connected"
        )
    
    # Generate deterministic thread ID
    thread_id = _thread_id_for(my_household_id, target_household_id)
    
    threads_ref = db.collection("threads")
    
    # Check if thread exists
    if hasattr(threads_ref, "document"):  # Firestore
        doc_ref = threads_ref.document(thread_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            return ThreadResponse(
                threadId=thread_id,
                participants=data.get("participants", []),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", "")
            )
    elif hasattr(threads_ref, "_docs"):  # Fake Firestore
        if thread_id in threads_ref._docs:
            data = threads_ref._docs[thread_id]
            return ThreadResponse(
                threadId=thread_id,
                participants=data.get("participants", []),
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", "")
            )
    
    # Create new thread
    now = _now_iso()
    thread_data = {
        "participants": [my_household_id, target_household_id],
        "created_at": now,
        "updated_at": now
    }
    
    if hasattr(threads_ref, "document"):  # Real Firestore
        threads_ref.document(thread_id).set(thread_data)
    elif hasattr(threads_ref, "_docs"):  # Fake Firestore
        threads_ref._docs[thread_id] = thread_data
    
    return ThreadResponse(
        threadId=thread_id,
        participants=thread_data["participants"],
        created_at=now,
        updated_at=now
    )


@router.get("", response_model=ThreadListResponse)
def list_my_threads(claims=Depends(verify_token)):
    """
    List all threads where the current user's household is a participant.
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing uid in token")
    
    my_household_id = _get_user_household_id(uid)
    
    threads_ref = db.collection("threads")
    all_threads = _list_docs(threads_ref)
    
    my_threads = []
    for thread_id, data in all_threads:
        participants = data.get("participants", [])
        if my_household_id in participants:
            my_threads.append(ThreadResponse(
                threadId=thread_id,
                participants=participants,
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", "")
            ))
    
    return ThreadListResponse(threads=my_threads)
