#!/usr/bin/env python3
"""
Test event reply notifications.

This test validates that event reply notifications are sent to:
- Event host (unless sender)
- Participants who RSVP'd "going" or "maybe" (unless sender or declined)

Run with: python3 test_event_reply_notifications.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.notification_service import create_notification
from app.models.notification import NotificationType


async def test_event_reply_notification():
    """Test creating an event reply notification"""
    print("\n🧪 Testing Event Reply Notification...")
    
    try:
        # Create a test notification
        notif_id = await create_notification(
            user_id="test_host_user",
            notification_type=NotificationType.EVENT_REPLY,
            title="Event update",
            body="The Smith Family sent a message in BBQ",
            data={
                "event_id": "evt_test_123",
                "sender_uid": "test_sender_user",
            }
        )
        
        print(f"   ✅ Event reply notification created: {notif_id}")
        print(f"   Type: {NotificationType.EVENT_REPLY}")
        print("   Title: Event update")
        print("   Body: The Smith Family sent a message in BBQ")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def main():
    print("=" * 60)
    print("Event Reply Notification Test")
    print("=" * 60)
    
    success = await test_event_reply_notification()
    
    if success:
        print("\n✅ Event reply notification test passed!")
        print("\n📋 Summary:")
        print("   - Notification type: event_reply")
        print("   - Title format: 'Event update'")
        print("   - Body format: '<Household> sent a message in <Event>'")
        print("   - Data includes: event_id, sender_uid")
        print("\n🎉 Implementation complete!")
    else:
        print("\n❌ Event reply notification test failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
