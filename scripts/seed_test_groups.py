#!/usr/bin/env python3
"""
Seed test neighborhood groups for auto-join testing.

This creates sample apartment complexes, HOAs, and radius-based neighborhoods
to test the auto-join functionality.

Usage:
    python scripts/seed_test_groups.py
"""

import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

def seed_test_groups():
    """Create test neighborhood groups in Firestore"""
    
    print("🌱 Seeding test neighborhood groups...")
    
    groups = [
        # 1. Riverside Apartments (Apartment Complex - Address Match)
        {
            "id": "riverside-apt-001",
            "type": "neighborhood",
            "name": "Riverside Apartments",
            "members": [
                {
                    "user_id": "admin-user-001",
                    "role": "admin",
                    "joined_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "metadata": {
                "neighborhood_type": "apartment_complex",
                "building_address": "123 River Street",
                "city": "Portland",
                "state": "OR",
                "units_total": 200,
                "amenities": ["gym", "pool", "parking"]
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        
        # 2. Pearl District HOA (Radius-based)
        {
            "id": "pearl-district-002",
            "type": "neighborhood",
            "name": "Pearl District Neighborhood",
            "members": [
                {
                    "user_id": "admin-user-002",
                    "role": "admin",
                    "joined_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "metadata": {
                "neighborhood_type": "open_neighborhood",
                "center_lat": 45.5250,
                "center_lng": -122.6800,
                "radius_miles": 0.5,  # 0.5 mile radius
                "description": "Pearl District residents"
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        
        # 3. Oakwood Hills HOA (Subdivision - Name Match)
        {
            "id": "oakwood-hoa-003",
            "type": "neighborhood",
            "name": "Oakwood Hills HOA",
            "members": [
                {
                    "user_id": "admin-user-003",
                    "role": "admin",
                    "joined_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "metadata": {
                "neighborhood_type": "hoa",
                "subdivision_name": "oakwood hills",
                "hoa_fees": "$150/month",
                "amenities": ["pool", "clubhouse"],
                "center_lat": 45.5300,
                "center_lng": -122.6900,
                "radius_miles": 0.3
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        
        # 4. Downtown Lofts (Another apartment complex)
        {
            "id": "downtown-lofts-004",
            "type": "neighborhood",
            "name": "Downtown Lofts",
            "members": [],
            "metadata": {
                "neighborhood_type": "apartment_complex",
                "building_address": "456 Main Street",
                "city": "Portland",
                "state": "OR",
                "units_total": 150,
                "amenities": ["gym", "rooftop deck"]
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Add to Firestore
    for group in groups:
        group_id = group["id"]
        try:
            db.collection("groups").document(group_id).set(group)
            print(f"✅ Created: {group['name']} ({group['metadata']['neighborhood_type']})")
        except Exception as e:
            print(f"❌ Error creating {group['name']}: {e}")
    
    print(f"\n✨ Seeded {len(groups)} test neighborhood groups!")
    print("\n📍 Test addresses that will auto-join:")
    print("   • 123 River Street, Apt 4B → Riverside Apartments + Pearl District")
    print("   • 456 Main Street, Unit 301 → Downtown Lofts")
    print("   • 789 Oakwood Hills Dr → Oakwood Hills HOA")
    print("   • Any address near (45.5250, -122.6800) → Pearl District")


if __name__ == "__main__":
    seed_test_groups()
