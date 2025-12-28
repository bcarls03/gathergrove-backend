# 🛠️ Implementation Checklist: Phase 1 Foundation

**Goal**: Create new data structures without breaking existing system

---

## 📋 Week 1: New Collections & Models

### Day 1-2: Create Pydantic Models

**File**: `app/models/people.py` (NEW)

```python
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class PrimaryAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    coordinates: Optional[Coordinates] = None

class ChildReference(BaseModel):
    id: str
    relationship: str = "child"  # or "dependent"

class NotificationPreferences(BaseModel):
    pushEnabled: bool = True
    emailEnabled: bool = True
    eventInvites: bool = True

class PersonIn(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    displayName: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    profileImageUrl: Optional[str] = None
    primaryAddress: Optional[PrimaryAddress] = None
    birthYear: Optional[int] = Field(None, ge=1900, le=2025)
    interests: List[str] = Field(default_factory=list, max_items=20)
    visibility: str = Field(default="neighbors", pattern="^(public|neighbors|private)$")
    notificationPreferences: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )

class PersonOut(PersonIn):
    id: str
    uid: Optional[str] = None
    email: Optional[str] = None
    familyIds: List[str] = Field(default_factory=list)
    groupIds: List[str] = Field(default_factory=list)
    children: List[ChildReference] = Field(default_factory=list)
    createdAt: datetime
    updatedAt: datetime
    lastActive: Optional[datetime] = None
```

**File**: `app/models/groups.py` (NEW)

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

GroupType = Literal["family", "hoa", "club", "neighborhood", "custom"]
Visibility = Literal["public", "private", "members"]
JoinPolicy = Literal["open", "request", "invite_only"]

class GeoBoundary(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]  # GeoJSON polygon format

class ChildInfo(BaseModel):
    personId: str
    birthYear: int
    birthMonth: int = 1
    sex: Optional[Literal["M", "F"]] = None

class GroupIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: GroupType = "custom"
    description: Optional[str] = Field(None, max_length=500)
    neighborhood: Optional[str] = None
    geoBoundary: Optional[GeoBoundary] = None
    centerCoordinates: Optional[dict] = None  # {lat, lng}
    visibility: Visibility = "private"
    joinPolicy: JoinPolicy = "invite_only"
    
    # Family-specific (when type="family")
    householdType: Optional[str] = None
    adultNames: List[str] = Field(default_factory=list)
    children: List[ChildInfo] = Field(default_factory=list)

class GroupOut(GroupIn):
    id: str
    memberIds: List[str] = Field(default_factory=list)
    adminIds: List[str] = Field(default_factory=list)
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
```

---

### Day 3-4: Migration Scripts

**File**: `scripts/migrate_to_new_schema.py` (NEW)

```python
#!/usr/bin/env python3
"""
Migration script: Households → Groups, Users → People

Run with: python scripts/migrate_to_new_schema.py --dry-run
          python scripts/migrate_to_new_schema.py --execute
"""
import sys
from datetime import datetime, timezone
from app.core.firebase import db

