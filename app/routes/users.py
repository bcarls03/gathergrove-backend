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
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field

from app.core.firebase import db
from app.deps.auth import verify_token, require_user
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


@router.get("/me")
def get_my_profile(claims=Depends(verify_token)):
    """
    Get the current user's profile.
    
    Returns the authenticated user's profile data.
    
    DEV MODE (GG_DEV_AUTOCREATE_USER=1): Auto-creates user if they don't exist (for testing convenience)
    """
    uid = claims["uid"]
    email = claims.get("email", f"{uid}@example.com")
    
    profile = _get_user_profile(uid)
    if not profile:
        # DEV MODE ONLY: Auto-create user instead of returning 404
        # Only enabled when GG_DEV_AUTOCREATE_USER=1 (explicit local dev opt-in)
        # CI, tests, and production will return 404 as expected (default OFF)
        if os.getenv("GG_DEV_AUTOCREATE_USER") == "1":
            now = _now()
            profile = {
                "uid": uid,
                "email": email,
                "first_name": "",
                "last_name": "",
                "profile_photo_url": None,
                "bio": None,
                "address": None,
                "lat": None,
                "lng": None,
                "discovery_opt_in": True,
                "visibility": "neighbors",
                "household_id": None,
                "interests": None,
                "created_at": now,
                "updated_at": now,
            }
            ref = db.collection("users").document(uid)
            ref.set(profile)
            print(f"ℹ️  Auto-created user profile for {uid} on GET /users/me (dev mode convenience)")
        else:
            # Default behavior: missing user => 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for uid={uid}"
            )
    
    # Normalize household field: prefer householdId (new), fallback to household_id (old)
    household_id_value = None
    if "householdId" in profile:
        household_id_value = profile["householdId"]
    elif "household_id" in profile:
        household_id_value = profile["household_id"]
    
    # Ensure both fields are present for compatibility
    if household_id_value:
        profile["householdId"] = household_id_value
        profile["household_id"] = household_id_value
    
    return _jsonify(profile)


@router.post("")
@router.post("/", include_in_schema=False)
def create_or_update_user(
    body: dict,
    claims=Depends(verify_token)
):
    """
    POST /users - Create or update user (compatibility endpoint).
    
    This endpoint provides backward compatibility with legacy tests.
    It creates a user if they don't exist, or updates if they do.
    
    Non-admin users cannot set isAdmin=true (it's ignored).
    """
    uid = claims["uid"]
    email = claims.get("email", f"{uid}@example.com")
    is_admin = claims.get("admin", False)
    
    # Get existing profile or create minimal one
    profile = _get_user_profile(uid)
    now = _now()
    
    if not profile:
        # Create new profile
        profile = {
            "uid": uid,
            "email": email,
            "name": body.get("name", ""),
            "isAdmin": body.get("isAdmin", False) if is_admin else False,
            "favorites": [],
            "createdAt": now,
            "updatedAt": now,
        }
    else:
        # Update existing
        if "name" in body:
            profile["name"] = body["name"]
        if "isAdmin" in body and is_admin:
            # Only admins can set isAdmin
            profile["isAdmin"] = body["isAdmin"]
        profile["updatedAt"] = now
    
    # Save to Firestore
    ref = db.collection("users").document(uid)
    ref.set(profile, merge=True)
    
    # Return raw dict (not using response model for compatibility)
    return profile


