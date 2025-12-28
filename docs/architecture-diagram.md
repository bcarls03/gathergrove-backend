# 🏗️ GatherGrove Architecture Diagram

## Current State (Before Migration)

```
┌─────────────────────────────────────────────────────────────┐
│                         CURRENT STATE                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    Users     │         │  Households  │         │    Events    │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ uid (PK)     │────1:1──│ id (PK)      │         │ id (PK)      │
│ email        │         │ lastName     │         │ title        │
│ name         │         │ type         │         │ type         │
│ isAdmin      │         │ neighborhood │         │ startAt      │
│ favorites[]  │─────────│ adultNames[] │         │ endAt        │
│ createdAt    │         │ children[]   │         │ neighborhoods│
│ updatedAt    │         │ createdAt    │         │ hostUid ────►│
└──────────────┘         └──────────────┘         │ capacity     │
                                                   │ category     │
                                                   │ status       │
                                                   └──────────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────┐
                                              │ Event_Attendees  │
                                              ├──────────────────┤
                                              │ id (composite)   │
                                              │ eventId          │
                                              │ uid              │
                                              │ status           │
                                              │ rsvpAt           │
                                              └──────────────────┘

LIMITATIONS:
❌ Person = Household (1:1 rigid coupling)
❌ No groups beyond households
❌ Simple neighborhood-only targeting
❌ No event images
❌ No shareability (auth-only)
```

---

## Future State (After Migration)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FUTURE STATE                                  │
│                    EVENTS-FIRST ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                         👤 PEOPLE LAYER                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐                                                  │
│  │     People       │          Core entity = PERSON                    │
│  ├──────────────────┤                                                  │
│  │ id (PK)          │          One person can:                         │
│  │ uid (optional)   │          • Belong to multiple families           │
│  │ firstName        │          • Join multiple groups                  │
│  │ lastName         │          • Have rich profile                     │
│  │ email            │          • Own location data                     │
│  │ familyIds[]   ───┼────┐                                            │
│  │ groupIds[]    ───┼───┐│                                            │
│  │ primaryAddress   │   ││                                            │
│  │  └─coordinates   │   ││    ┌──────────────────┐                   │
│  │    (lat, lng)    │   ││    │  Profiles        │                   │
│  │ interests[]      │   ││    ├──────────────────┤                   │
│  │ birthYear        │   ││    │ personId (FK)    │                   │
│  │ visibility       │   ││    │ visibility       │                   │
│  │ createdAt        │   ││    │ bio              │                   │
│  └──────────────────┘   ││    │ preferences      │                   │
│                          ││    │ notifSettings    │                   │
│                          ││    └──────────────────┘                   │
└──────────────────────────┼┼───────────────────────────────────────────┘
                           ││
                           │└─────────┐
                           │          │
