# app/routes/users.py
"""
User routes - Individual-first architecture.

Users are individuals (not households). Households are optional groups
that users can link to.

New endpoints:
- POST /users/signup - Create new user profile
- GET /users/me - Get my profile
- PATCH /users/me - Update my profile
- POST /users/me/household/link - Link to existing household
- POST /users/me/household/create - Create new household
- DELETE /users/me/household - Unlink from household
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.user import (
    UserProfile,
    UserProfileUpdate,
    UserSignupRequest,
    UserProfileOut
)
from app.models.household import (
    Household,
    HouseholdCreate,
    HouseholdOut
)

router = APIRouter(tags=["users"], prefix="/users")


# ----------------------------- Helpers --------------------------------

def _now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _jsonify(x):
    """Convert datetime objects to ISO strings for JSON responses."""
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, list):
        return [_jsonify(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify(v) for k, v in x.items()}
    return x


def _get_user_profile(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from Firestore.
    Returns dict if found, None if not found.
    """
    ref = db.collection("users").document(uid)
    snap = ref.get()
    
    if hasattr(snap, "exists") and snap.exists:
        data = snap.to_dict() or {}
        data["uid"] = uid
        return data
    
    return None


def _get_household(household_id: str) -> Optional[Dict[str, Any]]:
    """
    Get household from Firestore.
    Returns dict if found, None if not found.
    """
    ref = db.collection("households").document(household_id)
    snap = ref.get()
    
    if hasattr(snap, "exists") and snap.exists:
        data = snap.to_dict() or {}
        data["id"] = household_id
        return data
    
    return None


# ----------------------------- Routes ---------------------------------

@router.post("/signup", response_model=UserProfileOut, status_code=status.HTTP_201_CREATED)
def signup_user(
    body: UserSignupRequest,
    claims=Depends(verify_token)
):
    """
    Create a new user profile.
    
    This is the first step in onboarding. Creates an individual user profile
    (NOT a household). User can optionally link to a household later.
    
    Individual-first architecture: Every person gets their own profile.
    """
    uid = claims["uid"]
    
    # Check if user already exists
    existing = _get_user_profile(uid)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User profile already exists. Use PATCH /users/me to update."
        )
    
    # Create new user profile
    now = _now()
    profile_data = {
        "uid": uid,
        "email": body.email,
        "first_name": body.first_name,
        "last_name": body.last_name,
        "profile_photo_url": body.profile_photo_url,
        "bio": None,
        "address": body.address,
        "lat": body.lat,
        "lng": body.lng,
        "discovery_opt_in": True,  # Default
        "visibility": "neighbors",  # Default
        "household_id": None,  # No household yet
        "interests": None,
        "created_at": now,
        "updated_at": now,
    }
    
    # Save to Firestore
    ref = db.collection("users").document(uid)
    ref.set(profile_data)
    
    return _jsonify(profile_data)


@router.get("/me", response_model=UserProfileOut)
def get_my_profile(claims=Depends(verify_token)):
    """
    Get the current user's profile.
    
    Returns the authenticated user's profile data.
    """
    uid = claims["uid"]
    
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete signup first."
        )
    
    return _jsonify(profile)


@router.patch("/me", response_model=UserProfileOut)
def update_my_profile(
    body: UserProfileUpdate,
    claims=Depends(verify_token)
):
    """
    Update the current user's profile.
    
    All fields are optional. Only provided fields will be updated.
    """
    uid = claims["uid"]
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete signup first."
        )
    
    # Build update dict (only include provided fields)
    updates: Dict[str, Any] = {}
    
    if body.first_name is not None:
        updates["first_name"] = body.first_name
    if body.last_name is not None:
        updates["last_name"] = body.last_name
    if body.profile_photo_url is not None:
        updates["profile_photo_url"] = body.profile_photo_url
    if body.bio is not None:
        updates["bio"] = body.bio
    if body.address is not None:
        updates["address"] = body.address
    if body.lat is not None:
        updates["lat"] = body.lat
    if body.lng is not None:
        updates["lng"] = body.lng
    if body.discovery_opt_in is not None:
        updates["discovery_opt_in"] = body.discovery_opt_in
    if body.visibility is not None:
        updates["visibility"] = body.visibility
    if body.household_id is not None:
        updates["household_id"] = body.household_id
    if body.interests is not None:
        updates["interests"] = body.interests
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update"
        )
    
    # Add updated timestamp
    updates["updated_at"] = _now()
    
    # Update in Firestore (use set with merge for fake DB compatibility)
    ref = db.collection("users").document(uid)
    ref.set(updates, merge=True)
    
    # Get updated profile
    updated_profile = _get_user_profile(uid)
    return _jsonify(updated_profile)