@router.get("/me/favorites")
def get_my_favorites(claims=Depends(verify_token)):
    """
    GET /users/me/favorites - List favorited households.
    
    Returns paginated list of favorited households with normalized shape.
    """
    uid = claims["uid"]
    
    # Get user profile
    profile = _get_user_profile(uid)
    if not profile:
        # Create minimal profile if missing
        profile = {
            "uid": uid,
            "email": claims.get("email", f"{uid}@example.com"),
            "favorites": [],
        }
        ref = db.collection("users").document(uid)
        ref.set(profile, merge=True)
    
    fav_ids = profile.get("favorites", [])
    if not fav_ids:
        return {"items": [], "nextPageToken": None}
    
    # Fetch household details
    items = []
    for hid in fav_ids:
        household_ref = db.collection("households").document(hid)
        household_snap = household_ref.get()
        
        if not household_snap or not (hasattr(household_snap, "exists") and household_snap.exists):
            continue
        
        h = household_snap.to_dict() or {}
        
        # Extract child ages
        child_ages = []
        if "childAges" in h:
            child_ages = h["childAges"]
        elif "kids" in h and isinstance(h["kids"], list):
            for kid in h["kids"]:
                if isinstance(kid, dict) and "age_years" in kid:
                    child_ages.append(kid["age_years"])
        
        items.append({
            "id": hid,
            "lastName": h.get("lastName", ""),
            "type": h.get("type") or h.get("householdType") or h.get("kind", ""),
            "neighborhood": h.get("neighborhood") or h.get("neighborhoodCode", ""),
            "childAges": child_ages,
        })
    
    return {"items": items, "nextPageToken": None}


