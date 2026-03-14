"""Event reply models for Happening Now conversations."""

from pydantic import BaseModel, Field
from datetime import datetime


class EventReplyCreate(BaseModel):
    """Request body for creating an event reply."""
    body: str = Field(min_length=1, max_length=500)


class EventReplyOut(BaseModel):
    """Event reply response model."""
    id: str
    event_id: str
    household_id: str
    author_label: str  # e.g., "Smith Family", "Johnson Household"
    body: str
    created_at: datetime
    
    class Config:
        from_attributes = True
