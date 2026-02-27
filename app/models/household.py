"""
Household model - Optional grouping for users.

Households are groups that users can optionally link to.
Multiple users (adults) can be members of the same household.
"""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Kid(BaseModel):
    """
    Child information (age range only, no names for privacy).
    """
    age_years: Optional[int] = Field(
        None,
        description="Child's exact age in years (canonical field)"
    )
    age_range: Optional[Literal["0-2", "3-5", "6-8", "9-12", "13-17", "18+"]] = Field(
        None,
        description="Child's age range (backward compatibility fallback)"
    )
    birth_year: Optional[int] = Field(
        None,
        description="Child's birth year (for precise age reconstruction)"
    )
    birth_month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Child's birth month 1-12 (for precise age reconstruction)"
    )
    gender: Optional[Literal["male", "female", "prefer_not_to_say"]] = Field(
        None,
        description="Child's gender (optional)"
    )
    interests: Optional[list[str]] = Field(
        None,
        description="Child's interests for playdate matching (e.g., soccer, art)"
    )
    available_for_babysitting: bool = Field(
        False,
        description="Is this child available for babysitting? (opt-in)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "age_range": "6-8",
                "gender": "female",
                "interests": ["soccer", "art"],
                "available_for_babysitting": False
            }
        }


class Household(BaseModel):
    """
    Household model - Optional group that users can link to.
    
    Not all users have households (singles, couples without kids).
    Multiple adults can be members of the same household.
    """
    id: str = Field(..., description="Unique household ID (NOT user UID)")
    name: str = Field(..., description="Household name (e.g., 'The Smith Family')")
    
    # Members (adults)
    member_uids: list[str] = Field(
        default_factory=list,
        description="List of user UIDs who are members of this household"
    )
    
    # Household type
    household_type: Optional[Literal["family_with_kids", "empty_nesters", "singles_couples"]] = Field(
        None,
        description="Type of household"
    )
    
    # Children (if family_with_kids)
    kids: Optional[list[Kid]] = Field(
        None,
        description="List of children in household (age ranges only, no names)"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When household was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When household was last updated"
    )
    onboarding_completed_at: Optional[datetime] = Field(
        None,
        description="When household completed onboarding (immutable, for KPI tracking)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "household_abc123",
                "name": "The Smith Family",
                "member_uids": ["user_sarah_123", "user_mike_456"],
                "household_type": "family_with_kids",
                "kids": [
                    {
                        "age_range": "6-8",
                        "gender": "female",
                        "interests": ["soccer", "art"],
                        "available_for_babysitting": False
                    },
                    {
                        "age_range": "3-5",
                        "gender": "male",
                        "interests": ["dinosaurs", "legos"],
                        "available_for_babysitting": False
                    }
                ],
                "created_at": "2026-01-03T12:00:00Z",
                "updated_at": "2026-01-03T12:00:00Z"
            }
        }


class HouseholdCreate(BaseModel):
    """
    Request model for creating a new household.
    """
    name: str = Field(..., min_length=1, max_length=100)
    household_type: Literal["family_with_kids", "empty_nesters", "singles_couples"]
    kids: Optional[list[Kid]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "The Doe Family",
                "household_type": "family_with_kids",
                "kids": [
                    {
                        "age_range": "6-8",
                        "gender": "female",
                        "interests": ["soccer"]
                    }
                ]
            }
        }


class HouseholdUpdate(BaseModel):
    """
    Model for updating household (all fields optional).
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    household_type: Optional[Literal["family_with_kids", "empty_nesters", "singles_couples"]] = None
    kids: Optional[list[Kid]] = None


class HouseholdOut(BaseModel):
    """
    Model for household responses (what clients receive).
    """
    id: str
    name: str
    member_uids: list[str]
    household_type: Optional[str] = None
    kids: Optional[list[Kid]] = None
    created_at: datetime
    updated_at: datetime