# Pydantic models for PATCH validation with extra='forbid'
class UserPatchModel(BaseModel):
    """Model for PATCH /users/me and PATCH /users/{uid}"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    isAdmin: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    discovery_opt_in: Optional[bool] = None
    visibility: Optional[str] = None
    
    class Config:
        extra = 'forbid'  # Reject unknown fields with 422


@router.patch("/me")
def patch_my_profile(
    body: UserPatchModel,
    claims=Depends(verify_token)
):
    """
    PATCH /users/me - Update current user's profile.
    
    Validates fields and rejects unknown fields (422).
    Empty body returns 400.
    """
    uid = claims["uid"]
    is_admin = claims.get("admin", False)
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Get update dict (only non-None fields)
    updates = body.dict(exclude_none=True)
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update"
        )
    
    # Non-admin cannot set isAdmin
    if "isAdmin" in updates and not is_admin:
        del updates["isAdmin"]
    
    # Add timestamp
    updates["updatedAt"] = _now()
    
    # Update in Firestore
    ref = db.collection("users").document(uid)
    ref.set(updates, merge=True)
    
    # Get updated profile
    updated_profile = _get_user_profile(uid)
    return updated_profile


@router.get("/{uid}")
def get_user_by_id(
    uid: str,
    claims=Depends(verify_token)
):
    """
    GET /users/{uid} - Get user by ID.
    
    Owner can get self (200).
    Non-admin cannot get another user (403).
    Admin can get anyone (200).
    """
    current_uid = claims["uid"]
    is_admin = claims.get("admin", False)
    
    # Check permissions
    if uid != current_uid and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    
    # Get user profile
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return profile


@router.patch("/{uid}")
def patch_user_by_id(
    uid: str,
    body: UserPatchModel,
    claims=Depends(verify_token)
):
    """
    PATCH /users/{uid} - Update user by ID.
    
    Owner can patch self (200).
    Non-admin patching another user (403).
    Admin can patch anyone (200).
    Empty body returns 400.
    Unknown fields return 422 (via extra='forbid').
    """
    current_uid = claims["uid"]
    is_admin = claims.get("admin", False)
    
    # Check permissions
    if uid != current_uid and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get update dict (only non-None fields)
    updates = body.dict(exclude_none=True)
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update"
        )
    
    # Non-admin cannot set isAdmin
    if "isAdmin" in updates and not is_admin:
        del updates["isAdmin"]
    
    # Add timestamp
    updates["updatedAt"] = _now()
    
    # Update in Firestore
    ref = db.collection("users").document(uid)
    ref.set(updates, merge=True)
    
    # Get updated profile
    updated_profile = _get_user_profile(uid)
    return updated_profile


@router.get("")
@router.get("/", include_in_schema=False)
def admin_list_users(
    claims=Depends(verify_token),
    page_size: int = Query(default=50, ge=1, le=200),
    page_token: Optional[str] = Query(default=None)
):
    """
    GET /users - Admin list users with pagination.
    
    Only admin allowed (403 for non-admin).
    Supports page_size query parameter.
    """
    is_admin = claims.get("admin", False)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )
    
    # Get all user IDs
    coll = db.collection("users")
    ids = []
    
    # Handle both real Firestore and fake DB
    if hasattr(coll, "stream"):  # Real Firestore
        for doc in coll.stream():
            ids.append(doc.id)
    elif hasattr(coll, "_docs"):  # Fake DB
        ids = list(coll._docs.keys())
    
    # Sort IDs for consistent pagination
    ids.sort()
    
    # Simple pagination
    start_idx = 0
    if page_token:
        try:
            start_idx = ids.index(page_token) + 1
        except ValueError:
            start_idx = 0
    
    # Get page
    page_ids = ids[start_idx:start_idx + page_size]
    next_token = page_ids[-1] if len(page_ids) == page_size and start_idx + page_size < len(ids) else None
    
    # Fetch user data
    items = []
    for uid in page_ids:
        profile = _get_user_profile(uid)
        if profile:
            # Ensure "id" field exists for tests
            if "id" not in profile:
                profile["id"] = uid
            items.append(profile)
    
    return {"items": items, "nextPageToken": next_token}


@router.post("/me/favorites/{household_id}")
def add_favorite(
    household_id: str,
    claims=Depends(verify_token)
):
    """
    POST /users/me/favorites/{household_id} - Add household to favorites.
    
    Idempotent operation.
    """
    uid = claims["uid"]
    email = claims.get("email", f"{uid}@example.com")
    
    # Ensure user exists
    profile = _get_user_profile(uid)
    if not profile:
        profile = {
            "uid": uid,
            "email": email,
            "favorites": [],
        }
        ref = db.collection("users").document(uid)
        ref.set(profile, merge=True)
    
    # Check if household exists
    household_ref = db.collection("households").document(household_id)
    household_snap = household_ref.get()
    if not household_snap or not (hasattr(household_snap, "exists") and household_snap.exists):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found"
        )
    
    # Add to favorites (idempotent)
    favs = set(profile.get("favorites", []))
    if household_id not in favs:
        favs.add(household_id)
        ref = db.collection("users").document(uid)
        ref.set({
            "favorites": list(sorted(favs)),
            "updatedAt": _now()
        }, merge=True)
    
    # Return updated favorites list
    updated_profile = _get_user_profile(uid)
    return {"ok": True, "favorites": updated_profile.get("favorites", [])}


@router.delete("/me/favorites/{household_id}")
def remove_favorite(
    household_id: str,
    claims=Depends(verify_token)
):
    """
    DELETE /users/me/favorites/{household_id} - Remove household from favorites.
    
    Idempotent operation.
    """
    uid = claims["uid"]
    
    # Get user profile
    profile = _get_user_profile(uid)
    if not profile:
        # No profile = nothing to remove
        return {"ok": True, "favorites": []}
    
    # Remove from favorites (idempotent)
    favs = set(profile.get("favorites", []))
    if household_id in favs:
        favs.remove(household_id)
        ref = db.collection("users").document(uid)
        ref.set({
            "favorites": list(sorted(favs)),
            "updatedAt": _now()
        }, merge=True)
    
    # Return updated favorites list
    updated_profile = _get_user_profile(uid)
    return {"ok": True, "favorites": updated_profile.get("favorites", [])}


@router.get("/profiles", response_model=list[UserProfileOut])
def get_user_profiles(
    uids: str = Query(..., description="Comma-separated list of user IDs"),
    claims=Depends(verify_token)
):
    """
    Get profiles for multiple users by their UIDs.
    
    Used for fetching household member details.
    Returns only found profiles (silently skips missing ones).
    """
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()]
    
    profiles = []
    for uid in uid_list:
        profile = _get_user_profile(uid)
        if profile:
            profiles.append(_jsonify(profile))
    
    return profiles


@router.patch("/me", response_model=UserProfileOut)
def update_my_profile(
    body: UserProfileUpdate,
    claims=Depends(verify_token)
):
    """
    Update the current user's profile.
    
    All fields are optional. Only provided fields will be updated.
    
    DEV MODE: Auto-creates user if they don't exist (for testing convenience)
    """
    uid = claims["uid"]
    email = claims.get("email", f"{uid}@example.com")
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        # DEV MODE: Auto-create user instead of failing
        # This handles cases where in-memory Firestore was cleared
        now = _now()
        profile = {
            "uid": uid,
            "email": email,
            "first_name": "",
            "last_name": "",
            "profile_photo_url": None,
            "bio": None,
            "address": None,
            "lat": None,
            "lng": None,
            "discovery_opt_in": True,
            "visibility": "neighbors",
            "household_id": None,
            "interests": None,
            "created_at": now,
            "updated_at": now,
        }
        ref = db.collection("users").document(uid)
        ref.set(profile)
        print(f"ℹ️  Auto-created user profile for {uid} (dev mode convenience)")
    
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
        # Write BOTH fields for compatibility
        updates["householdId"] = body.household_id
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
    
    DEV MODE: Auto-creates user if they don't exist (for testing convenience)
    """
    uid = claims["uid"]
    email = claims.get("email", f"{uid}@example.com")
    
    # Check if user exists
    profile = _get_user_profile(uid)
    if not profile:
        # DEV MODE: Auto-create user instead of failing
        now = _now()
        profile = {
            "uid": uid,
            "email": email,
            "first_name": "",
            "last_name": "",
            "profile_photo_url": None,
            "bio": None,
            "address": None,
            "lat": None,
            "lng": None,
            "discovery_opt_in": True,
            "visibility": "neighbors",
            "householdId": None,  # ✅ Use camelCase to match connections.py
            "interests": None,
            "created_at": now,
            "updated_at": now,
        }
        ref = db.collection("users").document(uid)
        ref.set(profile)
        print(f"ℹ️  Auto-created user profile for {uid} (dev mode convenience)")
    
    # Check if user is already in a household
    if profile.get("householdId") or profile.get("household_id"):  # Check both for backwards compat
        existing_hh = profile.get("householdId") or profile.get("household_id")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already linked to household {existing_hh}. Unlink first."
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
    # Write BOTH fields for compatibility: householdId (camelCase) and household_id (snake_case)
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "householdId": household_id,
        "household_id": household_id,
        "updated_at": now
    }, merge=True)
    
    # DEBUG: Verify the household_id was actually saved
    updated_profile = user_ref.get().to_dict()
    print(f"✅ After household creation: uid={uid}, householdId={updated_profile.get('householdId')}, household_id={updated_profile.get('household_id')}")
    
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
    if profile.get("householdId") or profile.get("household_id"):  # Check both for backwards compat
        existing_hh = profile.get("householdId") or profile.get("household_id")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already linked to household {existing_hh}. Unlink first."
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
    # Write BOTH fields for compatibility: householdId (camelCase) and household_id (snake_case)
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "householdId": body.household_id,
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
    
    household_id = profile.get("householdId") or profile.get("household_id")  # Check both for backwards compat
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
    # Clear BOTH fields for compatibility
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "householdId": None,
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
        print(f"🔍 DEBUG: get_my_household - User profile not found for uid={uid}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Check both camelCase and snake_case for backward compatibility
    household_id = profile.get("householdId") or profile.get("household_id")
    print(f"🔍 DEBUG: get_my_household - User {uid} has household_id={household_id}")
    
    if not household_id:
        # Fallback: Search for household where user is a member
        # This handles edge cases where household was created but link wasn't saved
        print(f"DEBUG: get_my_household - No household_id on profile for {uid}, searching by member_uids")
        households_ref = db.collection("households")
        query = households_ref.where("member_uids", "array_contains", uid)
        results = list(query.stream())
        
        if results:
            # Take first result (don't use .limit() as fake Firestore doesn't support it)
            household_data = results[0].to_dict()
            household_id = results[0].id
            household_data["id"] = household_id
            print(f"✅ Found household via member_uids: {household_id}")
            
            # Backfill BOTH fields on user profile for future reads
            user_ref = db.collection("users").document(uid)
            user_ref.set({
                "householdId": household_id,
                "household_id": household_id,
                "updated_at": _now()
            }, merge=True)
            print(f"✅ Backfilled householdId and household_id on user {uid}")
            
            return _jsonify(household_data)
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not linked to any household"
        )
    
    # Get household
    household = _get_household(household_id)
    if not household:
        print(f"🔍 DEBUG: get_my_household - Household {household_id} not found in Firestore")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Household {household_id} not found"
        )
    
    return _jsonify(household)


