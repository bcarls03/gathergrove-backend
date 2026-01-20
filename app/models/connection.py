"""
Connection model - Household-to-household connections.

Connections represent mutual consent between households to communicate
and see each other's activity. They follow the "earned trust" principle:
- Either household can initiate a connection request
- The other household must accept before connection is established
- Either household can remove the connection at any time
"""

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


ConnectionStatus = Literal["pending", "accepted", "declined"]


class Connection(BaseModel):
    """
    Connection between two households.
    
    Connections are bidirectional - when accepted, both households
    can see each other in their "Connected" tab and can message.
    """
    id: Optional[str] = Field(
        None,
        description="Unique connection ID (Firestore doc ID)"
    )
    from_household_id: str = Field(
        ...,
        description="Household that initiated the connection request"
    )
    to_household_id: str = Field(
        ...,
        description="Household that received the connection request"
    )
    status: ConnectionStatus = Field(
        default="pending",
        description="Connection status: pending (awaiting acceptance), accepted, or declined"
    )
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the connection was requested (UTC)"
    )
    responded_at: Optional[datetime] = Field(
        None,
        description="When the connection was accepted/declined (UTC)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Created timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last updated timestamp (UTC)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "conn_abc123",
                "from_household_id": "household_123",
                "to_household_id": "household_456",
                "status": "accepted",
                "requested_at": "2026-01-19T10:00:00Z",
                "responded_at": "2026-01-19T12:00:00Z",
                "created_at": "2026-01-19T10:00:00Z",
                "updated_at": "2026-01-19T12:00:00Z"
            }
        }


class ConnectionRequest(BaseModel):
    """Request body for creating a new connection"""
    household_id: str = Field(
        ...,
        description="ID of the household to connect with"
    )


class ConnectionResponse(BaseModel):
    """Response body for connection actions"""
    status: ConnectionStatus = Field(
        ...,
        description="New status of the connection"
    )
