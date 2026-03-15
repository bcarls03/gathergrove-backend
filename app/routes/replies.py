"""Event replies routes - Happening Now conversation threads."""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List
import uuid

from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.reply import EventReplyCreate, EventReplyOut
from app.services import notification_service
from app.models.notification import NotificationType

router = APIRouter(tags=["replies"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _list_docs(coll):
    """List documents from Firestore collection (works with real and fake DB)"""
    if hasattr(coll, "stream"):
        return [(doc.id, doc.to_dict() or {}) for doc in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake path
        return list(coll._docs.items())
    return []


def _get_household_name_from_uid(uid: str) -> str:
    """Get display name for a household by looking up the user's household."""
    try:
        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            return "A neighbor"
        
        user_data = user_doc.to_dict()
        household_id = user_data.get("household_id")
        if not household_id:
            return "A neighbor"
        
        household_doc = db.collection("households").document(household_id).get()
        if not household_doc.exists:
            return "A neighbor"
        
        household_data = household_doc.to_dict()
        name = household_data.get("name") or household_data.get("last_name")
        if name:
            return str(name)
    except Exception:
        pass
    return "A neighbor"


def _get_household_name_from_household_id(household_id: str) -> str:
    """Get display name for a household by household ID (same pattern as invitations/connections)."""
    try:
        household_doc = db.collection("households").document(household_id).get()
        if not household_doc.exists:
            return "A neighbor"
        
        household_data = household_doc.to_dict()
        name = household_data.get("name") or household_data.get("last_name")
        if name:
            return str(name)
    except Exception:
        pass
    return "A neighbor"


async def _send_reply_notifications(event_id: str, event_data: dict, sender_uid: str, sender_household_id: str):
    """
    Send event reply notifications to:
    - Event host (unless they are the sender)
    - Participants who RSVP'd "going" or "maybe" (unless they are the sender or declined)
    """
    # Get event title for notification body
    event_title = event_data.get("title", "an event")
    
    # Get sender's household name (same pattern as invitations/connections/RSVPs)
    sender_name = _get_household_name_from_household_id(sender_household_id)
    
    # Get host UID
    host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
    
    # Collect recipient UIDs
    recipient_uids = set()
    
    # Add host (unless sender)
    if host_uid and host_uid != sender_uid:
        recipient_uids.add(host_uid)
    
    # Get all RSVPs for this event from event_attendees collection
    attendees_coll = db.collection("event_attendees")
    for _rid, attendee_data in _list_docs(attendees_coll):
        if not attendee_data:
            continue
        
        # Check if this RSVP is for our event
        ev_id = attendee_data.get("eventId") or attendee_data.get("event_id")
        if ev_id != event_id:
            continue
        
        attendee_uid = attendee_data.get("uid")
        if not attendee_uid or attendee_uid == sender_uid:
            continue  # Skip sender
        
        # Only notify "going" and "maybe" participants (exclude declined)
        status = str(attendee_data.get("status", "")).strip().lower()
        if status in ["going", "maybe"]:
            recipient_uids.add(attendee_uid)
    
    # Send notifications to all recipients
    for recipient_uid in recipient_uids:
        try:
            await notification_service.create_and_send(
                user_id=recipient_uid,
                notification_type=NotificationType.EVENT_REPLY,
                title="Event update",
                body=f"{sender_name} sent a message in {event_title}",
                data={
                    "event_id": event_id,
                    "sender_uid": sender_uid,
                }
            )
        except Exception as e:
            # Log error but continue sending to other recipients
            print(f"Failed to send reply notification to {recipient_uid}: {e}")


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
    
    # Send notifications to relevant participants (async, don't fail reply if notifications fail)
    try:
        await _send_reply_notifications(event_id, event_doc.to_dict(), uid, household_id)
    except Exception as e:
        # Log error but don't fail reply creation
        print(f"Failed to send reply notifications for event {event_id}: {e}")
    
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
