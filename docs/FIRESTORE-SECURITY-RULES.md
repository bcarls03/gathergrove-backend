# Firestore Security Rules

This directory contains Firestore security rules for the GatherGrove backend, implementing individual-first architecture with privacy controls and viral loop features.

## Files

- **`firestore.rules`**: Security rules for all Firestore collections
- **`firestore.indexes.json`**: Composite indexes for optimized queries
- **`firebase.json`**: Firebase project configuration

## Architecture

### Individual-First Design
- Users are independent entities (not coupled to households)
- Households are optional groupings for multiple adults
- Events use `host_user_id` (individual) instead of `hostUid` (household)

### Visibility Controls
- **Users**: `private`, `neighbors`, `public`
  - `private`: Only the user can see their profile
  - `neighbors`: Same neighborhood users can discover
  - `public`: All authenticated users can discover
  
- **Events**: `private`, `link_only`, `public`
  - `private`: Only the host can see
  - `link_only`: Anyone with the shareable link can see
  - `public`: All users can discover (viral loop)

## Security Rules Summary

### Users Collection (`/users/{userId}`)
- ✅ Users can create, read, update, delete their own profile
- ✅ Public/neighbor visibility enables discovery
- ✅ Private profiles are only visible to the owner

### Households Collection (`/households/{householdId}`)
- ✅ Any authenticated user can create a household
- ✅ Household members (in `member_uids` array) can read/write
- ✅ Members can delete their household

### Events Collection (`/events/{eventId}`)
- ✅ Any authenticated user can create an event
- ✅ Host (via `host_user_id`) can update/delete their event
- ✅ Public events: Anyone authenticated can read (viral loop)
- ✅ Link-only events: Anyone with link can read
- ✅ Private events: Host only
- ✅ **UNAUTHENTICATED access for public events** (viral loop)

### Event Attendees Collection (`/event_attendees/{attendeeId}`)
- ✅ Users can CRUD their own RSVPs
- ✅ Event hosts can read all RSVPs for their events

### Other Collections
- **Notifications**: Users can read/update/delete their own
- **Messages**: Users can read messages where they're sender/recipient
- **Favorites**: Users can CRUD their own favorites

## Testing Security Rules

### Option 1: Firebase Emulator (Local Testing)

1. **Install Firebase CLI** (if not already installed):
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase**:
   ```bash
   firebase login
   ```

3. **Initialize Firebase project** (one-time setup):
   ```bash
   firebase init
   # Select: Firestore, Emulators
   # Choose existing project or create new
   ```

4. **Start emulators**:
   ```bash
   firebase emulators:start
   ```
   
   This will start:
   - Firestore Emulator: `http://localhost:8080`
   - Auth Emulator: `http://localhost:9099`
   - Emulator UI: `http://localhost:4000`

5. **Run tests against emulator**:
   ```bash
   # Set environment variables to use emulator
   export FIRESTORE_EMULATOR_HOST="localhost:8080"
   export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099"
   
   # Run pytest
   python3 -m pytest tests/ -v
   ```

### Option 2: Firebase Console (Manual Testing)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Firestore Database** → **Rules**
4. Use the **Rules Playground** to test:
   - Simulate authenticated users
   - Test read/write operations
   - Verify visibility controls

### Option 3: Production Testing (After Deployment)

1. **Deploy rules to production**:
   ```bash
   firebase deploy --only firestore:rules
   ```

2. **Test with real data**:
   - Create test users with different visibility settings
   - Create events with different visibility levels
   - Test RSVP access controls
   - Verify unauthenticated access to public events

## Deployment

### Deploy Security Rules

```bash
# Deploy only Firestore rules
firebase deploy --only firestore:rules

# Deploy rules and indexes
firebase deploy --only firestore

# Deploy everything (rules, indexes, functions, etc.)
firebase deploy
```

### Verify Deployment

```bash
# Check deployed rules
firebase firestore:rules:get

# Check deployed indexes
firebase firestore:indexes
```

## Testing Checklist

### User Profile Rules
- [ ] User can create their own profile
- [ ] User can read their own profile
- [ ] User can update their own profile
- [ ] User can delete their own profile
- [ ] Public user is discoverable by all authenticated users
- [ ] Neighbor user is discoverable by same-neighborhood users
- [ ] Private user is NOT discoverable by others

### Household Rules
- [ ] User can create a household
- [ ] Household members can read the household
- [ ] Household members can update the household
- [ ] Household members can delete the household
- [ ] Non-members CANNOT read/write household

### Event Rules
- [ ] User can create an event
- [ ] Host can read their own event
- [ ] Host can update their own event
- [ ] Host can delete their own event
- [ ] Public event is readable by all authenticated users
- [ ] Public event is readable by UNAUTHENTICATED users (viral loop)
- [ ] Link-only event is readable by authenticated users
- [ ] Private event is readable ONLY by host
- [ ] Non-host CANNOT update/delete event

### RSVP Rules
- [ ] User can create their own RSVP
- [ ] User can read their own RSVP
- [ ] User can update their own RSVP
- [ ] User can delete their own RSVP
- [ ] Event host can read all RSVPs for their event
- [ ] Non-host CANNOT read other users' RSVPs

## Common Issues

### Issue: Rules not taking effect
**Solution**: Rules may take 1-2 minutes to propagate. Clear browser cache or wait.

### Issue: "Missing or insufficient permissions"
**Solution**: Check:
- User is authenticated (`request.auth != null`)
- User has correct permissions (owner, member, etc.)
- Visibility settings are correct

### Issue: Emulator rules not updating
**Solution**: 
- Stop emulator (`Ctrl+C`)
- Delete emulator data: `firebase emulators:start --clear-cache`
- Restart emulator

### Issue: Indexes not deployed
**Solution**:
```bash
firebase deploy --only firestore:indexes
```

## Key Features

### ✅ Individual-First Architecture
- Users are independent (not coupled to households)
- Households are optional groupings
- Events use individual hosts (`host_user_id`)

### ✅ Privacy Controls
- User visibility: private, neighbors, public
- Event visibility: private, link_only, public
- Granular read access based on visibility

### ✅ Viral Loop Support
- Public events have unauthenticated read access
- Shareable links enable non-user discovery
- Link-only events for semi-private sharing

### ✅ Backward Compatibility
- Old `hostUid` field still works
- Existing data can coexist with new structure
- Migration path is smooth

## Security Best Practices

1. **Never trust client input**: All validation in rules
2. **Principle of least privilege**: Grant minimum required access
3. **Test thoroughly**: Use emulator before production
4. **Monitor access**: Use Firebase Analytics to track
5. **Regular audits**: Review rules quarterly
6. **Document changes**: Update this doc when rules change

## References

- [Firestore Security Rules Documentation](https://firebase.google.com/docs/firestore/security/get-started)
- [Security Rules Testing](https://firebase.google.com/docs/rules/unit-tests)
- [Firebase Emulator Suite](https://firebase.google.com/docs/emulator-suite)
