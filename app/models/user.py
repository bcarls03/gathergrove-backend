"""
User profile model - Individual-first identity.

Every person gets their own UserProfile (separate from households).
Households are optional gro    # Privacy settings
    discovery_opt_in: bool
    visibility: str
    
    # Household link
    household_id: Optional[str] = None
    
    # Interests
    interests: Optional[list[str]] = Noneusers can link to.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


class UserProfile(BaseModel):
    """
    Individual user profile (not coupled to household).
    
    This is the primary identity model. Users can exist without households.
    """
    uid: str = Field(..., description="Firebase Auth UID (unique identifier)")
    email: EmailStr = Field(..., description="User's email address")
    
    # Personal info
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    profile_photo_url: Optional[str] = Field(None, description="Profile photo URL")
    bio: Optional[str] = Field(None, description="Short bio (optional)")
    
    # Location (approximate for privacy)
    address: Optional[str] = Field(None, description="Full address (not publicly shown)")
    lat: Optional[float] = Field(None, description="Latitude for proximity search")
    lng: Optional[float] = Field(None, description="Longitude for proximity search")
    location_precision: Optional[Literal["street", "zipcode"]] = Field(
        None,
        description="Precision level of location: 'street' for full address, 'zipcode' for ZIP only"
    )
    
    # Privacy settings
    discovery_opt_in: bool = Field(
        True, 
        description="Can neighbors discover this user? (default: True)"
    )
    visibility: Literal["private", "neighbors", "public"] = Field(
        "neighbors",
        description="Who can see this profile? (default: neighbors only)"
    )
    
    # Optional household linking
    household_id: Optional[str] = Field(
        None,
        description="ID of linked household (optional - singles don't have this)"
    )
    
    # Interests (optional)
    interests: Optional[list[str]] = Field(
        None,
        description="User interests for discovery filtering (e.g., hiking, cooking)"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When profile was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When profile was last updated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "uid": "abc123xyz",
                "email": "sarah@email.com",
                "first_name": "Sarah",
                "last_name": "Smith",
                "profile_photo_url": "https://example.com/photo.jpg",
                "bio": "Mom of 2, love hiking and board games",
                "address": "123 Oak St, Austin, TX 78701",
                "lat": 30.2672,
                "lng": -97.7431,
                "discovery_opt_in": True,
                "visibility": "neighbors",
                "household_id": "household_xyz",
                "interests": ["hiking", "cooking", "board_games"],
                "created_at": "2026-01-03T12:00:00Z",
                "updated_at": "2026-01-03T12:00:00Z"
            }
        }


class UserProfileUpdate(BaseModel):
    """
    Model for updating user profile (all fields optional).
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    discovery_opt_in: Optional[bool] = None
    visibility: Optional[Literal["private", "neighbors", "public"]] = None
    household_id: Optional[str] = None
    interests: Optional[list[str]] = None


class UserSignupRequest(BaseModel):
    """
    Request model for new user signup.
    """
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    address: Optional[str] = Field(None, max_length=200)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    profile_photo_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@email.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "address": "456 Elm St, Austin, TX",
                "lat": 30.2672,
                "lng": -97.7431
            }
        }


class IntentKid(BaseModel):
    """
    Kid metadata stored on person (user) record.
    Section 30: Person-owned intent kids (no names, no photos).
    """
    birthYear: int = Field(..., description="Birth year (e.g., 2018)")
    birthMonth: Optional[int] = Field(None, ge=1, le=12, description="Birth month (1-12, optional)")
    gender: Optional[Literal["male", "female", "prefer_not_to_say"]] = Field(None, description="Gender (optional)")
    awayAtCollege: bool = Field(False, description="Lives away from home (college, work, etc.)")
    canBabysit: bool = Field(False, description="Can help with babysitting / parent helper")


class UserIntent(BaseModel):
    """
    Person-level intent fields (Section 30).
    Stored on user record under 'intent' field.
    """
    household_type: Optional[Literal["family_with_kids", "empty_nesters", "singles_couples"]] = None
    kids: Optional[list[IntentKid]] = None


class UserProfileOut(BaseModel):
    """
    Model for user profile responses (what clients receive).
    """
    uid: str
    email: str
    first_name: str
    last_name: str
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Location - only show if user has discovery enabled
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Privacy settings
    discovery_opt_in: bool
    visibility: str
    
    # Household link
    household_id: Optional[str] = None
    
    # Interests
    interests: Optional[list[str]] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
