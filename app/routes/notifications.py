# app/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.firebase import db
from app.deps.auth import verify_token
from app.models.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _list_docs(coll):
    """List documents from Firestore collection (works with real and fake DB)"""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


@router.get("", response_model=NotificationListResponse, summary="Get user notifications")
def list_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    claims=Depends(verify_token),
):
    """
    Get notifications for the current user.
    
    - Returns notifications ordered by created_at (newest first)
    - Supports pagination via limit/offset
    - Can filter to unread_only
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    coll = db.collection("notifications")
    all_notifications = []
    
    # Fetch all notifications for this user
    for doc_id, data in _list_docs(coll):
        if data.get("user_id") == uid:
            # Filter by read status if requested
            if unread_only and data.get("read", False):
                continue
            
            all_notifications.append(
                NotificationResponse(
                    id=doc_id,
                    user_id=data.get("user_id", ""),
                    type=data.get("type", ""),
                    title=data.get("title", ""),
                    body=data.get("body", ""),
                    data=data.get("data", {}),
                    read=data.get("read", False),
                    created_at=data.get("created_at", ""),
                )
            )
    
    # Sort by created_at (newest first)
    all_notifications.sort(key=lambda n: n.created_at, reverse=True)
    
    # Calculate stats
    total = len(all_notifications)
    unread_count = sum(1 for n in all_notifications if not n.read)
    
    # Apply pagination
    paginated = all_notifications[offset : offset + limit]
    
    return NotificationListResponse(
        notifications=paginated,
        total=total,
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Get unread count")
def get_unread_count(claims=Depends(verify_token)):
    """
    Get count of unread notifications for the current user.
    
    - Used for badge display
    - Lightweight query
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    coll = db.collection("notifications")
    unread_count = 0
    
    # Count unread notifications for this user
    for doc_id, data in _list_docs(coll):
        if data.get("user_id") == uid and not data.get("read", False):
            unread_count += 1
    
    return UnreadCountResponse(count=unread_count)


@router.patch("/{notification_id}/read", summary="Mark notification as read")
def mark_as_read(
    notification_id: str,
    claims=Depends(verify_token),
):
    """
    Mark a notification as read.
    
    - Only the notification owner can mark it as read
    - Updates the read field to True
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get notification document
    notif_ref = db.collection("notifications").document(notification_id)
    
    if hasattr(notif_ref, "get"):  # real Firestore
        notif_doc = notif_ref.get()
        if not notif_doc.exists:
            raise HTTPException(status_code=404, detail="Notification not found")
        notif_data = notif_doc.to_dict()
    elif hasattr(notif_ref, "_doc"):  # dev fake
        notif_data = notif_ref._doc
        if not notif_data:
            raise HTTPException(status_code=404, detail="Notification not found")
    else:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Verify ownership
    if notif_data.get("user_id") != uid:
        raise HTTPException(
            status_code=403,
            detail="You can only mark your own notifications as read"
        )
    
    # Update read status
    updates = {"read": True}
    
    if hasattr(notif_ref, "update"):
        notif_ref.update(updates)
    else:
        notif_ref.set({**notif_data, **updates})
    
    return {"id": notification_id, "read": True, "message": "Notification marked as read"}
