#!/usr/bin/env python3
"""
Test Migration Idempotency

This script verifies that running the migration multiple times is safe
and won't create duplicate users.
"""

import sys
sys.path.insert(0, '/Users/briancarlberg/dev/gathergrove-backend')

from test_migration import create_test_fixtures
from migrate_to_individual_first import DataMigrator

print("=" * 80)
print("Idempotency Test: Running migration twice")
print("=" * 80)

# Create test fixtures
print("\nCreating test fixtures...")
create_test_fixtures()

# Run migration FIRST time
print("\n" + "=" * 80)
print("FIRST MIGRATION RUN")
print("=" * 80)
migrator1 = DataMigrator(dry_run=False)
migrator1.run()

# Run migration SECOND time (should skip existing users)
print("\n" + "=" * 80)
print("SECOND MIGRATION RUN (Testing Idempotency)")
print("=" * 80)
migrator2 = DataMigrator(dry_run=False)
migrator2.run()

# Check results
print("\n" + "=" * 80)
print("IDEMPOTENCY TEST RESULTS")
print("=" * 80)
print(f"First run:")
print(f"  - Users created: {migrator1.stats['users_created']}")
print(f"  - Users skipped: {migrator1.stats['users_skipped']}")
print(f"\nSecond run:")
print(f"  - Users created: {migrator2.stats['users_created']}")
print(f"  - Users skipped: {migrator2.stats['users_skipped']}")

# Verify idempotency
if migrator2.stats['users_created'] == 0 and migrator2.stats['users_skipped'] == 3:
    print("\n✅ IDEMPOTENCY TEST PASSED!")
    print("   Script safely detected existing users and skipped them.")
    sys.exit(0)
else:
    print("\n❌ IDEMPOTENCY TEST FAILED!")
    print("   Script created duplicate users on second run.")
    sys.exit(1)
