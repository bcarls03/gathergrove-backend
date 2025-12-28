# 🔌 API Examples: New Event Features

This document demonstrates the new event creation and invitation capabilities.

---

## 📍 Current API (Backward Compatible)

### Create Event - Legacy Format (Still Works)

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "X-Uid: sarah" \
  -H "X-Email: sarah@example.com" \
  -H "X-Admin: false" \
  -d '{
    "type": "future",
    "title": "Neighborhood BBQ",
    "details": "Bring your favorite dish!",
    "startAt": "2025-12-30T17:00:00Z",
    "endAt": "2025-12-30T21:00:00Z",
    "neighborhoods": ["Bay Hill", "Eagles Point"],
    "category": "neighborhood",
    "capacity": 30
  }'
```

**Response**:
```json
{
  "id": "evt_abc123",
  "type": "future",
  "title": "Neighborhood BBQ",
  "details": "Bring your favorite dish!",
  "startAt": "2025-12-30T17:00:00Z",
  "endAt": "2025-12-30T21:00:00Z",
  "neighborhoods": ["Bay Hill", "Eagles Point"],
  "category": "neighborhood",
  "capacity": 30,
  "hostUid": "sarah",
  "status": "active",
  "createdAt": "2025-12-27T10:30:00Z",
  "updatedAt": "2025-12-27T10:30:00Z"
}
```

---

## 🎯 New API: Smart Invitations

### Example 1: Specific People Only

**Use Case**: Birthday party - invite only my close friends

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "type": "future",
    "title": "Emma'\''s 8th Birthday Party",
    "details": "Pool party at our house! Pizza and cake provided.",
    "startAt": "2025-12-29T14:00:00Z",
    "endAt": "2025-12-29T17:00:00Z",
    "category": "playdate",
    "capacity": 15,
    "location": {
      "name": "Johnson'\''s House",
      "address": "123 Oak Street, Bay Hill",
      "coordinates": { "lat": 28.5383, "lng": -81.3792 }
    },
    "inviteCriteria": {
      "mode": "specific",
      "specificPeopleIds": [
        "person_smith",
        "person_davis", 
        "person_chen",
        "person_rodriguez"
      ]
    }
  }'
```

**Backend Processing**:
1. Creates event with `imageUrl: null` (generated async)
2. Generates 4 invitation records in `event_invites` collection
3. Sends push notifications to invited people
4. Starts async AI image generation
5. Returns immediately with event data

**Response**:
```json
{
  "id": "evt_xyz789",
  "title": "Emma's 8th Birthday Party",
  "imageUrl": null,
  "imageGenerating": true,
  "invitedCount": 4,
  "shareUrl": "/events/evt_xyz789/public?token=private_abc123",
  "status": "active",
  "...": "..."
}
```

---

### Example 2: Neighborhood + Age Range

**Use Case**: Playdate for families with kids 5-8 in Bay Hill

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "type": "future",
    "title": "Morning Playdate at Central Park",
    "details": "Let the kids burn off some energy! Bring snacks and water bottles.",
    "startAt": "2025-12-28T10:00:00Z",
    "endAt": "2025-12-28T12:00:00Z",
    "category": "playdate",
    "location": {
      "name": "Central Park Playground",
      "coordinates": { "lat": 28.5400, "lng": -81.3800 }
    },
    "inviteCriteria": {
      "mode": "criteria",
      "rules": [
        {
          "type": "neighborhood",
          "neighborhoods": ["Bay Hill"],
          "operator": "AND"
        },
        {
          "type": "age_range",
          "childAgeMin": 5,
          "childAgeMax": 8,
          "operator": "AND"
        }
      ]
    }
  }'
```

**Backend Processing**:
1. Evaluates criteria:
   - Finds all people in Bay Hill neighborhood
   - Filters to those with children aged 5-8
   - Result: 12 eligible people
2. Creates 12 invitation records
3. Sends notifications
4. Generates AI image with prompt: "A whimsical children's book illustration of kids playing at a playground, morning sunshine, playdate atmosphere..."

**Response**:
```json
{
  "id": "evt_playdate123",
  "title": "Morning Playdate at Central Park",
  "imageUrl": "https://storage.googleapis.com/.../evt_playdate123.png",
  "invitedCount": 12,
  "matchedCriteria": {
    "neighborhood": 18,
    "age_range": 15,
    "combined": 12
  },
  "status": "active"
}
```

---

### Example 3: HOA Members Within Walking Distance

**Use Case**: HOA meeting, invite only members within 1 mile

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "type": "future",
    "title": "Bay Hill HOA Quarterly Meeting",
    "details": "Discuss upcoming community improvements. Light refreshments provided.",
    "startAt": "2025-12-28T19:00:00Z",
    "endAt": "2025-12-28T21:00:00Z",
    "category": "neighborhood",
    "location": {
      "name": "Community Clubhouse",
      "address": "456 Clubhouse Dr, Bay Hill",
      "coordinates": { "lat": 28.5350, "lng": -81.3750 }
    },
    "inviteCriteria": {
      "mode": "criteria",
      "rules": [
        {
          "type": "group",
          "groupIds": ["group_bay_hill_hoa"],
          "operator": "AND"
        },
        {
          "type": "radius",
          "centerCoordinates": { "lat": 28.5350, "lng": -81.3750 },
          "radiusMiles": 1.0,
          "operator": "AND"
        }
      ]
    }
  }'
```