def migrate_households_to_groups(dry_run=True):
    """Migrate households collection to groups with type=family."""
    print("🏘️  Migrating households → groups...")
    
    households_ref = db.collection("households")
    groups_ref = db.collection("groups")
    
    count = 0
    for doc in households_ref.stream():
        household = doc.to_dict()
        
        # Build group document
        group = {
            "id": doc.id,
            "name": f"{household.get('lastName', 'Unknown')} Family",
            "type": "family",
            "description": None,
            "neighborhood": household.get("neighborhood"),
            "visibility": "private",
            "joinPolicy": "invite_only",
            
            # Family-specific fields (preserve existing data)
            "householdType": household.get("householdType") or household.get("type"),
            "adultNames": household.get("adultNames", []),
            "children": household.get("children", []),
            
            # Membership (initially just the household owner)
            "memberIds": [household.get("uid", doc.id)],
            "adminIds": [household.get("uid", doc.id)],
            
            "createdBy": household.get("uid", doc.id),
            "createdAt": household.get("createdAt") or datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        if not dry_run:
            groups_ref.document(doc.id).set(group)
        
        print(f"  ✓ {group['name']} (id: {doc.id})")
        count += 1
    
    print(f"✅ Migrated {count} households → groups\n")
    return count

def migrate_users_to_people(dry_run=True):
    """Create people records from existing users."""
    print("👤 Migrating users → people...")
    
    users_ref = db.collection("users")
    people_ref = db.collection("people")
    households_ref = db.collection("households")
    
    count = 0
    for doc in users_ref.stream():
        user = doc.to_dict()
        
        # Find associated household (if exists)
        household_id = None
        household_snap = households_ref.document(doc.id).get()
        if household_snap.exists:
            household_id = doc.id
        
        # Parse name into firstName/lastName
        full_name = user.get("name", "")
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else "Unknown"
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Build person document
        person = {
            "id": doc.id,
            "uid": doc.id,
            "email": user.get("email"),
            "firstName": first_name,
            "lastName": last_name,
            "displayName": full_name,
            "bio": None,
            "profileImageUrl": None,
            
            # Memberships
            "familyIds": [household_id] if household_id else [],
            "groupIds": [household_id] if household_id else [],  # Family is also a group
            
            # Location (will be filled in later by user)
            "primaryAddress": None,
            
            # Demographics
            "birthYear": None,
            "interests": [],
            "children": [],
            
            # Preferences
            "visibility": "neighbors",
            "notificationPreferences": {
                "pushEnabled": True,
                "emailEnabled": True,
                "eventInvites": True
            },
            
            "createdAt": user.get("createdAt") or datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "lastActive": None
        }
        
        if not dry_run:
            people_ref.document(doc.id).set(person)
        
        print(f"  ✓ {full_name} (id: {doc.id})")
        count += 1
    
    print(f"✅ Migrated {count} users → people\n")
    return count

def update_event_host_references(dry_run=True):
    """Update events to reference personId instead of uid (no-op for now, just validation)."""
    print("🎉 Validating event host references...")
    
    events_ref = db.collection("events")
    count = 0
    
    for doc in events_ref.stream():
        event = doc.to_dict()
        host_uid = event.get("hostUid")
        
        # For now, personId = uid, so no migration needed
        # Just validate that host exists in people collection
        if host_uid:
            person_snap = db.collection("people").document(host_uid).get()
            if not person_snap.exists:
                print(f"  ⚠️  Event {doc.id}: host {host_uid} not found in people collection")
            else:
                count += 1
    
    print(f"✅ Validated {count} event hosts\n")
    return count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate GatherGrove data to new schema")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without executing")
    parser.add_argument("--execute", action="store_true", help="Actually perform the migration")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("❌ Must specify --dry-run or --execute")
        sys.exit(1)
    
    dry_run = args.dry_run
    
    print("="*60)
    print("  GatherGrove Schema Migration")
    print("  Mode:", "DRY RUN (no changes)" if dry_run else "EXECUTE (live changes)")
    print("="*60)
    print()
    
    try:
        households_count = migrate_households_to_groups(dry_run)
        users_count = migrate_users_to_people(dry_run)
        events_count = update_event_host_references(dry_run)
        
        print("="*60)
        print("✅ Migration complete!")
        print(f"  • {households_count} households → groups")
        print(f"  • {users_count} users → people")
        print(f"  • {events_count} events validated")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
```

**Usage**:
```bash
# Preview changes
python scripts/migrate_to_new_schema.py --dry-run

