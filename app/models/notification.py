# app/models/notification.py
from typing import Dict, Any
from pydantic import BaseModel, Field


class NotificationType:
    """Notification type constants"""
    EVENT_INVITE = "event_invite"
    RSVP = "rsvp"
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    EVENT_REPLY = "event_reply"


class NotificationCreate(BaseModel):
    """Request model for creating a notification"""
    user_id: str
    type: str  # One of NotificationType constants
    title: str
    body: str
    data: Dict[str, Any] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    """Response model for a notification"""
    id: str
    user_id: str
    type: str
    title: str
    body: str
    data: Dict[str, Any]
    read: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "notif_123",
                "user_id": "user_456",
                "type": "event_invite",
                "title": "Sarah invited you to a BBQ",
                "body": "Saturday at 3pm",
                "data": {"event_id": "evt_789"},
                "read": False,
                "created_at": "2026-03-11T10:00:00Z"
            }
        }


class NotificationListResponse(BaseModel):
    """Response model for list of notifications"""
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Response model for unread count"""
    count: int
