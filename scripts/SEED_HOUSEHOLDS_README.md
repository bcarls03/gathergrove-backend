# Test Households Seed Script

## Overview

This script creates **12 realistic test households** in Firestore for testing the Discovery page functionality.

## What It Creates

### 📊 Household Mix
- **7 Families with kids** (various age ranges)
- **1 Single parent** (with kids)
- **2 Couples** (no kids)
- **2 Singles** (no kids)

### 🏘️ Neighborhoods
- **Oak Ridge**: 5 households
- **Riverside**: 4 households
- **Hillside**: 3 households

### 👶 Kid Ages
- Ages 1-16 (various combinations)
- Some kids can babysit (age 10+)
- Different genders and configurations

### 🔗 Test Connections
Creates 4 pre-connected households for testing the "Connected" tab:
- Miller family
- Johnson family
- Garcia family
- Wilson family

## Usage

### Basic Seed (Add Households)
```bash
cd gathergrove-backend
GOOGLE_APPLICATION_CREDENTIALS=secrets/gathergrove-dev-firebase-adminsdk.json python3 scripts/seed_test_households.py
```

### Reset & Seed (Delete Old + Add New)
```bash
cd gathergrove-backend
GOOGLE_APPLICATION_CREDENTIALS=secrets/gathergrove-dev-firebase-adminsdk.json python3 scripts/seed_test_households.py --reset
```

### Quick Command (Copy-Paste)
```bash
cd /Users/briancarlberg/dev/gathergrove-backend && GOOGLE_APPLICATION_CREDENTIALS=secrets/gathergrove-dev-firebase-adminsdk.json python3 scripts/seed_test_households.py --reset
```

## Test Households

| Name | Type | Kids | Ages | Neighborhood | Can Message |
|------|------|------|------|--------------|-------------|
| **Miller** | Family | 2 | 7, 4 | Oak Ridge | ✅ Connected |
| **Johnson** | Family | 3 | 5, 3, 1 | Oak Ridge | ✅ Connected |
| **Garcia** | Family | 3 | 10, 8, 6 | Riverside | ✅ Connected |
| **Chen** | Family | 2 | 12, 9 | Riverside | ❌ |
| **Patel** | Family | 2 | 6, 4 | Hillside | ❌ |
| **Wilson** | Single Parent | 2 | 8, 5 | Oak Ridge | ✅ Connected |
| **Anderson** | Family | 2 | 16, 14 | Hillside | ❌ |
| **Taylor** | Couple | 0 | - | Riverside | ❌ |
| **Martinez** | Couple | 0 | - | Oak Ridge | ❌ |
| **Brown** | Single | 0 | - | Hillside | ❌ |
| **Lee** | Single | 0 | - | Riverside | ❌ |
| **Robinson** | Family | 3 | 15, 11, 6 | Oak Ridge | ❌ |

## Testing Discovery Features

### Test Nearby Tab
1. Open http://localhost:5174/discovery
2. Should see **12 households** in "Nearby" tab
3. **Connected households** show "✅ Connected" badge
4. **Non-connected households** show "Connect" button

### Test Connected Tab
1. Click "Connected" tab
2. Should see **4 households** (Miller, Johnson, Garcia, Wilson)
3. All should have "Message" button (blue solid)
4. Can click "Message" to open Messages tab

### Test Filters
1. Click "Family w/ Kids" chip → See 7 families + 1 single parent
2. Click "Couple" chip → See 2 couples
3. Click "Single" chip → See 2 singles
4. Adjust age slider (e.g., 4-8 years) → See families with kids in that range

### Test Household Selector
1. Click "Invite to Event" on any household
2. Navigate to `/compose/event`
3. Household should appear **checked** in selector
4. Can select additional households from the list

### Test Connections
1. Click "Connect" button on a non-connected household
2. Connection request should be sent
3. After acceptance, household moves to "Connected" tab
4. "Connect" button becomes "Message" button

## Modifying the Script