**Backend Processing**:
1. Looks up group `group_bay_hill_hoa`, finds 85 members
2. Filters to members with primaryAddress within 1 mile of clubhouse
3. Result: 42 eligible people
4. Creates invitation records and sends notifications

**Response**:
```json
{
  "id": "evt_hoa_meeting",
  "title": "Bay Hill HOA Quarterly Meeting",
  "imageUrl": "https://storage.googleapis.com/.../evt_hoa_meeting.png",
  "invitedCount": 42,
  "matchedCriteria": {
    "group": 85,
    "radius": 58,
    "combined": 42
  },
  "status": "active"
}
```

---

### Example 4: Public Event (Shareable with Anyone)

**Use Case**: Dog park meetup, share publicly

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "type": "future",
    "title": "Saturday Dog Park Social",
    "details": "Bring your furry friend! All breeds welcome. Water bowls provided.",
    "startAt": "2025-12-29T15:00:00Z",
    "endAt": "2025-12-29T17:00:00Z",
    "category": "pet",
    "location": {
      "name": "Bay Hill Dog Park",
      "coordinates": { "lat": 28.5420, "lng": -81.3780 }
    },
    "inviteCriteria": {
      "mode": "public",
      "allowNonMembers": true
    }
  }'
```

**Backend Processing**:
1. Creates event with public access
2. Generates shareable public token
3. No invitation records created (event is open to all)
4. Creates beautiful AI image with dog park theme

**Response**:
```json
{
  "id": "evt_dogpark",
  "title": "Saturday Dog Park Social",
  "imageUrl": "https://storage.googleapis.com/.../evt_dogpark.png",
  "shareUrl": "https://gathergrove.com/events/evt_dogpark/public?token=public_xyz789",
  "publicAccess": true,
  "invitedCount": null,
  "status": "active"
}
```

**Share Link**: Anyone can open the public URL and see a beautiful landing page, even if they don't have an account!

---

### Example 5: Complex Multi-Criteria

**Use Case**: Book club meetup - members who like reading AND live nearby

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "type": "future",
    "title": "Book Club: Project Hail Mary Discussion",
    "details": "Discussing Andy Weir'\''s latest novel. Spoilers ahead!",
    "startAt": "2026-01-05T19:30:00Z",
    "endAt": "2026-01-05T21:30:00Z",
    "category": "other",
    "capacity": 12,
    "location": {
      "name": "Sarah'\''s House",
      "coordinates": { "lat": 28.5383, "lng": -81.3792 }
    },
    "inviteCriteria": {
      "mode": "criteria",
      "rules": [
        {
          "type": "group",
          "groupIds": ["group_bay_hill_book_club"],
          "operator": "AND"
        },
        {
          "type": "interest",
          "requiredInterests": ["reading", "science_fiction"],
          "operator": "AND"
        },
        {
          "type": "radius",
          "centerCoordinates": { "lat": 28.5383, "lng": -81.3792 },
          "radiusMiles": 5.0,
          "operator": "AND"
        }
      ]
    }
  }'
```

**Backend Processing**:
1. Get book club members (24 people)
2. Filter to those with interests including "reading" AND "science_fiction" (18 remain)
3. Filter to those within 5 miles (11 remain)
4. Create 11 invitations

**Response**:
```json
{
  "id": "evt_bookclub",
  "title": "Book Club: Project Hail Mary Discussion",
  "imageUrl": "https://storage.googleapis.com/.../evt_bookclub.png",
  "invitedCount": 11,
  "capacity": 12,
  "matchedCriteria": {
    "group": 24,
    "interest": 18,
    "radius": 11
  },
  "status": "active"
}
```

---

## 📊 Query: Get My Invitations

### List Events I'm Invited To

```bash
curl -X GET "http://localhost:8000/events/invites/me" \
  -H "Authorization: Bearer <firebase_token>"
```

**Response**:
```json
{
  "invited": [
    {
      "event": {
        "id": "evt_playdate123",
        "title": "Morning Playdate at Central Park",
        "imageUrl": "https://...",
        "startAt": "2025-12-28T10:00:00Z",
        "category": "playdate"
      },
      "invitation": {
        "status": "pending",
        "invitedBy": "auto",
        "matchedCriteria": ["neighborhood", "age_range"],
        "createdAt": "2025-12-27T10:00:00Z"
      }
    },
    {
      "event": {
        "id": "evt_xyz789",
        "title": "Emma's 8th Birthday Party",
        "imageUrl": "https://...",
        "startAt": "2025-12-29T14:00:00Z",
        "category": "playdate"
      },
      "invitation": {
        "status": "pending",
        "invitedBy": "person_johnson",
        "matchedCriteria": [],
        "createdAt": "2025-12-27T11:00:00Z"
      }
    }
  ],
  "attending": [
    {
      "event": { "id": "evt_hoa_meeting", "..." },
      "rsvp": { "status": "going", "rsvpAt": "2025-12-26T15:00:00Z" }
    }
  ]
}
```