# ============================================================================
# Get Suggested Neighborhood Groups
# ============================================================================

@router.get("/me/suggested-groups")
def get_suggested_neighborhood_groups(user: Dict = Depends(require_user)):
    """
    Get neighborhood groups that match the user's address/location.
    Returns suggested groups without auto-joining the user.
    
    For HOAs, also extracts potential HOA name from user's address.
    """
    uid = user["uid"]
    
    # Get user profile
    profile = _get_user_profile(uid)
    
    user_lat = profile.get('lat')
    user_lng = profile.get('lng')
    user_address = profile.get('address', '').lower()
    
    # Need location to suggest groups
    if not user_lat or not user_lng:
        return {"suggested_groups": [], "hoa_name_hint": None}
    
    suggested_groups = []
    
    # Extract potential HOA name from address
    hoa_name_hint = _extract_hoa_name_from_address(user_address)
    
    # Query all neighborhood groups from Firestore
    try:
        groups_ref = db.collection("groups").where("type", "==", "neighborhood")
        groups_docs = groups_ref.stream()
        
        for group_doc in groups_docs:
            group_id = group_doc.id
            group_data = group_doc.to_dict()
            
            if not group_data:
                continue
            
            # Check if user matches this group
            if _should_join_neighborhood(user_lat, user_lng, user_address, group_data):
                # Check if user is already a member
                members = group_data.get('members', [])
                is_member = any(m.get('user_id') == uid for m in members)
                
                if not is_member:
                    # Add to suggestions
                    suggested_groups.append({
                        'id': group_id,
                        'name': group_data.get('name'),
                        'type': group_data.get('type'),
                        'metadata': group_data.get('metadata', {}),
                        'member_count': len(members)
                    })
    
    except Exception as e:
        print(f"⚠️  Error fetching suggested groups: {e}")
        return {"suggested_groups": [], "hoa_name_hint": None}
    
    return {
        "suggested_groups": suggested_groups,
        "hoa_name_hint": hoa_name_hint  # Frontend can use this to pre-fill HOA creation form
    }


