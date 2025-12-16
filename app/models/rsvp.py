# app/models/rsvp.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class RSVPStatus(str, Enum):
    going = "going"
    maybe = "maybe"
    cant = "cant"


class EventRsvpHousehold(BaseModel):
    uid: str
    household_id: str
    last_name: Optional[str] = None
    neighborhood: Optional[str] = None
    household_type: Optional[str] = None
    child_ages: List[int] = []


class EventRsvpBuckets(BaseModel):
    going: List[EventRsvpHousehold] = []
    maybe: List[EventRsvpHousehold] = []
    cant: List[EventRsvpHousehold] = []
