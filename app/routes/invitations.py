# app/routes/invitations.py
"""
Event invitations API.

Supports:
- Creating invitations (platform and off-platform)
- Smart routing: households → in-app, phone numbers → SMS (unless already registered)
- Public RSVP page for anonymous guests
- RSVP submission without account creation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from app.models.invitation import (
    InvitationCreate,
    EventInvitation,
    InvitationListOut,
    RSVPSubmit,
    PublicEventView
)
from app.deps.auth import verify_token
from app.core.firebase import db
from app.services.sms import sms_service
from app.services.user_service import find_household_by_phone
from app.utils.tokens import generate_rsvp_token

router = APIRouter(prefix="/events", tags=["invitations"])


def _now_iso() -> str:
    """Get current timestamp as ISO string"""
    return datetime.now(timezone.utc).isoformat()


def _format_event_time(dt: datetime) -> str:
    """Format datetime for SMS (e.g., 'Sat, Jan 25 at 3:00 PM')"""
    return dt.strftime("%a, %b %d at %I:%M %p")


@router.post("/{event_id}/invitations", status_code=status.HTTP_201_CREATED)
async def create_invitations(
    event_id: str,
    invitation_data: InvitationCreate,
    claims=Depends(verify_token)
):
    """
    Create invitations for an event.
    
    **Smart routing:**
    - `household_ids` → in-app notifications (even if they have phone on file)
    - `phone_numbers` → SMS ONLY if not already registered
    - If phone number belongs to existing user → send in-app instead
    
    This prevents duplicate notifications and respects user preferences.
    """
    current_user_id = claims.get("uid")
    
    # Verify event exists and user is the host
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event_data = event_doc.to_dict()
    
    # Check if current user is the host
    if event_data.get("host_user_id") != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event host can send invitations"
        )
    
    invitations_created = []
    sms_sent_count = 0
    
    # 1. Handle platform invites (household_ids)
    for household_id in invitation_data.household_ids:
        invitation_id = f"inv_{event_id}_{household_id}"
        
        invitation = {
            "id": invitation_id,
            "event_id": event_id,
            "invitee_type": "household",
            "invitee_id": household_id,
            "phone_number": None,
            "invited_by": current_user_id,
            "status": "pending",
            "rsvp_token": None,
            "guest_name": None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "sms_sent_at": None,
            "sms_delivered_at": None,
            "sms_failed_at": None
        }
        
        # Save to Firestore
        db.collection("invitations").document(invitation_id).set(invitation)
        invitations_created.append(invitation)
        
        # TODO: Send in-app notification
        # await notification_service.send_event_invite(household_id, event_id)
    
    # 2. Handle off-platform invites (phone numbers)
    for phone_number in invitation_data.phone_numbers:
        # Check if phone is already registered
        existing_household_id = await find_household_by_phone(phone_number)
        
        if existing_household_id:
            # Phone belongs to existing user - route to in-app
            invitation_id = f"inv_{event_id}_{existing_household_id}"
            
            invitation = {
                "id": invitation_id,
                "event_id": event_id,
                "invitee_type": "household",
                "invitee_id": existing_household_id,
                "phone_number": None,  # Don't store phone for privacy
                "invited_by": current_user_id,
                "status": "pending",
                "rsvp_token": None,
                "guest_name": None,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "sms_sent_at": None,
                "sms_delivered_at": None,
                "sms_failed_at": None
            }
            
            db.collection("invitations").document(invitation_id).set(invitation)
            invitations_created.append(invitation)
            
            # TODO: Send in-app notification
            # await notification_service.send_event_invite(existing_household_id, event_id)
            
        else:
            # New user - send SMS
            rsvp_token = generate_rsvp_token()
            invitation_id = f"inv_{event_id}_{rsvp_token}"
            
            invitation = {
                "id": invitation_id,
                "event_id": event_id,
                "invitee_type": "phone_number",
                "invitee_id": None,
                "phone_number": phone_number,
                "invited_by": current_user_id,
                "status": "pending",
                "rsvp_token": rsvp_token,
                "guest_name": None,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "sms_sent_at": None,
                "sms_delivered_at": None,
                "sms_failed_at": None
            }
            
            # Get host name for SMS
            host_household = db.collection("households").document(current_user_id).get()
            host_name = "A neighbor"
            if host_household.exists:
                host_data = host_household.to_dict()
                host_name = host_data.get("lastName", "A neighbor")
                if not host_name.startswith("The "):
                    host_name = f"The {host_name} Family"
            
            # Build RSVP link
            rsvp_link = f"https://gathergrove.com/rsvp/{rsvp_token}"
            
            # Send SMS
            success, message_sid = sms_service.send_event_invitation(
                to_number=phone_number,
                event_title=event_data.get("title", "Event"),
                host_name=host_name,
                event_datetime=_format_event_time(event_data.get("start")),
                rsvp_link=rsvp_link
            )
            
            if success:
                invitation["sms_sent_at"] = _now_iso()
                sms_sent_count += 1
            else:
                invitation["sms_failed_at"] = _now_iso()
            
            db.collection("invitations").document(invitation_id).set(invitation)
            invitations_created.append(invitation)
    
    return {
        "success": True,
        "invitations_created": len(invitations_created),
        "platform_invites": len(invitation_data.household_ids),
        "sms_invites": sms_sent_count,
        "message": f"✅ {len(invitations_created)} invitations sent"
    }


@router.get("/{event_id}/invitations")
async def get_event_invitations(
    event_id: str,
    claims=Depends(verify_token)
) -> InvitationListOut:
    """
    Get all invitations for an event (host only).
    
    Returns both platform and off-platform RSVPs with counts.
    """
    current_user_id = claims.get("uid")
    
    # Verify event exists and user is the host
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event_data = event_doc.to_dict()
    
    if event_data.get("host_user_id") != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event host can view invitations"
        )
    
    # Get all invitations for this event
    invitations_ref = db.collection("invitations")
    
    # Handle fake vs real Firestore
    if hasattr(invitations_ref, "_docs"):
        # Fake Firestore
        all_invitations = [
            EventInvitation(**inv) 
            for inv in invitations_ref._docs.values() 
            if inv.get("event_id") == event_id
        ]
    else:
        # Real Firestore
        query = invitations_ref.where("event_id", "==", event_id)
        all_invitations = [
            EventInvitation(**doc.to_dict()) 
            for doc in query.stream()
        ]
    
    # Calculate counts
    platform_count = sum(1 for inv in all_invitations if inv.invitee_type == "household")
    off_platform_count = sum(1 for inv in all_invitations if inv.invitee_type == "phone_number")
    
    # RSVP summary
    rsvp_summary = {
        "accepted": sum(1 for inv in all_invitations if inv.status == "accepted"),
        "declined": sum(1 for inv in all_invitations if inv.status == "declined"),
        "maybe": sum(1 for inv in all_invitations if inv.status == "maybe"),
        "pending": sum(1 for inv in all_invitations if inv.status == "pending")
    }
    
    return InvitationListOut(
        invitations=all_invitations,
        total_count=len(all_invitations),
        platform_count=platform_count,
        off_platform_count=off_platform_count,
        rsvp_summary=rsvp_summary
    )


@router.get("/rsvp/{rsvp_token}")
async def get_event_by_token(rsvp_token: str) -> PublicEventView:
    """
    **PUBLIC ENDPOINT** - No auth required.
    
    Get event details for anonymous RSVP page.
    Returns sanitized event info (no sensitive data).
    """
    # Find invitation by token
    invitations_ref = db.collection("invitations")
    
    # Handle fake vs real Firestore
    invitation = None
    if hasattr(invitations_ref, "_docs"):
        # Fake Firestore
        for inv_data in invitations_ref._docs.values():
            if inv_data.get("rsvp_token") == rsvp_token:
                invitation = inv_data
                break
    else:
        # Real Firestore
        query = invitations_ref.where("rsvp_token", "==", rsvp_token).limit(1)
        results = list(query.stream())
        if results:
            invitation = results[0].to_dict()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid RSVP link"
        )
    
    # Get event details
    event_id = invitation["event_id"]
    event_ref = db.collection("events").document(event_id)
    event_doc = event_ref.get()
    
    if not event_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event_data = event_doc.to_dict()
    
    # Get host name
    host_id = invitation["invited_by"]
    host_household = db.collection("households").document(host_id).get()
    host_name = "A neighbor"
    if host_household.exists:
        host_data = host_household.to_dict()
        last_name = host_data.get("lastName", "")
        adult_names = host_data.get("adultNames", [])
        if last_name:
            host_name = f"The {last_name} Family"
        elif adult_names:
            host_name = adult_names[0]
    
    # Calculate spots remaining (if capacity set)
    spots_remaining = None
    if event_data.get("capacity"):
        accepted_count = sum(
            1 for inv in invitations_ref._docs.values()
            if inv.get("event_id") == event_id and inv.get("status") == "accepted"
        ) if hasattr(invitations_ref, "_docs") else len(list(
            invitations_ref.where("event_id", "==", event_id).where("status", "==", "accepted").stream()
        ))
        spots_remaining = max(0, event_data["capacity"] - accepted_count)
    
    return PublicEventView(
        id=event_id,
        title=event_data.get("title", "Event"),
        details=event_data.get("details"),
        start=event_data["start"],
        end=event_data.get("end"),
        location=event_data.get("neighborhood"),  # Use neighborhood as location
        host_name=host_name,
        category=event_data.get("category", "other"),
        capacity=event_data.get("capacity"),
        spots_remaining=spots_remaining
    )


@router.post("/rsvp/{rsvp_token}")
async def submit_rsvp(
    rsvp_token: str,
    rsvp_data: RSVPSubmit
):
    """
    **PUBLIC ENDPOINT** - No auth required.
    
    Submit RSVP for an off-platform guest.
    Updates invitation status and optionally captures guest name.
    """
    # Find invitation by token
    invitations_ref = db.collection("invitations")
    
    invitation_doc_id = None
    invitation = None
    
    if hasattr(invitations_ref, "_docs"):
        # Fake Firestore
        for doc_id, inv_data in invitations_ref._docs.items():
            if inv_data.get("rsvp_token") == rsvp_token:
                invitation_doc_id = doc_id
                invitation = inv_data
                break
    else:
        # Real Firestore
        query = invitations_ref.where("rsvp_token", "==", rsvp_token).limit(1)
        results = list(query.stream())
        if results:
            doc = results[0]
            invitation_doc_id = doc.id
            invitation = doc.to_dict()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid RSVP link"
        )
    
    # Update invitation
    update_data = {
        "status": rsvp_data.status,
        "updated_at": _now_iso()
    }
    
    if rsvp_data.guest_name:
        update_data["guest_name"] = rsvp_data.guest_name
    
    db.collection("invitations").document(invitation_doc_id).update(update_data)
    
    return {
        "success": True,
        "status": rsvp_data.status,
        "message": "RSVP received! Thank you."
    }
