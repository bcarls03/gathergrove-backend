# app/models/invitation.py
"""
Models for event invitations (platform and off-platform).

Supports:
- In-app invitations to households on GatherGrove
- SMS invitations to phone numbers not yet on platform
- Anonymous RSVP tracking via tokens
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


InviteeType = Literal["household", "phone_number"]
InvitationStatus = Literal["pending", "accepted", "declined", "maybe"]


class InvitationCreate(BaseModel):
    """Request to create invitations for an event"""
    household_ids: list[str] = Field(
        default_factory=list,
        description="List of household IDs to invite (platform users)"
    )
    phone_numbers: list[str] = Field(
        default_factory=list,
        description="List of E.164 phone numbers to invite (off-platform)"
    )


class EventInvitation(BaseModel):
    """
    A single invitation to an event.
    Can be either platform (household_id) or off-platform (phone_number).
    """
    id: str
    event_id: str
    
    # Invitee identification (mutually exclusive)
    invitee_type: InviteeType
    invitee_id: Optional[str] = Field(
        None,
        description="Household ID if invitee_type='household'"
    )
    phone_number: Optional[str] = Field(
        None,
        description="E.164 phone number if invitee_type='phone_number'"
    )
    
    # Invitation metadata
    invited_by: str = Field(..., description="Household ID of event host")
    status: InvitationStatus = "pending"
    
    # For off-platform guests
    rsvp_token: Optional[str] = Field(
        None,
        description="Unique token for anonymous RSVP (off-platform only)"
    )
    guest_name: Optional[str] = Field(
        None,
        description="Optional name provided by off-platform guest"
    )
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Delivery tracking (for SMS)
    sms_sent_at: Optional[datetime] = None
    sms_delivered_at: Optional[datetime] = None
    sms_failed_at: Optional[datetime] = None


class InvitationListOut(BaseModel):
    """Response for listing invitations to an event"""
    invitations: list[EventInvitation]
    total_count: int
    platform_count: int
    off_platform_count: int
    rsvp_summary: dict[str, int] = Field(
        description="Count by status: {accepted: X, declined: Y, maybe: Z, pending: W}"
    )


class RSVPSubmit(BaseModel):
    """Public RSVP submission (no auth required)"""
    status: InvitationStatus = Field(..., description="accepted | declined | maybe")
    guest_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional name for off-platform guest"
    )


class PublicEventView(BaseModel):
    """Sanitized event details for public RSVP page (no auth required)"""
    id: str
    title: str
    details: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None
    location: Optional[str] = None
    host_name: str = Field(..., description="Display name of host (e.g., 'The Miller Family')")
    category: str
    
    # Capacity info (if set)
    capacity: Optional[int] = None
    spots_remaining: Optional[int] = None