@router.post("/me/household/create", response_model=HouseholdOut, status_code=status.HTTP_201_CREATED)
def create_household(
    body: HouseholdCreate,
    claims=Depends(verify_token)
):
    """
    Create a new household and link current user to it.
    
    Household is optional! Singles and couples don't need households.
    This is typically used by families with kids.
    """
    uid = claims["uid"]
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete signup first."
        )
    
    # Check if user is already in a household
    if profile.get("household_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already linked to household {profile['household_id']}. Unlink first."
        )
    
    # Create new household
    household_id = f"household_{uuid.uuid4().hex[:12]}"
    now = _now()
    
    household_data = {
        "id": household_id,
        "name": body.name,
        "member_uids": [uid],  # Current user is first member
        "household_type": body.household_type,
        "kids": [kid.dict() for kid in body.kids] if body.kids else None,
        "created_at": now,
        "updated_at": now,
    }
    
    # Save household to Firestore
    household_ref = db.collection("households").document(household_id)
    household_ref.set(household_data)
    
    # Update user profile to link to household (use set with merge)
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "household_id": household_id,
        "updated_at": now
    }, merge=True)
    
    return _jsonify(household_data)


class HouseholdLinkRequest(BaseModel):
    """Request to link to an existing household."""
    household_id: str = Field(..., description="ID of household to link to")


@router.post("/me/household/link", response_model=UserProfileOut)
def link_to_household(
    body: HouseholdLinkRequest,
    claims=Depends(verify_token)
):
    """
    Link current user to an existing household.
    
    Use this when joining an existing household (e.g., spouse already created one).
    """
    uid = claims["uid"]
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete signup first."
        )
    
    # Check if user is already in a household
    if profile.get("household_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already linked to household {profile['household_id']}. Unlink first."
        )
    
    # Check if household exists
    household = _get_household(body.household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Household {body.household_id} not found"
        )
    
    now = _now()
    
    # Add user to household's member list
    member_uids = household.get("member_uids", [])
    if uid not in member_uids:
        member_uids.append(uid)
        household_ref = db.collection("households").document(body.household_id)
        household_ref.set({
            "member_uids": member_uids,
            "updated_at": now
        }, merge=True)
    
    # Update user profile to link to household (use set with merge)
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "household_id": body.household_id,
        "updated_at": now
    }, merge=True)
    
    # Get updated profile
    updated_profile = _get_user_profile(uid)
    return _jsonify(updated_profile)


@router.delete("/me/household", status_code=status.HTTP_204_NO_CONTENT)
def unlink_from_household(claims=Depends(verify_token)):
    """
    Unlink current user from their household.
    
    User will remain in the system but no longer be part of a household.
    This is useful for moves, separations, etc.
    """
    uid = claims["uid"]
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    household_id = profile.get("household_id")
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not linked to any household"
        )
    
    now = _now()
    
    # Remove user from household's member list
    household = _get_household(household_id)
    if household:
        member_uids = household.get("member_uids", [])
        if uid in member_uids:
            member_uids.remove(uid)
            household_ref = db.collection("households").document(household_id)
            household_ref.set({
                "member_uids": member_uids,
                "updated_at": now
            }, merge=True)
    
    # Update user profile to unlink from household (use set with merge)
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "household_id": None,
        "updated_at": now
    }, merge=True)
    
    return None


@router.get("/me/household", response_model=HouseholdOut)
def get_my_household(claims=Depends(verify_token)):
    """
    Get the household that the current user belongs to.
    
    Returns 404 if user is not linked to any household.
    """
    uid = claims["uid"]
    
    # Get user profile
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    household_id = profile.get("household_id")
    if not household_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not linked to any household"
        )
    
    # Get household
    household = _get_household(household_id)
    if not household:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Household {household_id} not found"
        )
    
    return _jsonify(household)