# Execute migration
python scripts/migrate_to_new_schema.py --execute
```

---

### Day 5: Firestore Indexes

**File**: `firestore.indexes.json` (UPDATE)

```json
{
  "indexes": [
    {
      "collectionGroup": "people",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "groupIds", "arrayConfig": "CONTAINS" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "people",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "familyIds", "arrayConfig": "CONTAINS" },
        { "fieldPath": "lastName", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "groups",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "type", "order": "ASCENDING" },
        { "fieldPath": "neighborhood", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "groups",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "memberIds", "arrayConfig": "CONTAINS" },
        { "fieldPath": "name", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "event_invites",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "eventId", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "event_invites",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "personId", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

**Deploy indexes**:
```bash
firebase deploy --only firestore:indexes
```

---

## 📋 Week 2: Dual-Write Logic & Validation

### Day 6-7: Add Dual-Write Helpers

**File**: `app/services/dual_write.py` (NEW)

```python
"""
Dual-write helpers for migration period.
Writes to both old and new collections to maintain consistency.
"""
from typing import Dict, Any
from app.core.firebase import db
from datetime import datetime, timezone

def create_household_and_group(data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    """
    During migration: write to both households and groups.
    
    Args:
        data: Household/group data
        uid: User/person ID
    
    Returns:
        The created group document
    """
    now = datetime.now(timezone.utc)
    
    # Write to old households collection (for backward compatibility)
    household_data = {
        "id": uid,
        "uid": uid,
        "lastName": data.get("lastName", ""),
        "type": data.get("type") or data.get("householdType"),
        "neighborhood": data.get("neighborhood"),
        "adultNames": data.get("adultNames", []),
        "children": data.get("children", []),
        "createdAt": data.get("createdAt", now),
        "updatedAt": now
    }
    db.collection("households").document(uid).set(household_data, merge=True)
    
    # Write to new groups collection
    group_data = {
        "id": uid,
        "name": f"{data.get('lastName', 'Unknown')} Family",
        "type": "family",
        "description": None,
        "neighborhood": data.get("neighborhood"),
        "householdType": data.get("householdType") or data.get("type"),
        "adultNames": data.get("adultNames", []),
        "children": data.get("children", []),
        "memberIds": [uid],
        "adminIds": [uid],
        "visibility": "private",
        "joinPolicy": "invite_only",
        "createdBy": uid,
        "createdAt": data.get("createdAt", now),
        "updatedAt": now
    }
    db.collection("groups").document(uid).set(group_data, merge=True)
    
    return group_data

def create_user_and_person(data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    """
    During migration: write to both users and people.
    
    Args:
        data: User/person data
        uid: User/person ID
    
    Returns:
        The created person document
    """
    now = datetime.now(timezone.utc)
    
    # Write to old users collection (for backward compatibility)
    user_data = {
        "uid": uid,
        "email": data.get("email"),
        "name": data.get("name") or f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
        "isAdmin": data.get("isAdmin", False),
        "favorites": data.get("favorites", []),
        "createdAt": data.get("createdAt", now),
        "updatedAt": now
    }
    db.collection("users").document(uid).set(user_data, merge=True)
    
    # Write to new people collection
    full_name = user_data["name"]
    name_parts = full_name.split(" ", 1)
    
    person_data = {
        "id": uid,
        "uid": uid,
        "email": data.get("email"),
        "firstName": data.get("firstName") or name_parts[0] if name_parts else "Unknown",
        "lastName": data.get("lastName") or (name_parts[1] if len(name_parts) > 1 else ""),
        "displayName": full_name,
        "bio": data.get("bio"),
        "profileImageUrl": data.get("profileImageUrl"),
        "familyIds": data.get("familyIds", []),
        "groupIds": data.get("groupIds", []),
        "primaryAddress": data.get("primaryAddress"),
        "birthYear": data.get("birthYear"),
        "interests": data.get("interests", []),
        "children": data.get("children", []),
        "visibility": data.get("visibility", "neighbors"),
        "notificationPreferences": data.get("notificationPreferences", {
            "pushEnabled": True,
            "emailEnabled": True,
            "eventInvites": True
        }),
        "createdAt": data.get("createdAt", now),
        "updatedAt": now,
        "lastActive": None
    }
    db.collection("people").document(uid).set(person_data, merge=True)
    
    return person_data
```

### Day 8-10: Update Existing Routes

**File**: `app/routes/households.py` (MODIFY)

```python
# Add at top:
from app.services.dual_write import create_household_and_group

# Modify upsert_my_household:
@router.post("/households", summary="Create/update my household (by uid)")
def upsert_my_household(
    payload: Dict[str, Any] = Body(...),
    claims=Depends(verify_token),
):
    """
    Create/update the household for the currently-auth'd user.
    NOW: Dual-writes to both households and groups collections.
    """
    uid = claims.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing uid in auth claims")
    
    # Use dual-write helper
    group_data = create_household_and_group(payload, uid)
    
    # Return in old format for backward compatibility
    household_data = {
        "id": uid,
        "lastName": payload.get("lastName"),
        "type": group_data.get("householdType"),
        "neighborhood": group_data.get("neighborhood"),
        "adultNames": group_data.get("adultNames"),
        "children": group_data.get("children"),
        "createdAt": group_data.get("createdAt"),
        "updatedAt": group_data.get("updatedAt")
    }
    
    return _jsonify(household_data)
```

**File**: `app/routes/users.py` (MODIFY)

```python
# Add at top:
from app.services.dual_write import create_user_and_person

# Modify upsert_my_user:
@router.post("/users", summary="Create or update my user (owner-only upsert)")
def upsert_my_user(body: UserIn, claims=Depends(verify_token)):
    """
    Create/update user for currently-auth'd user.
    NOW: Dual-writes to both users and people collections.
    """
    uid = claims["uid"]
    
    data = {
        "name": body.name,
        "email": claims.get("email"),
        "isAdmin": body.isAdmin if claims.get("admin") else False
    }
    
    # Use dual-write helper
    person_data = create_user_and_person(data, uid)
    
    # Return in old format for backward compatibility
    user_data = {
        "id": uid,
        "uid": uid,
        "name": body.name,
        "email": claims.get("email"),
        "isAdmin": person_data.get("isAdmin", False),
        "createdAt": person_data.get("createdAt"),
        "updatedAt": person_data.get("updatedAt")
    }
    
    return _jsonify(user_data)
```

---

## ✅ Phase 1 Validation Checklist

Before moving to Phase 2, verify:

- [ ] **Collections created**:
  - [ ] `people` collection exists in Firestore
  - [ ] `groups` collection exists in Firestore
  - [ ] Indexes deployed successfully

- [ ] **Migration successful**:
  - [ ] All households migrated to groups
  - [ ] All users migrated to people
  - [ ] Data integrity verified (counts match)

- [ ] **Dual-write working**:
  - [ ] New household creates both household + group
  - [ ] New user creates both user + person
  - [ ] Updates propagate to both collections

- [ ] **Tests passing**:
  - [ ] Existing test suite passes 100%
  - [ ] No breaking changes detected
  - [ ] Can read from both old and new collections

- [ ] **Backward compatibility**:
  - [ ] Old API endpoints work unchanged
  - [ ] Frontend can use old format
  - [ ] No client code changes required yet

---

## 🚨 Rollback Plan

If Phase 1 migration causes issues:

1. **Stop dual-write**: Comment out `create_household_and_group` and `create_user_and_person` calls
2. **Revert to old endpoints**: Remove changes to `households.py` and `users.py`
3. **Delete new collections**: `people` and `groups` can be deleted (data preserved in `households` and `users`)
4. **No data loss**: Old collections remain untouched and functional

---

## 📊 Success Metrics for Phase 1

- ✅ 100% of existing tests pass
- ✅ Zero downtime during migration
- ✅ Data parity: `len(households) == len(groups where type=family)`
- ✅ Data parity: `len(users) == len(people)`
- ✅ All existing API calls return correct data
- ✅ Performance: No noticeable latency increase (<50ms overhead for dual-write)

---

## 🎯 Next: Phase 2 Preparation

Once Phase 1 is complete and stable for 1 week:

1. **Set up OpenAI API** for DALL-E 3
2. **Design event image templates** (category-specific styles)
3. **Create `inviteCriteria` Pydantic model**
4. **Write invitation matcher service** (start with simple neighborhood matching)
5. **Create public event landing page HTML template**

See `docs/extensibility-proposal.md` for full Phase 2 details.

---

**Phase 1 Goal**: Solid foundation with zero breaking changes ✅
