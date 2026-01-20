"""
Universal Groups API

Handles all group types (neighborhoods, households, activities, interests, etc.)
using a single flexible endpoint structure.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.group import (
    Group,
    GroupType,
    GroupMember,
    CreateGroupRequest,
    UpdateGroupRequest,
    AddMemberRequest,
    GroupResponse,
    GroupListResponse
)
from app.deps.auth import get_current_user_uid
from app.core.firebase import db

router = APIRouter(prefix="/groups", tags=["groups"])

# TODO: Replace with real Firestore integration
# For now, using in-memory storage for demo
_groups_db: dict[str, Group] = {}


@router.post("", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """
    Create a new group of any type (household, activity, interest, etc.)
    
    The creator automatically becomes an admin member.
    Type-specific data is stored in the flexible metadata field.
    """
    try:
        group_id = str(uuid.uuid4())
        
        # For HOA groups, creator starts as admin with admin_verified status
        # For other groups, creator starts as admin with admin_verified status
        verification_status = "admin_verified"
        
        # Create group with creator as admin
        group = Group(
            id=group_id,
            type=request.type,
            name=request.name,
            members=[
                GroupMember(
                    user_id=current_user_uid,
                    role="admin",
                    joined_at=datetime.now(),
                    verification_status=verification_status,
                    verified_by=[current_user_uid]  # Self-verified as creator
                )
            ],
            metadata=request.metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to Firestore
        group_dict = group.dict()
        # Convert datetime objects to ISO strings for Firestore
        group_dict['created_at'] = group.created_at.isoformat()
        group_dict['updated_at'] = group.updated_at.isoformat()
        for member in group_dict['members']:
            member['joined_at'] = member['joined_at'].isoformat()
        
        db.collection("groups").document(group_id).set(group_dict)
        _groups_db[group_id] = group  # Also update in-memory for compatibility
        
        print(f"✅ Created {request.type} group '{request.name}' with ID {group_id}")
        
        return GroupResponse(
            success=True,
            group=group,
            message=f"Successfully created {request.type} group"
        )
    
    except Exception as e:
        print(f"❌ Error creating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """Get details of a specific group"""
    
    # TODO: Get from Firestore
    # group_doc = await db.collection("groups").document(group_id).get()
    
    group = _groups_db.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify user has access (is member or admin)
    is_member = any(m.user_id == current_user_uid for m in group.members)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    return GroupResponse(success=True, group=group)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    request: UpdateGroupRequest,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """Update group details (admin only)"""
    
    group = _groups_db.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify user is admin
    is_admin = any(
        m.user_id == current_user_uid and m.role == "admin" 
        for m in group.members
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update fields
    if request.name:
        group.name = request.name
    if request.metadata is not None:
        group.metadata = request.metadata
    group.updated_at = datetime.now()
    
    # TODO: Update in Firestore
    # await db.collection("groups").document(group_id).update(group.dict())
    _groups_db[group_id] = group
    
    return GroupResponse(success=True, group=group, message="Group updated")


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """Delete a group (admin only)"""
    
    group = _groups_db.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify user is admin
    is_admin = any(
        m.user_id == current_user_uid and m.role == "admin" 
        for m in group.members
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # TODO: Delete from Firestore
    # await db.collection("groups").document(group_id).delete()
    del _groups_db[group_id]
    
    return {"success": True, "message": "Group deleted"}


@router.post("/{group_id}/members", response_model=GroupResponse)
async def add_member(
    group_id: str,
    request: AddMemberRequest,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """Add a member to the group (admin only)"""
    
    group = _groups_db.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify user is admin
    is_admin = any(
        m.user_id == current_user_uid and m.role == "admin" 
        for m in group.members
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if user is already a member
    if any(m.user_id == request.user_id for m in group.members):
        raise HTTPException(status_code=400, detail="User is already a member")
    
    # Add new member
    new_member = GroupMember(
        user_id=request.user_id,
        role=request.role,
        joined_at=datetime.now()
    )
    group.members.append(new_member)
    group.updated_at = datetime.now()
    
    # TODO: Update in Firestore
    _groups_db[group_id] = group
    
    return GroupResponse(success=True, group=group, message="Member added")


@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: str,
    user_id: str,
    current_user_uid: str = Depends(get_current_user_uid)
):
    """Remove a member from the group (admin only, or user can remove themselves)"""
    
    group = _groups_db.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Can remove yourself, or admin can remove others
    is_admin = any(
        m.user_id == current_user_uid and m.role == "admin" 
        for m in group.members
    )
    if user_id != current_user_uid and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove member
    group.members = [m for m in group.members if m.user_id != user_id]
    group.updated_at = datetime.now()
    
    # TODO: Update in Firestore
    _groups_db[group_id] = group
    
    return {"success": True, "message": "Member removed"}


@router.get("", response_model=GroupListResponse)
async def list_groups(
    type: Optional[GroupType] = Query(None, description="Filter by group type"),
    user_id: Optional[str] = Query(None, description="Filter by user membership"),
    current_user_uid: str = Depends(get_current_user_uid)
):
    """
    List groups with optional filters
    
    - Filter by type (household, activity, interest, etc.)
    - Filter by user membership
    """
    
    # Query Firestore for groups
    groups_ref = db.collection("groups")
    
    # Apply type filter at query level if possible
    if type:
        groups_docs = groups_ref.where("type", "==", type).stream()
    else:
        # Get all groups - need to iterate through the collection
        # Since fake Firestore doesn't have .stream() without where, get all docs
        groups_docs = []
        groups_coll = groups_ref
        for doc_id in groups_coll._docs:
            doc_snap = groups_coll.document(doc_id).get()
            if doc_snap.exists:
                groups_docs.append(doc_snap)
    
    # Convert Firestore docs to Group models
    groups = []
    for doc in groups_docs:
        data = doc.to_dict()
        if data:
            # Convert members array to GroupMember objects
            members = []
            for m in data.get('members', []):
                members.append(GroupMember(
                    user_id=m.get('user_id'),
                    role=m.get('role', 'member'),
                    joined_at=m.get('joined_at')
                ))
            
            group = Group(
                id=doc.id,
                type=data.get('type'),
                name=data.get('name'),
                members=members,
                metadata=data.get('metadata', {}),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at') or data.get('created_at')  # Fallback to created_at if updated_at is None
            )
            groups.append(group)
    
    # Apply user_id filter
    if user_id:
        groups = [
            g for g in groups 
            if any(m.user_id == user_id for m in g.members)
        ]
    
    return GroupListResponse(
        success=True,
        groups=groups,
        total=len(groups)
    )
