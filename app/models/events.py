# === add/imports ===
from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# UPDATE: Add 3 new categories (food, celebrations, sports) - now 8 total
Category = Literal[
    "neighborhood",   # 🏡 Block parties, cul-de-sac hangs
    "playdate",       # 🎪 Kids playdates, park meetups
    "help",           # 🤝 Borrow tools, rides, babysitting
    "pet",            # 🐶 Dog walks, pet sitting
    "food",           # 🍕 NEW - Dinners, potlucks, restaurants
    "celebrations",   # 🎉 NEW - Birthdays, holidays, milestones
    "sports",         # ⚾ NEW - Pickup games, fitness, hikes
    "other"           # ✨ Anything else
]

EventVisibility = Literal["private", "link_only", "public"]

# === update your Pydantic models ===
class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    details: Optional[str] = Field(default=None, max_length=2000)
    start: datetime
    end: datetime
    neighborhood: str = Field(min_length=1, max_length=80)
    capacity: Optional[int] = Field(default=None, ge=1)
    publishAt: Optional[datetime] = None               # if you already added scheduling
    category: Optional[Category] = "other"             # <-- Category (8 options now)
    
    # NEW: Visibility for viral loop (default: private)
    visibility: EventVisibility = "private"

class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    details: Optional[str] = Field(default=None, max_length=2000)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    neighborhood: Optional[str] = Field(default=None, min_length=1, max_length=80)
    capacity: Optional[int] = Field(default=None, ge=1)
    publishAt: Optional[datetime] = None
    category: Optional[Category] = None                # <-- Category (8 options)
    
    # NEW: Can update visibility
    visibility: Optional[EventVisibility] = None
    
    # Can update status (for cancellation)
    status: Optional[Literal["active", "canceled"]] = None

class EventOut(BaseModel):
    id: str
    title: str
    details: Optional[str] = None
    start: datetime
    end: datetime
    neighborhood: str
    capacity: Optional[int] = None
    
    # UPDATED: Changed from hostId to host_user_id (individual user, not household)
    host_user_id: str = Field(..., description="User ID of event host (individual)")
    
    createdAt: datetime
    updatedAt: datetime
    publishAt: datetime                                # ensure this exists if you use scheduling
    category: Category                                  # <-- NEW (non-optional in output)
    status: Literal["active","canceled"] = "active"
    
    # NEW: Visibility for viral loop (public RSVP)
    visibility: EventVisibility = Field(
        "private",
        description="Who can see this event? private=host only, link_only=anyone with link, public=discovery"
    )
    
    # NEW: Shareable link for public RSVP pages
    shareable_link: Optional[str] = Field(
        None,
        description="Short link for public RSVP (e.g., /e/abc123)"
    )
