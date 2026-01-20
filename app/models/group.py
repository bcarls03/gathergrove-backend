"""
Universal Group Model for GatherGrove

Groups are the core organizing layer. They can represent:
- Neighborhoods
- Households
- Activity groups (sports teams, clubs)
- Interest groups (book clubs, wine tasting)
- Extended families

This flexible structure avoids hardcoding specific group types
and allows natural expansion as new use cases emerge.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime

# Group types - can be extended without schema changes
GroupType = Literal[
    "neighborhood",
    "household", 
    "activity",
    "interest",
    "extended-family"
]

class GroupMember(BaseModel):
    """Member of a group with role and join timestamp"""
    user_id: str = Field(..., description="Firebase UID of the user")
    role: Literal["admin", "member"] = Field(default="member")
    joined_at: datetime = Field(default_factory=datetime.now)
    
    # HOA verification fields
    verification_status: Literal["pending", "neighbor_vouched", "admin_verified"] = Field(
        default="admin_verified",
        description="Verification status for HOA groups (pending → neighbor_vouched → admin_verified)"
    )
    verified_by: Optional[List[str]] = Field(
        default=None,
        description="List of user_ids who vouched for this member (for neighbor verification)"
    )

class Group(BaseModel):
    """
    Universal group model - households, neighborhoods, activities, etc.
    
    Type-specific data is stored in the flexible `metadata` field,
    avoiding the need for separate models for each group type.
    """
    id: str = Field(..., description="Unique group identifier")
    type: GroupType = Field(..., description="Type of group")
    name: str = Field(..., min_length=1, max_length=200, description="Display name")
    members: List[GroupMember] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="""Flexible storage for type-specific data.
        
        For 'neighborhood' type with neighborhood_type='hoa':
        {
            "neighborhood_type": "hoa",
            "hoa_name": "Oakwood Hills HOA",
            "management_company": "ABC Management Co.",  # optional
            "amenities": ["pool", "clubhouse", "tennis courts"],  # optional
            "boundaries": {  # optional
                "streets": ["Oakwood Dr", "Oak Lane"],
                "zip": "97203"
            },
            "board_contact": "board@oakwoodhills.com",  # optional
            "website": "https://oakwoodhills.com"  # optional
        }
        
        For 'neighborhood' type with neighborhood_type='apartment_complex':
        {
            "neighborhood_type": "apartment_complex",
            "building_address": "123 River Street",
            "building_name": "Riverside Apartments",
            "management_company": "Property Management Inc."
        }
        
        For 'neighborhood' type with neighborhood_type='open_neighborhood':
        {
            "neighborhood_type": "open_neighborhood",
            "area_name": "Pearl District",
            "approximate_center": {"lat": 45.5231, "lng": -122.6765}
        }
        """
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "id": "group-123",
                    "type": "household",
                    "name": "Smith Family",
                    "members": [
                        {
                            "user_id": "uid-456",
                            "role": "admin",
                            "joined_at": "2026-01-05T10:00:00Z"
                        }
                    ],
                    "metadata": {
                        "household_type": "family",
                        "children": [
                            {
                                "birth_month": 6,
                                "birth_year": 2018,
                                "gender": "Female",
                                "can_babysit": False
                            }
                        ]
                    },
                    "created_at": "2026-01-05T10:00:00Z",
                    "updated_at": "2026-01-05T10:00:00Z"
                }
            ]
        }

# Request/Response models
class CreateGroupRequest(BaseModel):
    """Request to create a new group"""
    type: GroupType
    name: str = Field(..., min_length=1, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UpdateGroupRequest(BaseModel):
    """Request to update group details"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    metadata: Optional[Dict[str, Any]] = None

class AddMemberRequest(BaseModel):
    """Request to add a member to a group"""
    user_id: str
    role: Literal["admin", "member"] = "member"

class GroupResponse(BaseModel):
    """API response containing group data"""
    success: bool
    group: Optional[Group] = None
    message: Optional[str] = None

class GroupListResponse(BaseModel):
    """API response containing list of groups"""
    success: bool
    groups: List[Group]
    total: int
    message: Optional[str] = None


# HOA-specific models
class JoinGroupRequest(BaseModel):
    """Request to join a group (with optional verification note)"""
    note: Optional[str] = Field(None, max_length=500, description="Optional message for group admins")


class VouchForMemberRequest(BaseModel):
    """Request for verified member to vouch for pending member"""
    member_user_id: str = Field(..., description="User ID of the member to vouch for")


class VerifyMemberRequest(BaseModel):
    """Admin request to verify a member"""
    member_user_id: str = Field(..., description="User ID of the member to verify")
    verification_status: Literal["admin_verified", "pending"] = Field(
        ...,
        description="New verification status (admin_verified to approve, pending to reject)"
    )