┌──────────────────────────┼──────────┼───────────────────────────────────┐
│                          ▼          ▼   🏘️ GROUPS LAYER                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                          Groups                                   │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ id (PK)                                                           │ │
│  │ name                  Flexible group types:                       │ │
│  │ type ─────────────────► • Family (replaces households)           │ │
│  │ description           ► • HOA                                     │ │
│  │ neighborhood          ► • Club (book club, running group)         │ │
│  │ memberIds[]           ► • Neighborhood                            │ │
│  │ adminIds[]            ► • Custom (dog owners, etc.)               │ │
│  │ geoBoundary                                                       │ │
│  │ centerCoordinates     Group-level metadata:                       │ │
│  │ visibility            • Geographic boundaries                     │ │
│  │ joinPolicy            • Membership rules                          │ │
│  │ createdAt             • Privacy settings                          │ │
│  │                                                                   │ │
│  │ // Family-specific (type="family"):                              │ │
│  │ householdType         For backward compatibility with             │ │
│  │ adultNames[]          current household model                     │ │
│  │ children[]                                                        │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Groups can be
                                    │ used in invite
                                    │ criteria
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        🎉 EVENTS LAYER (Premium)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                         Events                                    │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │ id (PK)                                                           │ │
│  │ title                 ⭐ Premium Features:                         │ │
│  │ details               • AI-generated landing image                │ │
│  │ imageUrl       ───────► DALL-E 3 / Stable Diffusion              │ │
│  │ imagePrompt           • Consistent brand style                    │ │
│  │ imageStyle            • Public shareable pages                    │ │
│  │                       • Sophisticated targeting                   │ │
│  │ type (now/future)                                                 │ │
│  │ startAt, endAt                                                    │ │
│  │ category                                                          │ │
│  │ location {                                                        │ │
│  │   name                                                            │ │
│  │   coordinates                                                     │ │
│  │ }                                                                 │ │
│  │                                                                   │ │
│  │ hostId (FK→People)    🎯 Invitation Criteria (NEW):               │ │
│  │ status                                                            │ │
│  │                       ┌────────────────────────────────────────┐ │ │
│  │ inviteCriteria {      │                                        │ │ │
│  │   mode: "specific" | "criteria" | "public"                     │ │ │
│  │                       │                                        │ │ │
│  │   specificPeopleIds[] │  Direct invites                        │ │ │
│  │   specificGroupIds[]  │  Group invites                         │ │ │
│  │                       │                                        │ │ │
│  │   rules[] {           │  Smart targeting:                      │ │ │
│  │     type: "neighborhood" | "group" | "radius" |                │ │ │
│  │           "age_range" | "interest" | "custom"                  │ │ │
│  │                       │                                        │ │ │
│  │     // Examples:      │                                        │ │ │
│  │     neighborhoods[]   │  ► "Bay Hill neighborhood"             │ │ │
│  │     groupIds[]        │  ► "Bay Hill HOA members"              │ │ │
│  │     centerCoords      │  ► "Within 5 miles of my house"        │ │ │
│  │     radiusMiles       │  ► "Parents with kids 5-10"            │ │ │
│  │     childAgeMin/Max   │  ► "Dog owners who like hiking"        │ │ │
│  │     interests[]       │                                        │ │ │
│  │                       │  Combine with AND/OR                   │ │ │
│  │     operator: "AND" | "OR"                                     │ │ │
│  │   }                   │                                        │ │ │
│  │                       └────────────────────────────────────────┘ │ │
│  │   publicAccessToken   For shareable URLs                          │ │
│  │   allowNonMembers                                                 │ │
│  │ }                                                                 │ │
│  │                                                                   │ │
│  │ shareUrl              🔗 Public landing page                      │ │
│  │ shareCount            📊 Viral tracking                           │ │
│  │ viewCount                                                         │ │
│  │                                                                   │ │
│  │ createdAt, updatedAt                                              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                               │                                        │
│        ┌──────────────────────┼───────────────────┐                   │
│        ▼                      ▼                   ▼                   │
│  ┌──────────┐         ┌──────────────┐    ┌──────────────┐           │
│  │  Event   │         │    Event     │    │    Event     │           │
│  │ Invites  │         │  Attendees   │    │   Shares     │           │
│  ├──────────┤         ├──────────────┤    ├──────────────┤           │
│  │ eventId  │         │ eventId      │    │ eventId      │           │
│  │ personId │         │ personId     │    │ sharedBy     │           │
│  │ invitedBy│         │ status       │    │ accessToken  │           │
│  │ method   │         │ (going/      │    │ viewCount    │           │
│  │ status   │         │  maybe/      │    │ signups      │           │
│  │ viewedAt │         │  declined)   │    │ sharedVia    │           │
│  └──────────┘         │ rsvpAt       │    │ createdAt    │           │
│                       └──────────────┘    └──────────────┘           │
│  Explicit invitation  RSVP tracking       Viral growth                │
│  tracking             (existing)          tracking (NEW)              │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

NEW CAPABILITIES:
✅ People belong to multiple groups
✅ Complex invite targeting (neighborhood + age + radius + groups)
✅ AI-generated event images
✅ Public shareable event pages (viral growth)
✅ Explicit invitation tracking
✅ Rich analytics & insights
```

---

## Data Flow: Creating an Event with Smart Invitations

```
┌────────────────────────────────────────────────────────────────────────┐
│                       EVENT CREATION FLOW                              │
└────────────────────────────────────────────────────────────────────────┘

1️⃣ User Creates Event
   ↓
   POST /events
   {
     "title": "Neighborhood BBQ",
     "category": "neighborhood",
     "inviteCriteria": {
       "mode": "criteria",
       "rules": [
         { "type": "group", "groupIds": ["bay-hill-hoa"] },
         { "type": "age_range", "childAgeMin": 5, "childAgeMax": 12 },
         { "type": "radius", "centerCoordinates": {...}, "radiusMiles": 3 }
       ]
     }
   }
   ↓

