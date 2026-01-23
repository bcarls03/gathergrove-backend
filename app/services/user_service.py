# app/services/user_service.py
"""
User lookup and management services.

Used for:
- Finding users by phone number (for smart invitation routing)
- Checking if user exists before sending SMS
"""

from typing import Optional
from app.core.firebase import db


async def find_user_by_phone(phone_number: str) -> Optional[dict]:
    """
    Find a user by their phone number.
    
    Args:
        phone_number: E.164 format (e.g., +15551234567)
        
    Returns:
        User document if found, None otherwise
    """
    # Query users collection for matching phone
    users_ref = db.collection("users")
    
    # Check if it's fake Firestore (dev mode)
    if hasattr(users_ref, "_docs"):
        # Fake Firestore: iterate manually
        for user_id, user_data in users_ref._docs.items():
            if user_data.get("phoneNumber") == phone_number:
                return {
                    "id": user_id,
                    "household_id": user_data.get("householdId"),
                    **user_data
                }
        return None
    else:
        # Real Firestore: use query
        query = users_ref.where("phoneNumber", "==", phone_number).limit(1)
        results = list(query.stream())
        
        if results:
            user_doc = results[0]
            user_data = user_doc.to_dict()
            return {
                "id": user_doc.id,
                "household_id": user_data.get("householdId"),
                **user_data
            }
        return None


async def find_household_by_phone(phone_number: str) -> Optional[str]:
    """
    Find household ID for a given phone number.
    
    This is a convenience wrapper around find_user_by_phone
    that returns just the household_id.
    
    Returns:
        Household ID if found, None otherwise
    """
    user = await find_user_by_phone(phone_number)
    return user.get("household_id") if user else None
