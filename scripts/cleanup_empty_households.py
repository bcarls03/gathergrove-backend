#!/usr/bin/env python3
"""
Clean up old test households that have no identifying information.

This removes households that have:
- No lastName
- No adultNames (or empty array)
- Were created during early testing

Usage:
    python scripts/cleanup_empty_households.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

def cleanup_empty_households():
    """Delete households with no identifying information"""
    
    print("🧹 Cleaning up empty/incomplete households...")
    
    households_ref = db.collection("households")
    deleted = 0
    skipped = 0
    
    # List of known empty household IDs from the query
    empty_household_ids = [
        "household_22bf90e16a5b",
        "household_24391521e86f",
        "household_3c08f3b4726f",
        "household_882d6a5890db",
        "household_b3101920dd0c",
        "household_b344c5e7cff2",
        "household_d736938dc2e7",
        "household_da0d1fd0af65",
        "household_e27601d2d7ce"
    ]
    
    for doc_id in empty_household_ids:
        try:
            doc_ref = households_ref.document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                last_name = data.get('lastName')
                adult_names = data.get('adultNames', [])
                
                # Only delete if truly empty
                if not last_name and (not adult_names or len(adult_names) == 0):
                    doc_ref.delete()
                    deleted += 1
                    print(f"  ✗ Deleted {doc_id}")
                else:
                    skipped += 1
                    print(f"  ✓ Skipped {doc_id} (has some data)")
            else:
                print(f"  ⚠ {doc_id} not found (already deleted?)")
        except Exception as e:
            print(f"  ❌ Error deleting {doc_id}: {e}")
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Deleted: {deleted} households")
    print(f"   Skipped: {skipped} households")
    
    return deleted

if __name__ == "__main__":
    deleted_count = cleanup_empty_households()
    
    print("\n💡 Next steps:")
    print("  1. Refresh the Discovery page: http://localhost:5174/discovery")
    print("  2. You should now see only households with proper names")
    print("  3. The 12 test households (Miller, Garcia, etc.) should all be visible")
