#!/usr/bin/env python3
"""
Data Migration Script: Household-First → Individual-First Architecture

This script transforms the existing Firestore data from the old household-first
architecture (where users and households were 1:1 coupled) to the new individual-first
architecture (where users are independent and households are optional groupings).

CRITICAL: This is a ONE-WAY migration. Backup your data before running!

Usage:
    # Dry-run mode (read-only, shows what would change):
    python3 scripts/migrate_to_individual_first.py --dry-run

    # Production run (writes to Firestore):
    python3 scripts/migrate_to_individual_first.py --production

    # Development run (uses in-memory fake Firestore):
    python3 scripts/migrate_to_individual_first.py --dev

Author: Brian Carlberg
Date: January 3, 2026
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, '/Users/briancarlberg/dev/gathergrove-backend')

from app.core.firebase import db


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def now_iso() -> str:
    """Return current timestamp as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def list_docs(collection):
    """List all documents in a Firestore collection (works with real + fake)."""
    if hasattr(collection, "stream"):  # Real Firestore
        return [(doc.id, doc.to_dict() or {}) for doc in collection.stream()]
    if hasattr(collection, "_docs"):  # Fake Firestore (dev mode)
        return list(collection._docs.items())
    return []


def parse_adult_name(name: str) -> Tuple[str, str]:
    """
    Parse adult name into first_name and last_name.
    
    Examples:
        "Alice Smith" → ("Alice", "Smith")
        "Bob" → ("Bob", "")
        "Mary Jane Watson" → ("Mary Jane", "Watson")
    """
    parts = name.strip().split()
    if len(parts) == 0:
        return ("Unknown", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        # Last part is last name, rest is first name
        return (" ".join(parts[:-1]), parts[-1])


# ============================================================================
# MIGRATION LOGIC
# ============================================================================

class DataMigrator:
    """Handles migration from household-first to individual-first architecture."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.stats = {
            "households_read": 0,
            "users_created": 0,
            "users_skipped": 0,
            "households_created": 0,
            "old_households_deleted": 0,
            "events_updated": 0,
            "event_attendees_updated": 0,
            "errors": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def pre_flight_check(self):
        """
        Pre-flight validation to ensure database is in expected state.
        Checks for existing users/ collection and warns if migration already ran.
        """
        self.log("=" * 80)
        self.log("PRE-FLIGHT CHECK: Validating database state")
        self.log("=" * 80)
        
        users_coll = db.collection("users")
        existing_users = list_docs(users_coll)
        
        if existing_users:
            self.log(f"⚠️  WARNING: users/ collection already exists!", "WARNING")
            self.log(f"   Found {len(existing_users)} existing users", "WARNING")
            self.log(f"   This suggests migration may have already run.", "WARNING")
            
            if not self.dry_run:
                self.log("")
                response = input("   Continue anyway? This may create duplicates. (yes/no): ")
                if response.lower() != "yes":
                    self.log("❌ Migration aborted by user", "ERROR")
                    sys.exit(1)
                self.log("   ⚠️  Proceeding with migration (user confirmed)", "WARNING")
        else:
            self.log("✅ users/ collection is empty - safe to proceed", "SUCCESS")
        
        self.log("")
    
    def migrate_households_to_users_and_households(self):
        """
        Step 1: Read old households collection and create:
        1. UserProfile docs in users/{uid} collection
        2. New Household docs in households/{new_id} collection
        3. Delete old household docs (clean start)
        """
        self.log("=" * 80)
        self.log("STEP 1: Migrating households → users + households")
        self.log("=" * 80)
        
        households_coll = db.collection("households")
        users_coll = db.collection("users")
        new_households_coll = db.collection("households")
        
        # Track old household doc IDs to delete after migration
        old_household_ids = []
        
        for doc_id, data in list_docs(households_coll):
            self.stats["households_read"] += 1
            
            try:
                # OLD STRUCTURE:
                # households/{uid} → {
                #   uid: "user123",
                #   email: "alice@example.com",
                #   adultNames: ["Alice Smith", "Bob Smith"],
                #   lastName: "Smith",
                #   householdType: "Family w/ Kids",
                #   kids: [...],
                #   ...
                # }
                
                uid = data.get("uid", doc_id)
                email = data.get("email", "")
                adult_names = data.get("adultNames", [])
                
                if not uid:
                    self.log(f"⚠️  Skipping household {doc_id}: No uid", "WARNING")
                    self.stats["errors"].append(f"Household {doc_id}: No uid")
                    continue
                
                if not adult_names or len(adult_names) == 0:
                    self.log(f"⚠️  Skipping household {doc_id}: No adult names", "WARNING")
                    self.stats["errors"].append(f"Household {doc_id}: No adult names")
                    continue
                
                # Check if user already exists (idempotency)
                existing_user = None
                if not self.dry_run:
                    try:
                        existing_user_doc = users_coll.document(uid).get()
                        if existing_user_doc.exists:
                            existing_user = existing_user_doc.to_dict()
                    except:
                        pass  # Fake Firestore doesn't support .get().exists
                
                if existing_user:
                    self.log(f"⏭️  User {uid} already exists, skipping household {doc_id}", "INFO")
                    self.log(f"   Existing user: {existing_user.get('first_name')} {existing_user.get('last_name')}", "INFO")
                    self.stats["users_skipped"] += 1
                    continue
                
                # Parse first adult name (primary user)
                primary_adult_name = adult_names[0]
                first_name, last_name = parse_adult_name(primary_adult_name)
                
                # Generate new household ID
                household_id = uuid.uuid4().hex
                
                # NEW STRUCTURE 1: UserProfile
                user_profile = {
                    "uid": uid,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name or data.get("lastName", ""),
                    "profile_photo_url": data.get("photoURL") or data.get("profilePhotoUrl") or None,
                    "bio": data.get("bio") or None,
                    "address": data.get("address") or None,
                    "lat": data.get("lat") or None,
                    "lng": data.get("lng") or None,
                    "neighborhood": data.get("neighborhood") or None,
                    "discovery_opt_in": data.get("discoveryOptIn", True),
                    "visibility": "neighbors",  # Default to neighbors for existing users
                    "household_id": household_id,  # Link to household
                    "created_at": data.get("createdAt") or now_iso(),
                    "updated_at": now_iso()
                }
                
                # NEW STRUCTURE 2: Household
                household = {
                    "id": household_id,
                    "name": f"The {last_name or 'Household'}s" if last_name else "Household",
                    "member_uids": [uid],  # Initially just the primary user
                    "household_type": data.get("householdType") or data.get("type") or None,
                    "kids": data.get("kids") or [],
                    "address": data.get("address") or None,
                    "lat": data.get("lat") or None,
                    "lng": data.get("lng") or None,
                    "neighborhood": data.get("neighborhood") or None,
                    "created_at": data.get("createdAt") or now_iso(),
                    "updated_at": now_iso()
                }
                
                # Log what we're about to do
                self.log(f"📝 Household {doc_id} (uid: {uid})")
                self.log(f"   → User: {first_name} {last_name} ({email})")
                self.log(f"   → Household: {household['name']} (id: {household_id})")
                
                # Track old household doc ID for deletion
                old_household_ids.append(doc_id)
                
                if self.dry_run:
                    self.log("   [DRY-RUN] Would create user profile", "INFO")
                    self.log("   [DRY-RUN] Would create household", "INFO")
                    self.log(f"   [DRY-RUN] Would delete old household: households/{doc_id}", "INFO")
                else:
                    # Write UserProfile
                    users_coll.document(uid).set(user_profile, merge=False)
                    self.stats["users_created"] += 1
                    self.log(f"   ✅ Created user profile: users/{uid}", "SUCCESS")
                    
                    # Write Household
                    new_households_coll.document(household_id).set(household, merge=False)
                    self.stats["households_created"] += 1
                    self.log(f"   ✅ Created household: households/{household_id}", "SUCCESS")
                
            except Exception as e:
                self.log(f"❌ Error migrating household {doc_id}: {e}", "ERROR")
                self.stats["errors"].append(f"Household {doc_id}: {str(e)}")
        
        # Delete old household documents (clean start)
        if old_household_ids:
            self.log(f"\n�️  Deleting {len(old_household_ids)} old household documents...")
            for doc_id in old_household_ids:
                if self.dry_run:
                    self.log(f"   [DRY-RUN] Would delete: households/{doc_id}", "INFO")
                else:
                    try:
                        households_coll.document(doc_id).delete()
                        self.log(f"   ✅ Deleted old household: households/{doc_id}", "SUCCESS")
                    except Exception as e:
                        self.log(f"   ⚠️  Could not delete households/{doc_id}: {e}", "WARNING")
        
        self.log(f"\n�📊 Households processed: {self.stats['households_read']}")
        self.log(f"   Users created: {self.stats['users_created']}")
        self.log(f"   Households created: {self.stats['households_created']}")
        self.log(f"   Old households deleted: {len(old_household_ids)}")
    
    def migrate_events_hostUid_to_host_user_id(self):
        """
        Step 2: Update all events to use host_user_id instead of hostUid.
        Also add visibility field (default to 'private' for existing events).
        """
        self.log("\n" + "=" * 80)
        self.log("STEP 2: Migrating events: hostUid → host_user_id")
        self.log("=" * 80)
        
        events_coll = db.collection("events")
        
        for event_id, data in list_docs(events_coll):
            try:
                # Check if already migrated
                if "host_user_id" in data:
                    self.log(f"⏭️  Event {event_id} already has host_user_id, skipping", "INFO")
                    continue
                
                # Get old hostUid
                host_uid = data.get("hostUid")
                if not host_uid:
                    self.log(f"⚠️  Event {event_id} has no hostUid, skipping", "WARNING")
                    self.stats["errors"].append(f"Event {event_id}: No hostUid")
                    continue
                
                # Prepare update
                updates = {
                    "host_user_id": host_uid,
                    "visibility": "private",  # Default existing events to private
                    "shareable_link": None,  # Private events don't have shareable links
                    "updatedAt": now_iso()
                }
                
                self.log(f"📝 Event {event_id}: {data.get('title', 'Untitled')}")
                self.log(f"   hostUid: {host_uid} → host_user_id: {host_uid}")
                self.log(f"   visibility: private (default for existing events)")
                
                if self.dry_run:
                    self.log("   [DRY-RUN] Would update event", "INFO")
                else:
                    # Update event
                    events_coll.document(event_id).set(updates, merge=True)
                    self.stats["events_updated"] += 1
                    self.log(f"   ✅ Updated event: events/{event_id}", "SUCCESS")
                
            except Exception as e:
                self.log(f"❌ Error migrating event {event_id}: {e}", "ERROR")
                self.stats["errors"].append(f"Event {event_id}: {str(e)}")
        
        self.log(f"\n📊 Events updated: {self.stats['events_updated']}")
    
    def verify_migration(self):
        """
        Step 3: Verify data integrity after migration.
        """
        self.log("\n" + "=" * 80)
        self.log("STEP 3: Verifying migration")
        self.log("=" * 80)
        
        users_coll = db.collection("users")
        households_coll = db.collection("households")
        events_coll = db.collection("events")
        
        # Count documents
        user_count = len(list_docs(users_coll))
        household_count = len(list_docs(households_coll))
        event_count = len(list_docs(events_coll))
        
        self.log(f"📊 Final counts:")
        self.log(f"   Users: {user_count}")
        self.log(f"   Households: {household_count}")
        self.log(f"   Events: {event_count}")
        
        # Check for events without host_user_id
        events_missing_host = 0
        for event_id, data in list_docs(events_coll):
            if "host_user_id" not in data and "hostUid" not in data:
                events_missing_host += 1
                self.log(f"⚠️  Event {event_id} missing both host_user_id and hostUid", "WARNING")
        
        if events_missing_host > 0:
            self.log(f"❌ {events_missing_host} events missing host identifier", "ERROR")
        else:
            self.log(f"✅ All events have host identifier", "SUCCESS")
        
        # Check for users without household_id
        users_without_household = 0
        for user_id, data in list_docs(users_coll):
            if "household_id" not in data or not data["household_id"]:
                users_without_household += 1
        
        if users_without_household > 0:
            self.log(f"ℹ️  {users_without_household} users without household (this is OK for singles/couples)", "INFO")
    
    def run(self):
        """Execute the full migration."""
        self.log("=" * 80)
        self.log("GatherGrove Data Migration: Household-First → Individual-First")
        self.log("=" * 80)
        self.log(f"Mode: {'DRY-RUN (no writes)' if self.dry_run else 'PRODUCTION (writes to Firestore)'}")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 80)
        
        try:
            # Pre-flight check
            self.pre_flight_check()
            
            # Step 1: Migrate households to users + households
            self.migrate_households_to_users_and_households()
            
            # Step 2: Migrate events hostUid → host_user_id
            self.migrate_events_hostUid_to_host_user_id()
            
            # Step 3: Verify migration
            self.verify_migration()
            
            # Final summary
            self.log("\n" + "=" * 80)
            self.log("MIGRATION COMPLETE")
            self.log("=" * 80)
            self.log(f"📊 Final Statistics:")
            self.log(f"   Households read: {self.stats['households_read']}")
            self.log(f"   Users created: {self.stats['users_created']}")
            self.log(f"   Users skipped (already exist): {self.stats['users_skipped']}")
            self.log(f"   Households created: {self.stats['households_created']}")
            self.log(f"   Old households deleted: {self.stats['old_households_deleted']}")
            self.log(f"   Events updated: {self.stats['events_updated']}")
            self.log(f"   Errors: {len(self.stats['errors'])}")
            
            if self.stats['errors']:
                self.log("\n❌ Errors encountered:")
                for error in self.stats['errors']:
                    self.log(f"   - {error}", "ERROR")
            else:
                self.log("\n✅ No errors encountered!", "SUCCESS")
            
            if self.dry_run:
                self.log("\n🔍 This was a DRY-RUN. No data was modified.", "INFO")
                self.log("   Run with --production to apply changes.", "INFO")
            
        except Exception as e:
            self.log(f"\n❌ FATAL ERROR: {e}", "ERROR")
            raise


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate GatherGrove data from household-first to individual-first architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (shows what would change, no writes):
  python3 scripts/migrate_to_individual_first.py --dry-run
  
  # Production run (writes to Firestore):
  python3 scripts/migrate_to_individual_first.py --production
  
  # Development run (uses in-memory fake Firestore):
  python3 scripts/migrate_to_individual_first.py --dev
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode: read data and show what would change, but don't write"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Production mode: actually write changes to Firestore (DANGEROUS!)"
    )
    
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode: use in-memory fake Firestore"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.production and args.dry_run:
        print("❌ ERROR: Cannot use both --production and --dry-run")
        sys.exit(1)
    
    if not args.production and not args.dry_run and not args.dev:
        print("❌ ERROR: Must specify one of: --dry-run, --production, or --dev")
        print("   Use --dry-run first to see what would change!")
        sys.exit(1)
    
    # Confirm production run
    if args.production:
        print("\n⚠️  WARNING: You are about to run a PRODUCTION migration!")
        print("   This will modify your Firestore database.")
        print("   Make sure you have a backup before proceeding.")
        response = input("\nType 'yes' to continue: ")
        if response.lower() != "yes":
            print("❌ Migration cancelled.")
            sys.exit(0)
    
    # Run migration
    dry_run = not args.production
    migrator = DataMigrator(dry_run=dry_run)
    migrator.run()


if __name__ == "__main__":
    main()