2️⃣ Backend Processes
   ↓
   ┌─────────────────────────────────────────┐
   │ a) Create Event Document                │
   │    └─ Generate event ID                 │
   │                                          │
   │ b) Generate AI Image (async)            │
   │    └─ Extract keywords from title       │
   │    └─ Build DALL-E prompt               │
   │    └─ Call OpenAI API                   │
   │    └─ Upload to Firebase Storage        │
   │    └─ Update event.imageUrl             │
   │                                          │
   │ c) Evaluate Invite Criteria             │
   │    └─ Get all people in bay-hill-hoa    │
   │    └─ Filter: has kids age 5-12         │
   │    └─ Filter: within 3 mi radius        │
   │    └─ Apply AND logic                   │
   │    └─ Result: 23 eligible people        │
   │                                          │
   │ d) Create Invitation Records            │
   │    └─ For each of 23 people:            │
   │        • Create event_invites doc       │
   │        • status = "pending"             │
   │        • matchedCriteria = [rules]      │
   │                                          │
   │ e) Send Notifications                   │
   │    └─ Push notifications                │
   │    └─ Email digests (optional)          │
   └─────────────────────────────────────────┘
   ↓

3️⃣ Response to User
   ↓
   {
     "id": "evt123",
     "title": "Neighborhood BBQ",
     "imageUrl": "https://storage.../evt123.png",
     "invitedCount": 23,
     "shareUrl": "/events/evt123/public?token=abc..."
   }
   ↓

4️⃣ Users Receive Invites
   ↓
   • Push notification: "You're invited to Neighborhood BBQ!"
   • In-app: Shows in "My Invites" tab
   • Can RSVP, view details, share with others
```

---

## Invitation Matching Engine

```
┌────────────────────────────────────────────────────────────────────────┐
│                   INVITATION CRITERIA EVALUATOR                        │
└────────────────────────────────────────────────────────────────────────┘

Input: Event with inviteCriteria
   ↓
   
MODE ROUTER
   ↓
   ├─ mode="specific" ──► Direct list of person/group IDs
   │                      └─ Return immediately
   │
   ├─ mode="public" ────► Everyone (no filtering)
   │                      └─ Create public share token
   │
   └─ mode="criteria" ──► Smart matching (below)
                          ↓

CRITERIA EVALUATION PIPELINE
   ↓
   Start with: all_people = [person1, person2, ..., personN]
   ↓
   
   For each rule in rules[]:
      ↓
      ┌────────────────────────────────────────┐
      │ Rule Type Handlers                     │
      ├────────────────────────────────────────┤
      │                                        │
      │ "neighborhood"                         │
      │   └─ Filter: person.primaryAddress     │
      │              .neighborhood in list     │
      │                                        │
      │ "group"                                │
      │   └─ Filter: person.groupIds           │
      │              intersects groupIds       │
      │                                        │
      │ "radius"                               │
      │   └─ Filter: distance(                 │
      │              person.coordinates,       │
      │              event.coordinates         │
      │            ) <= radiusMiles            │
      │                                        │
      │ "age_range"                            │
      │   └─ Filter: person has children with  │
      │              age in [min, max]         │
      │                                        │
      │ "interest"                             │
      │   └─ Filter: person.interests          │
      │              intersects required[]     │
      │                                        │
      └────────────────────────────────────────┘
      ↓
      matched_people = apply_filter(all_people, rule)
      ↓
      if rule.operator == "AND":
         all_people = all_people ∩ matched_people
      else:  # OR
         all_people = all_people ∪ matched_people
   ↓
   
Output: List of person IDs who match ALL/ANY criteria
   ↓
   
Create event_invites documents for each matched person
```

---

## Geographic Radius Calculation

```
┌────────────────────────────────────────────────────────────────────────┐
│                     RADIUS-BASED FILTERING                             │
└────────────────────────────────────────────────────────────────────────┘

Example: "Invite anyone within 5 miles of 123 Main St"
   ↓
   
1️⃣ Geocode Event Location
   ↓
   Input: "123 Main St, Orlando, FL 32819"
   API: Google Geocoding / Mapbox
   Output: { lat: 28.5383, lng: -81.3792 }
   ↓

2️⃣ Query Candidates
   ↓
   Firestore: Get all people documents
   (In production: Use GeoFirestore extension for efficient geoqueries)
   ↓

3️⃣ Calculate Distances
   ↓
   For each person:
      if person.primaryAddress.coordinates exists:
         distance = haversine_distance(
            event.coordinates,
            person.coordinates
         )
         
         if distance <= 5 miles:
            include in results
   ↓

4️⃣ Optimization (for scale)
   ↓
   • Use bounding box pre-filter (cheap)
   • Index on lat/lng with GeoFirestore
   • Cache frequent locations (zip code centers)
   • Consider Algolia/Elasticsearch for complex geo queries
