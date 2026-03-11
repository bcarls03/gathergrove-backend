# app/services/notification_service.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

from app.core.firebase import db

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Get current UTC timestamp as ISO string"""
    return datetime.now(timezone.utc).isoformat()


def _list_docs(coll):
    """List documents from Firestore collection (works with real and fake DB)"""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a notification in Firestore.
    
    Args:
        user_id: The UID of the user to notify
        notification_type: One of NotificationType constants (event_invite, rsvp, connection_request)
        title: Notification title (e.g., "Sarah invited you to a BBQ")
        body: Notification body (e.g., "Saturday at 3pm")
        data: Additional data (event_id, household_id, connection_id, etc.)
    
    Returns:
        notification_id: The ID of the created notification
    """
    if data is None:
        data = {}
    
    now = _now_iso()
    notification_data = {
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "body": body,
        "data": data,
        "read": False,
        "created_at": now,
    }
    
    # Add to Firestore
    coll = db.collection("notifications")
    new_ref = coll.document()
    new_ref.set(notification_data)
    notification_id = new_ref.id
    
    logger.info(f"Created notification {notification_id} for user {user_id}: {notification_type}")
    return notification_id


async def send_push_notification(
    user_id: str,
    notification_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a push notification via FCM.
    
    Args:
        user_id: The UID of the user to notify
        notification_id: The notification ID (for navigation)
        title: Push notification title
        body: Push notification body
        data: Additional data payload
    
    Returns:
        success: True if sent successfully, False otherwise
    """
    # TODO: Implement FCM sending logic using firebase_admin.messaging
    # For now, just log (will be implemented in Phase 3)
    logger.info(f"[STUB] Would send push to user {user_id}: {title}")
    return True


async def create_and_send(
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    check_preferences: bool = True
) -> Optional[str]:
    """
    Create a notification and send push notification.
    
    Args:
        user_id: The UID of the user to notify
        notification_type: One of NotificationType constants
        title: Notification title
        body: Notification body
        data: Additional data
        check_preferences: If True, check user's notifications_enabled preference
    
    Returns:
        notification_id: The ID of the created notification, or None if skipped
    """
    if data is None:
        data = {}
    
    # Check user preferences (if enabled)
    if check_preferences:
        users_coll = db.collection("users")
        for doc_id, user_data in _list_docs(users_coll):
            if user_data.get("uid") == user_id:
                notifications_enabled = user_data.get("notifications_enabled", True)
                if not notifications_enabled:
                    logger.info(f"Skipping notification for user {user_id} (notifications disabled)")
                    return None
                break
    
    # Create notification in Firestore
    notification_id = await create_notification(user_id, notification_type, title, body, data)
    
    # Add notification_id to data payload for push
    push_data = {**data, "notification_id": notification_id, "type": notification_type}
    
    # Send push notification (stub for now)
    await send_push_notification(user_id, notification_id, title, body, push_data)
    
    return notification_id