### Add More Households
Edit the `households` array in `seed_test_households()` function:

```python
{
    "id": "household-yourname-013",
    "uid": "user-yourname-013",
    "email": "your.name@example.com",
    "lastName": "YourName",
    "adultNames": ["FirstName", "Partner"],
    "neighborhood": "Oak Ridge",
    "householdType": "family_with_kids",
    "kids": [
        {**generate_birth_date(5), "sex": "boy", ...},
    ],
    # ... rest of fields
}
```

### Add More Connections
Edit the `connections` array in `seed_connections()` function:

```python
"connected_household_ids": [
    "user-miller-001",
    "user-johnson-002",
    # Add more UIDs here
]
```

### Change Neighborhoods
Replace neighborhood names throughout the script:
- "Oak Ridge"
- "Riverside"  
- "Hillside"

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'firebase_admin'"
**Solution:** Install dependencies:
```bash
cd gathergrove-backend
pip install -r requirements.txt
```

### Issue: "Firebase credentials not found"
**Solution:** Make sure to set `GOOGLE_APPLICATION_CREDENTIALS`:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=secrets/gathergrove-dev-firebase-adminsdk.json
```

### Issue: "Using in-memory fake Firestore"
**Solution:** The script will work but won't persist to real Firebase. Set credentials (see above).

### Issue: Households not showing in Discovery
**Solution:** 
1. Check backend is running: `http://localhost:8000/docs`
2. Check API returns data: `GET http://localhost:8000/households`
3. Check browser console for errors
4. Verify frontend is calling correct API endpoint

### Issue: Connected tab is empty
**Solution:** 
1. Check your dev UID matches the one in the script
2. Check localStorage: `localStorage.getItem('gg:uid')`
3. Update the script with your UID in `seed_connections()`

## Backend API Endpoints

After seeding, you can verify data via API:

### List All Households
```bash
curl http://localhost:8000/households
```

### Get Specific Household
```bash
curl http://localhost:8000/households/user-miller-001
```

### Get Connections
```bash
curl http://localhost:8000/connections
```

## Data Structure

### Household Document
```typescript
{
  id: "household-miller-001",
  uid: "user-miller-001",
  email: "sarah.miller@example.com",
  lastName: "Miller",
  adultNames: ["Sarah", "Mike"],
  neighborhood: "Oak Ridge",
  householdType: "family_with_kids",
  kids: [
    {
      birthMonth: 3,
      birthYear: 2017,
      sex: "girl",
      awayAtCollege: false,
      canBabysit: false
    }
  ],
  address: {
    street: "456 Oak Lane",
    city: "Portland",
    state: "OR",
    zip: "97201"
  },
  latitude: 45.5155,
  longitude: -122.6789,
  createdAt: "2026-01-21T...",
  updatedAt: "2026-01-21T..."
}
```

### Connection Document
```typescript
{
  uid: "dev-test-user-001",
  connected_household_ids: [
    "user-miller-001",
    "user-johnson-002",
    "user-garcia-003",
    "user-wilson-006"
  ]
}
```

## Next Steps

After seeding data:

1. ✅ **Start Backend**
   ```bash
   cd gathergrove-backend
   python -m uvicorn app.main:app --reload
   ```

2. ✅ **Start Frontend**
   ```bash
   cd gathergrove-frontend
   npm run dev
   ```

3. ✅ **Test Discovery Page**
   - Visit http://localhost:5174/discovery
   - Browse nearby households
   - Click Connect/Message buttons
   - Test filters
   - Try household selector

4. ✅ **Test Full Flow**
   - Discovery → Click "Invite to Event"
   - Compose → Select additional households
   - Create event → Verify invitations

## Related Scripts

- `reset-dev-db.sh` - Reset entire dev database
- `seed_test_groups.py` - Seed neighborhood groups
- `seed_happening_now.py` - Seed test events

## Files Modified

This script writes to:
- `users/` collection (Firestore)
- `connections/` collection (Firestore)

Safe to run multiple times with `--reset` flag.