```

---

## AI Image Generation Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                  AI IMAGE GENERATION FLOW                              │
└────────────────────────────────────────────────────────────────────────┘

Triggered: On event creation (async)
   ↓

1️⃣ Extract Event Attributes
   ↓
   • category: "playdate"
   • title: "Morning Playdate at the Park"
   • details: "Bring snacks and toys"
   • time: 10:00 AM
   • season: Winter
   ↓

2️⃣ Build AI Prompt
   ↓
   Template:
   """
   A [style] illustration of a [category] event.
   Scene: [keywords from title/details]
   Atmosphere: [time of day], [weather], friendly neighborhood gathering
   Style: Warm, inviting, community-focused
   No text or words in image.
   16:9 aspect ratio.
   """
   ↓
   Result:
   """
   A whimsical, colorful children's book illustration of a playdate event.
   Scene: children playing in a park, morning sunshine, toys and snacks
   Atmosphere: bright daylight, friendly neighborhood gathering
   Style: Warm, inviting, community-focused
   No text or words in image.
   16:9 aspect ratio.
   """
   ↓

3️⃣ Call AI API
   ↓
   OpenAI DALL-E 3:
     • model: "dall-e-3"
     • size: "1792x1024" (wide format)
     • quality: "standard" ($0.04/image)
     • prompt: [from step 2]
   ↓
   [10-20 seconds]
   ↓
   Response: temporary_url = "https://oaidalleapiprod.blob..."
   ↓

4️⃣ Upload to Permanent Storage
   ↓
   Firebase Storage:
     • Download from temporary_url
     • Upload to: /event-images/{event_id}.png
     • Set public read permissions
     • Get permanent URL
   ↓
   permanent_url = "https://firebasestorage.googleapis.com/.../evt123.png"
   ↓

5️⃣ Update Event Document
   ↓
   Firestore:
   db.collection("events").document(event_id).update({
     "imageUrl": permanent_url,
     "imagePrompt": prompt,
     "imageGeneratedAt": now()
   })
   ↓

6️⃣ Fallback Strategy
   ↓
   If generation fails:
     • Use category-specific placeholder
     • Retry once after 5 seconds
     • Log error for manual review
   
   Placeholder images by category:
     • neighborhood → community-gathering.png
     • playdate → kids-playing.png
     • help → helping-hands.png
     • pet → pets-together.png
```

---

## Public Event Landing Page

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PUBLIC EVENT PAGE FLOW                              │
└────────────────────────────────────────────────────────────────────────┘

User shares event → Generates shareable URL
   ↓
   URL: https://gathergrove.com/events/evt123/public?token=xyz789
   ↓

Recipient clicks link (may not be logged in)
   ↓

1️⃣ Server Receives Request
   ↓
   GET /events/evt123/public?token=xyz789
   ↓
   • Verify token validity
   • Check event.inviteCriteria.mode
   • Track view (analytics)
   ↓

