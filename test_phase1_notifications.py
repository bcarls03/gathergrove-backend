#!/usr/bin/env python3
"""
Test script for Phase 1 notification implementation.
Tests the notification model, service, and endpoints.
"""

import asyncio
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_UID = "test_user_123"

def test_health():
    """Test server is running"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✅ Server health check passed")

def test_unread_count_endpoint():
    """Test GET /api/notifications/unread-count"""
    response = requests.get(f"{BASE_URL}/api/notifications/unread-count")
    # In dev mode with fake auth, this might return 200
    # In production with real Firebase auth, would return 401/403
    assert response.status_code in [200, 401, 403]
    print("✅ Unread count endpoint exists")

def test_list_notifications_endpoint():
    """Test GET /api/notifications"""
    response = requests.get(f"{BASE_URL}/api/notifications")
    # In dev mode with fake auth, this might return 200
    # In production with real Firebase auth, would return 401/403
    assert response.status_code in [200, 401, 403]
    if response.status_code == 200:
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert "unread_count" in data
    print("✅ List notifications endpoint exists")

def test_notification_service():
    """Test notification service functions"""
    from app.services.notification_service import create_notification
    from app.models.notification import NotificationType
    
    # Test creating a notification
    async def create_test_notification():
        notif_id = await create_notification(
            user_id=TEST_UID,
            notification_type=NotificationType.EVENT_INVITE,
            title="Test Event Invitation",
            body="This is a test notification",
            data={"event_id": "test_event_123"}
        )
        assert notif_id is not None
        assert len(notif_id) > 0
        return notif_id
    
    notif_id = asyncio.run(create_test_notification())
    print(f"✅ Notification service created notification: {notif_id}")

def test_notification_models():
    """Test notification Pydantic models"""
    from app.models.notification import (
        NotificationCreate,
        NotificationResponse,
        NotificationType,
    )
    
    # Test NotificationCreate
    create_req = NotificationCreate(
        user_id=TEST_UID,
        type=NotificationType.EVENT_INVITE,
        title="Test Title",
        body="Test Body",
        data={"test_key": "test_value"}
    )
    assert create_req.user_id == TEST_UID
    print("✅ NotificationCreate model works")
    
    # Test NotificationResponse
    response = NotificationResponse(
        id="test_id",
        user_id=TEST_UID,
        type=NotificationType.RSVP,
        title="Test Title",
        body="Test Body",
        data={},
        read=False,
        created_at="2026-03-11T10:00:00Z"
    )
    assert response.read is False
    print("✅ NotificationResponse model works")

if __name__ == "__main__":
    print("🧪 Testing Phase 1 Notification Implementation\n")
    
    try:
        test_health()
        test_unread_count_endpoint()
        test_list_notifications_endpoint()
        test_notification_models()
        test_notification_service()
        
        print("\n✅ All Phase 1 tests passed!")
        print("\n📝 Phase 1 Complete:")
        print("   - Notification data model ✅")
        print("   - Notification service ✅")
        print("   - Notification endpoints ✅")
        print("   - Router registered ✅")
        print("\n🚀 Ready for Phase 2: Wire up triggers")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
