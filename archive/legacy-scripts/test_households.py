#!/usr/bin/env python3
"""Quick test to check households in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.firebase import db

# Check households collection
households_ref = db.collection("households")
docs = list(households_ref.stream())

print(f"=== HOUSEHOLDS DATABASE CHECK ===")
print(f"Total households found: {len(docs)}")
print()

if len(docs) == 0:
    print("❌ NO HOUSEHOLDS IN DATABASE!")
    print()
    print("To fix this, run:")
    print("  python3 scripts/seed_test_households.py")
else:
    print("✅ Households exist:")
    for doc in docs[:10]:
        data = doc.to_dict()
        print(f"  - {doc.id}: {data.get('lastName', 'Unknown')}")