---

## 🔗 Share Event Endpoint

### Generate Shareable Link

```bash
curl -X POST http://localhost:8000/events/evt_playdate123/share \
  -H "Authorization: Bearer <firebase_token>"
```

**Response**:
```json
{
  "shareUrl": "https://gathergrove.com/events/evt_playdate123/public?token=share_abc123xyz",
  "accessToken": "share_abc123xyz",
  "expiresAt": null,
  "message": "Share this link with anyone, even if they're not on GatherGrove!"
}
```

### View Public Event Landing Page

```bash
curl "https://gathergrove.com/events/evt_playdate123/public?token=share_abc123xyz"
```

Returns beautiful HTML page with:
- Full-width AI-generated hero image
- Event details (title, time, location)
- Host information
- RSVP buttons (prompts signup if not logged in)
- Share buttons (copy link, SMS, email)

---

## 🎨 AI Image Generation

### Regenerate Event Image

```bash
curl -X POST http://localhost:8000/events/evt_playdate123/regenerate-image \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "style": "whimsical",
    "customPrompt": "Focus on a sunny day with lots of greenery"
  }'
```

**Response**:
```json
{
  "status": "generating",
  "estimatedSeconds": 15,
  "message": "Image is being generated. Refresh event to see updated imageUrl."
}
```

**After 15 seconds**, GET the event again:

```bash
curl http://localhost:8000/events/evt_playdate123 \
  -H "Authorization: Bearer <firebase_token>"
```

**Response** (includes new image):
```json
{
  "id": "evt_playdate123",
  "imageUrl": "https://storage.googleapis.com/.../evt_playdate123_v2.png",
  "imageGeneratedAt": "2025-12-27T10:45:23Z",
  "...": "..."
}
```

---

## 📈 Analytics: Event Performance

### Get Event Analytics

```bash
curl "http://localhost:8000/events/evt_dogpark/analytics" \
  -H "Authorization: Bearer <firebase_token>"
```

**Response**:
```json
{
  "eventId": "evt_dogpark",
  "invitations": {
    "sent": 0,
    "viewed": 0,
    "pending": 0
  },
  "shares": {
    "totalShares": 12,
    "uniqueViewers": 87,
    "totalViews": 143,
    "signupsGenerated": 4,
    "conversionRate": 0.046
  },
  "rsvps": {
    "going": 23,
    "maybe": 8,
    "declined": 2
  },
  "shareBreakdown": [
    {
      "sharedBy": "person_maria",
      "sharedVia": "link",
      "views": 45,
      "signups": 2,
      "sharedAt": "2025-12-27T12:00:00Z"
    },
    {
      "sharedBy": "person_john",
      "sharedVia": "sms",
      "views": 23,
      "signups": 1,
      "sharedAt": "2025-12-27T14:30:00Z"
    }
  ]
}
```

**Insights**: Maria's share link drove 2 signups! 🎉

---

## 🔄 Migration: Legacy to New Format

### Old Format (Still Accepted)

```json
{
  "type": "future",
  "title": "BBQ",
  "neighborhoods": ["Bay Hill"],
  "startAt": "2025-12-30T17:00:00Z"
}
```

### Automatically Converted To

```json
{
  "type": "future",
  "title": "BBQ",
  "startAt": "2025-12-30T17:00:00Z",
  "inviteCriteria": {
    "mode": "criteria",
    "rules": [
      {
        "type": "neighborhood",
        "neighborhoods": ["Bay Hill"],
        "operator": "AND"
      }
    ]
  }
}
```

**Backward Compatibility**: Old clients keep working, new clients get new features!

---

## 🚀 Summary: What's New

### ✅ For Event Hosts

1. **Smart targeting**: "Anyone in my HOA with kids 5-10 within 3 miles"
2. **Beautiful images**: AI-generated landing page images
3. **Viral sharing**: Share events publicly, track who joins
4. **Analytics**: See how your event is performing

### ✅ For Attendees

1. **Personalized invites**: Only see relevant events
2. **Clear expectations**: Know why you were invited ("matched: neighborhood + age range")
3. **Easy sharing**: Invite friends who aren't on the platform yet
4. **Beautiful discovery**: Gorgeous event images

### ✅ For Developers

1. **Extensible architecture**: Add new criteria types easily
2. **Backward compatible**: Old code keeps working
3. **Well-tested**: Comprehensive test coverage
4. **Clear migration path**: Phase-by-phase rollout

---

**Next Steps**: 
1. Review proposal: `docs/extensibility-proposal.md`
2. Follow implementation: `docs/phase1-implementation-checklist.md`
3. Visualize architecture: `docs/architecture-diagram.md`

**Ready to build the future of neighborhood events! 🎉**