@router.post("/me/join-group/{group_id}")
def join_neighborhood_group(group_id: str, user: Dict = Depends(require_user)):
    """
    Join a neighborhood group by ID.
    
    For HOA groups (metadata.neighborhood_type == 'hoa'):
    - New members start with verification_status='pending'
    - Requires 2 verified neighbors or admin approval
    
    For other groups:
    - Instant join with verification_status='admin_verified'
    """
    uid = user["uid"]
    
    # Get group from Firestore
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    members = group_data.get('members', [])
    metadata = group_data.get('metadata', {})
    
    # Check if already a member
    is_member = any(m.get('user_id') == uid for m in members)
    
    if is_member:
        return {"message": "Already a member of this group"}
    
    # Determine verification status based on group type
    is_hoa = (
        group_data.get('type') == 'neighborhood' and 
        metadata.get('neighborhood_type') == 'hoa'
    )
    
    verification_status = 'pending' if is_hoa else 'admin_verified'
    
    # Add user as member
    members.append({
        'user_id': uid,
        'role': 'member',
        'joined_at': datetime.now(timezone.utc).isoformat(),
        'verification_status': verification_status,
        'verified_by': []  # Will be populated when neighbors vouch
    })
    
    # Update group
    group_ref.update({'members': members})
    
    if is_hoa and verification_status == 'pending':
        return {
            "message": f"Join request sent to {group_data.get('name')}. Pending verification.",
            "verification_status": "pending"
        }
    else:
        return {
            "message": f"Successfully joined {group_data.get('name')}",
            "verification_status": "admin_verified"
        }


