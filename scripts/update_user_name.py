#!/usr/bin/env python3
"""Update OAuth user's name in Firestore"""

import os
import sys

# Set environment before importing Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(__file__), "..", "secrets", "gathergrove-dev-firebase-adminsdk.json"
)
# NOT using emulator - using real Firestore dev database
# os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

from google.cloud import firestore

def main():
    db = firestore.Client()
    
    # OAuth user UID
    uid = "HxqCeMn9fKLpS4T3LhAzjcZqbtdO"
    
    ref = db.collection("users").document(uid)
    snap = ref.get()
    
    if not snap.exists:
        print(f"❌ User {uid} not found!")
        sys.exit(1)
    
    print(f"📄 Current data:")
    current = snap.to_dict()
    print(f"  first_name: {current.get('first_name')}")
    print(f"  last_name: {current.get('last_name')}")
    print(f"  email: {current.get('email')}")
    
    # Update with actual name
    ref.update({
        "first_name": "Brian",
        "last_name": "Carlberg"
    })
    
    print(f"\n✅ Updated user {uid}")
    
    # Verify
    updated_snap = ref.get()
    updated = updated_snap.to_dict()
    print(f"  first_name: {updated.get('first_name')}")
    print(f"  last_name: {updated.get('last_name')}")

if __name__ == "__main__":
    main()