2️⃣ Render Beautiful Landing Page
   ↓
   ┌─────────────────────────────────────────┐
   │  ╔═══════════════════════════════════╗  │
   │  ║  [AI-Generated Hero Image]        ║  │
   │  ║  (Full-width, 16:9)               ║  │
   │  ╚═══════════════════════════════════╝  │
   │                                          │
   │  🎉 Neighborhood BBQ                     │
   │  📅 Saturday, Dec 28 • 5:00 PM          │
   │  📍 Smith's Backyard, Bay Hill           │
   │                                          │
   │  Join us for an evening of food, fun,   │
   │  and community! Bring your favorite     │
   │  dish to share.                         │
   │                                          │
   │  👥 23 people invited • 8 going          │
   │                                          │
   │  ┌─────────────────────────────────┐    │
   │  │   [RSVP: I'm Going!]            │    │
   │  │   [Maybe]  [Can't Make It]      │    │
   │  └─────────────────────────────────┘    │
   │                                          │
   │  🔗 Share this event                     │
   │  [Copy Link] [Text] [Email]             │
   │                                          │
   │  Hosted by Sarah Johnson                │
   └─────────────────────────────────────────┘
   ↓

3️⃣ RSVP Flow
   ↓
   User clicks "I'm Going!"
   ↓
   if not logged in:
      → Redirect to signup/login
      → Store intended RSVP in session
      → After auth, auto-submit RSVP
   else:
      → POST /events/evt123/rsvp
      → Update UI: "You're going!"
   ↓

4️⃣ Analytics Tracking
   ↓
   • Increment event.viewCount
   • Track share.viewCount for specific token
   • If user signs up: share.signupsGenerated++
   • Attribution: new user → sharing user gets credit
```

---

## Migration Path Visualization

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION TIMELINE                              │
└────────────────────────────────────────────────────────────────────────┘

PHASE 1: Foundation (Weeks 1-2)
═══════════════════════════════════════════════════════════════════════
Old Schema              Dual Write           New Schema
─────────────           ─────────            ─────────────

households  ─────────►  [Bridge]  ────────►  groups (type=family)
    └─ id                  │                      └─ id
    └─ lastName            │                      └─ name
    └─ type                │                      └─ memberIds[]
    └─ children[]          │                      └─ children[]
                           │
users ──────────────────►  │     ────────────►  people
    └─ uid                 │                      └─ id (= uid)
    └─ name                │                      └─ firstName/lastName
    └─ email               │                      └─ familyIds[]
                           │                      └─ groupIds[]
                           ▼
                    [Backfill Script]
                    Runs once to migrate
                    existing data

Status: ✅ Both schemas work
       ✅ No breaking changes
       ✅ Tests pass


PHASE 2: Enhanced Events (Weeks 3-4)
═══════════════════════════════════════════════════════════════════════
Events Collection Enhancement
─────────────────────────────

events                     
    └─ neighborhoods[]  ──────► Still supported (legacy)
    └─ imageUrl         ──────► NEW: AI-generated
    └─ inviteCriteria   ──────► NEW: Complex targeting
           └─ mode="criteria"
           └─ rules[]
                └─ type: "neighborhood" (uses legacy field)
                └─ type: "group"        (new capability)
                └─ type: "radius"       (new capability)
                └─ type: "age_range"    (new capability)

Frontend can use:
• Old format: neighborhoods[] → works
• New format: inviteCriteria → unlocks features

Status: ✅ Backward compatible
       ✅ New features opt-in
       ✅ Images auto-generated


PHASE 3: Smart Invitations (Weeks 5-6)
═══════════════════════════════════════════════════════════════════════
New Collections Added
─────────────────────

event_invites     ──────► Explicit invitation tracking
    └─ eventId
    └─ personId
    └─ status
    └─ matchedCriteria[]

event_shares      ──────► Viral growth tracking
    └─ eventId
    └─ accessToken
    └─ viewCount
    └─ signupsGenerated

Status: ✅ Pure additions
       ✅ No breaking changes
       ✅ Analytics enabled


PHASE 4: Full Groups & People (Weeks 7-8)
═══════════════════════════════════════════════════════════════════════
New APIs Launched
─────────────────

POST   /groups           ──────► Create custom groups
GET    /people/me        ──────► My person profile
POST   /people/me/groups ──────► Join multiple groups

Old APIs Deprecated (still work)
────────────────────────────────
GET    /households       ──────► Use /groups?type=family instead
POST   /households       ──────► Use /groups instead

Deprecation Timeline:
• Warnings added to old endpoints
• Documentation updated
• 6-month grace period
• After 6 months: redirect to new endpoints

Status: ✅ Migration path clear
       ✅ All features available
       ✅ Users can adopt gradually


PHASE 5: Cleanup (Week 9+)
═══════════════════════════════════════════════════════════════════════
Final Transition
────────────────

• Remove dual-write logic
• Archive households collection (read-only)
• Update all clients to new APIs
• Finalize documentation

Status: ✅ Migration complete
       ✅ Legacy support ends
       ✅ Full extensibility achieved
```

---

## Summary: Key Architectural Improvements

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BEFORE vs AFTER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  BEFORE (Current)              AFTER (Proposed)                     │
│  ─────────────────             ──────────────────                   │
│                                                                     │
│  👤 Person = User = Household  👤 Person with flexible memberships  │
│     (rigid 1:1:1)                 • Multiple families             │
│                                   • Multiple groups                │
│                                   • Rich profile                   │
│                                                                     │
│  🏘️ Only households              🏘️ Groups of any type              │
│                                   • Families                       │
│                                   • HOAs                           │
│                                   • Clubs                          │
│                                   • Custom                         │
│                                                                     │
│  🎉 Events with simple filters   🎉 Premium events with:            │
│     • Neighborhoods only            • AI-generated images          │
│     • Auth-only access              • Smart targeting             │
│     • No images                     • Public shareability          │
│                                     • Viral growth                 │
│                                                                     │
│  📨 Implicit invitations         📨 Explicit invitation system     │
│     (everyone sees everything)      • Criteria-based matching     │
│                                     • Invitation tracking          │
│                                     • Analytics                    │
│                                                                     │
│  🌍 Simple location (strings)    🌍 Geospatial capabilities        │
│                                     • Coordinates                  │
│                                     • Radius queries               │
│                                     • Boundary polygons            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**The result**: A flexible, extensible platform where events are premium experiences and people can organize in any way that makes sense for their community! 🚀