@router.delete("/me/leave-group/{group_id}")
def leave_neighborhood_group(group_id: str, user: Dict = Depends(require_user)):
    """
    Leave a neighborhood group by ID.
    """
    uid = user["uid"]
    
    # Get group from Firestore
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    members = group_data.get('members', [])
    
    # Check if user is a member
    is_member = any(m.get('user_id') == uid for m in members)
    
    if not is_member:
        return {"message": "Not a member of this group"}
    
    # Remove user from members
    members = [m for m in members if m.get('user_id') != uid]
    
    # Update group
    group_ref.update({'members': members})
    
    return {"message": f"Successfully left {group_data.get('name')}"}


@router.post("/groups/{group_id}/vouch-for-member")
def vouch_for_member(
    group_id: str,
    member_user_id: str,
    user: Dict = Depends(require_user)
):
    """
    Vouch for a pending member in an HOA group.
    
    Requirements:
    - Voucher must be a verified member (verification_status = 'admin_verified' or 'neighbor_vouched')
    - Member must be in 'pending' status
    - Once 2 verified members vouch, status changes to 'neighbor_vouched'
    """
    uid = user["uid"]
    
    # Get group
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    members = group_data.get('members', [])
    
    # Find voucher (current user)
    voucher = next((m for m in members if m.get('user_id') == uid), None)
    if not voucher:
        raise HTTPException(status_code=403, detail="You must be a member to vouch")
    
    # Check voucher is verified
    voucher_status = voucher.get('verification_status', 'admin_verified')
    if voucher_status == 'pending':
        raise HTTPException(status_code=403, detail="Only verified members can vouch for others")
    
    # Find member to vouch for
    member_index = next(
        (i for i, m in enumerate(members) if m.get('user_id') == member_user_id),
        None
    )
    
    if member_index is None:
        raise HTTPException(status_code=404, detail="Member not found in this group")
    
    member = members[member_index]
    
    # Check member is pending
    if member.get('verification_status') != 'pending':
        return {"message": "Member is already verified"}
    
    # Add vouch
    verified_by = member.get('verified_by', [])
    if uid in verified_by:
        return {"message": "You have already vouched for this member"}
    
    verified_by.append(uid)
    members[member_index]['verified_by'] = verified_by
    
    # Check if threshold reached (2 vouches)
    if len(verified_by) >= 2:
        members[member_index]['verification_status'] = 'neighbor_vouched'
        message = f"Member verified by neighbors! ({len(verified_by)} vouches)"
    else:
        message = f"Vouch recorded. {2 - len(verified_by)} more vouch(es) needed."
    
    # Update group
    group_ref.update({'members': members})
    
    return {
        "message": message,
        "verification_status": members[member_index]['verification_status'],
        "vouch_count": len(verified_by)
    }


@router.post("/groups/{group_id}/verify-member")
def admin_verify_member(
    group_id: str,
    member_user_id: str,
    approve: bool,
    user: Dict = Depends(require_user)
):
    """
    Admin verification of a member (HOA board member only).
    
    - Admins can approve or reject members
    - Approval sets verification_status to 'admin_verified'
    - Rejection sets back to 'pending' or removes member
    """
    uid = user["uid"]
    
    # Get group
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    members = group_data.get('members', [])
    
    # Check if current user is admin
    admin = next((m for m in members if m.get('user_id') == uid), None)
    if not admin or admin.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only HOA admins can verify members")
    
    # Find member to verify
    member_index = next(
        (i for i, m in enumerate(members) if m.get('user_id') == member_user_id),
        None
    )
    
    if member_index is None:
        raise HTTPException(status_code=404, detail="Member not found in this group")
    
    if approve:
        # Approve member
        members[member_index]['verification_status'] = 'admin_verified'
        members[member_index]['verified_by'] = [uid]  # Track admin who verified
        message = "Member approved by HOA admin"
    else:
        # Reject member - remove from group
        members.pop(member_index)
        message = "Member removed from group"
    
    # Update group
    group_ref.update({'members': members})
    
    return {"message": message, "approved": approve}


