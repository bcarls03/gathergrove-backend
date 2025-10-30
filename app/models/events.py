# === add/imports ===
from typing import Literal, Optional
Category = Literal["neighborhood", "playdate", "help", "pet", "other"]

# === update your Pydantic models ===
class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    details: Optional[str] = Field(default=None, max_length=2000)
    start: datetime
    end: datetime
    neighborhood: str = Field(min_length=1, max_length=80)
    capacity: Optional[int] = Field(default=None, ge=1)
    publishAt: Optional[datetime] = None               # if you already added scheduling
    category: Optional[Category] = "other"             # <-- NEW (optional, default)

class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    details: Optional[str] = Field(default=None, max_length=2000)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    neighborhood: Optional[str] = Field(default=None, min_length=1, max_length=80)
    capacity: Optional[int] = Field(default=None, ge=1)
    publishAt: Optional[datetime] = None
    category: Optional[Category] = None                # <-- NEW

class EventOut(BaseModel):
    id: str
    title: str
    details: Optional[str] = None
    start: datetime
    end: datetime
    neighborhood: str
    capacity: Optional[int] = None
    hostId: str
    createdAt: datetime
    updatedAt: datetime
    publishAt: datetime                                # ensure this exists if you use scheduling
    category: Category                                  # <-- NEW (non-optional in output)
    status: Literal["active","canceled"] = "active"
