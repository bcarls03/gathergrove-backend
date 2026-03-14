"""Event replies routes - Happening Now conversation threads."""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
import uuid

from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.reply import EventReplyCreate, EventReplyOut

router = APIRouter(tags=["replies"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/events/{event_id}/replies", response_model=EventReplyOut)
async def create_event_reply(
    event_id: str,
    payload: EventReplyCreate,
    claims: dict = Depends(verify_token)
):
    """
    Create a reply to a Happening Now event.
    
    - Validates user has a household
    - Validates event exists
    - Creates reply in event_replies collection
    """
    uid = claims["uid"]
    
    # Get user's household
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_doc.to_dict()
    household_id = user_data.get("household_id")
    if not household_id:
        raise HTTPException(status_code=400, detail="User has no household")
    
    # Get household for author label
    household_doc = db.collection("households").document(household_id).get()
    if not household_doc.exists:
        raise HTTPException(status_code=404, detail="Household not found")
    
    household_data = household_doc.to_dict()
    last_name = household_data.get("last_name", "")
    household_type = household_data.get("household_type", "")
    
    # Create author label (e.g., "Smith Family")
    author_label = f"{last_name} "
    if household_type == "family_with_kids":
        author_label += "Family"
    elif household_type == "empty_nesters":
        author_label += "Household"
    elif household_type == "singles_couples":
        author_label += "Household"
    else:
        author_label += "Household"
    author_label = author_label.strip()
    
    # Verify event exists
    event_doc = db.collection("events").document(event_id).get()
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create reply document
    reply_id = str(uuid.uuid4())
    created_at = _now()
    
    reply_data = {
        "id": reply_id,
        "event_id": event_id,
        "household_id": household_id,
        "author_label": author_label,
        "body": payload.body.strip(),
        "created_at": created_at,
    }
    
    db.collection("event_replies").document(reply_id).set(reply_data)
    
    return EventReplyOut(**reply_data)


@router.get("/events/{event_id}/replies", response_model=List[EventReplyOut])
async def get_event_replies(
    event_id: str,
    claims: dict = Depends(verify_token)
):
    """
    Get all replies for a Happening Now event.
    
    Returns replies sorted by created_at ascending (oldest first).
    """
    # Verify event exists
    event_doc = db.collection("events").document(event_id).get()
    if not event_doc.exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Fetch replies for this event
    replies_query = (
        db.collection("event_replies")
        .where("event_id", "==", event_id)
        .order_by("created_at")
        .stream()
    )
    
    replies = []
    for doc in replies_query:
        data = doc.to_dict()
        replies.append(EventReplyOut(**data))
    
    return replies