@router.get("/groups/{group_id}/pending-members")
def get_pending_members(group_id: str, user: Dict = Depends(require_user)):
    """
    Get list of pending members for admin review.
    
    Only admins can see pending members.
    Returns members with verification_status='pending' or 'neighbor_vouched'
    """
    uid = user["uid"]
    
    # Get group
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    members = group_data.get('members', [])
    
    # Check if current user is admin
    admin = next((m for m in members if m.get('user_id') == uid), None)
    if not admin or admin.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only HOA admins can view pending members")
    
    # Filter pending/neighbor-vouched members
    pending_members = [
        {
            'user_id': m.get('user_id'),
            'joined_at': m.get('joined_at'),
            'verification_status': m.get('verification_status'),
            'vouch_count': len(m.get('verified_by', []))
        }
        for m in members
        if m.get('verification_status') in ['pending', 'neighbor_vouched']
    ]
    
    return {
        "group_name": group_data.get('name'),
        "pending_members": pending_members,
        "count": len(pending_members)
    }


# ============================================================================
# Auto-Join Neighborhood Groups Helper (DEPRECATED - keeping for reference)
# ============================================================================

def _auto_join_neighborhood_groups(uid: str, user_data: Dict[str, Any]) -> None:
    """
    Automatically add user to matching neighborhood groups based on their address.
    
    This function:
    1. Queries all neighborhood groups
    2. Checks if user's location matches group criteria
    3. Auto-adds user as a member if they match
    
    Matching strategies:
    - Apartment complexes: Exact address match
    - Geographic neighborhoods: Radius-based distance check
    - HOAs/Subdivisions: Boundary polygon check (future)
    """
    user_lat = user_data.get('lat')
    user_lng = user_data.get('lng')
    user_address = user_data.get('address', '').lower()
    
    # Need location to auto-join
    if not user_lat or not user_lng:
        return
    
    # Query all neighborhood groups from Firestore
    try:
        groups_ref = db.collection("groups").where("type", "==", "neighborhood")
        groups_docs = groups_ref.stream()
        
        for group_doc in groups_docs:
            group_id = group_doc.id
            group_data = group_doc.to_dict()
            
            if not group_data:
                continue
            
            # Check if user should join this group
            if _should_join_neighborhood(user_lat, user_lng, user_address, group_data):
                # Check if user is already a member
                members = group_data.get('members', [])
                is_member = any(m.get('user_id') == uid for m in members)
                
                if not is_member:
                    # Auto-add user as member
                    members.append({
                        'user_id': uid,
                        'role': 'member',
                        'joined_at': datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Update group in Firestore
                    db.collection("groups").document(group_id).update({'members': members})
                    
                    print(f"✅ Auto-joined user {uid} to neighborhood group {group_data.get('name')}")
    
    except Exception as e:
        # Log error but don't fail the profile update
        print(f"⚠️  Error auto-joining neighborhood groups: {e}")


def _extract_hoa_name_from_address(address: str) -> Optional[str]:
    """
    Extract potential HOA/subdivision name from an address.
    
    Examples:
        "789 Oakwood Hills Dr, Portland, OR 97203" → "Oakwood Hills"
        "123 Cedar Ridge Ln, Beaverton, OR 97006" → "Cedar Ridge"
        "456 Maple Grove Ct, Tigard, OR 97223" → "Maple Grove"
        "789 SW Main St, Portland, OR 97205" → None (street name, not HOA)
    
    Strategy:
    1. Look for multi-word patterns before street suffixes (Dr, Ln, Ct, Way, etc.)
    2. Filter out directional prefixes (SW, NE, etc.)
    3. Prioritize 2-3 word combinations that sound like subdivision names
    """
    import re
    
    if not address:
        return None
    
    # Normalize address
    addr_lower = address.lower()
    
    # Common street suffixes to identify where street name ends
    street_suffixes = [
        'drive', 'dr', 'lane', 'ln', 'court', 'ct', 'way', 'street', 'st',
        'avenue', 'ave', 'road', 'rd', 'circle', 'cir', 'place', 'pl',
        'boulevard', 'blvd', 'parkway', 'pkwy', 'terrace', 'ter'
    ]
    
    # Directional prefixes to ignore
    directionals = ['north', 'n', 'south', 's', 'east', 'e', 'west', 'w',
                   'northeast', 'ne', 'northwest', 'nw', 'southeast', 'se', 'southwest', 'sw']
    
    # Common single words that likely aren't HOA names (too generic)
    generic_words = ['main', 'first', 'second', 'third', 'oak', 'pine', 'elm',
                     'maple', 'cedar', 'birch', 'willow']
    
    # Extract the street portion (before city/state/zip)
    # Pattern: number + words + suffix
    # Example: "789 Oakwood Hills Dr" from "789 Oakwood Hills Dr, Portland, OR 97203"
    street_pattern = r'^\d+\s+(.+?)(?:,|$)'
    match = re.search(street_pattern, addr_lower)
    
    if not match:
        return None
    
    street_portion = match.group(1).strip()
    
    # Remove directional prefix if present
    words = street_portion.split()
    if words and words[0] in directionals:
        words = words[1:]
    
    # Find the street suffix
    suffix_idx = -1
    for i, word in enumerate(words):
        if word.rstrip('.') in street_suffixes:
            suffix_idx = i
            break
    
    if suffix_idx <= 0:
        return None
    
    # Extract words before the suffix
    name_words = words[:suffix_idx]
    
    # Need at least 1 word for potential subdivision name
    # Allow single-word names like "Nicole Lane" or "Riverside Drive"
    if len(name_words) < 1:
        return None
    
    # For single-word names, skip if too generic (but allow proper names)
    if len(name_words) == 1:
        word = name_words[0]
        # Skip generic words unless they're capitalized (suggesting proper name)
        if word in generic_words:
            return None
    
    # Capitalize each word and join
    hoa_name = ' '.join(word.capitalize() for word in name_words)
    
    return hoa_name


def _should_join_neighborhood(
    lat: float, 
    lng: float, 
    address: str, 
    group_data: Dict[str, Any]
) -> bool:
    """
    Determine if user should auto-join this neighborhood group.
    
    Returns True if user's location matches group criteria.
    """
    metadata = group_data.get('metadata', {})
    neighborhood_type = metadata.get('neighborhood_type', '')
    
    # Strategy 1: Apartment Complex - Exact address match
    if neighborhood_type == 'apartment_complex':
        building_address = metadata.get('building_address', '').lower()
        if building_address and building_address in address:
            return True
    
    # Strategy 2: Radius-based neighborhoods (default for open neighborhoods)
    if 'center_lat' in metadata and 'center_lng' in metadata:
        center_lat = metadata.get('center_lat')
        center_lng = metadata.get('center_lng')
        radius_miles = metadata.get('radius_miles', 1.0)  # Default 1 mile radius
        
        distance = _calculate_distance_miles(lat, lng, center_lat, center_lng)
        if distance <= radius_miles:
            return True
    
    # Strategy 3: Address substring match (for named subdivisions/HOAs)
    # Use smart extraction to match HOA name from user's address
    if neighborhood_type in ['hoa', 'subdivision']:
        # Try exact match first (subdivision_name in metadata)
        subdivision_name = metadata.get('subdivision_name', '').lower()
        if subdivision_name and subdivision_name in address:
            return True
        
        # Try matching extracted HOA name from address
        extracted_hoa = _extract_hoa_name_from_address(address)
        group_name = group_data.get('name', '').lower()
        
        if extracted_hoa:
            # Match if extracted HOA name is in group name
            # Example: "Oakwood Hills" extracted from address matches "Oakwood Hills HOA" group
            if extracted_hoa.lower() in group_name:
                return True
            
            # Also check if it matches hoa_name in metadata
            hoa_name_meta = metadata.get('hoa_name', '').lower()
            if hoa_name_meta and extracted_hoa.lower() in hoa_name_meta:
                return True
    
    # Future: Strategy 4 - Polygon boundary check
    # if 'boundary_polygon' in metadata:
    #     return _is_point_in_polygon(lat, lng, metadata['boundary_polygon'])
    
    return False


def _calculate_distance_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two lat/lng points in miles using Haversine formula.
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Earth's radius in miles
    R = 3959.0
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lng1_rad = radians(lng1)
    lat2_rad = radians(lat2)
    lng2_rad = radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return distance
