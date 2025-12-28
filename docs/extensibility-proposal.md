# 🎯 GatherGrove Extensibility Proposal: Events-First Architecture

**Date:** December 27, 2025  
**Status:** Proposal for Review  
**Author:** System Architect

---

## 📋 Executive Summary

This proposal outlines a comprehensive architectural evolution to transform GatherGrove into a highly extensible, **events-first platform** where:

1. **EVENTS** are the premium product with AI-generated imagery, sophisticated invite criteria, and social shareability
2. **PEOPLE** exist within flexible organizational structures (families, groups, HOAs, etc.)
3. **INVITATION SYSTEM** supports complex targeting: specific people, geographic radius, age-based filters, group membership, and combinations thereof

The proposal is designed to build upon the existing codebase while maintaining backward compatibility during migration.

---

## 🎨 Vision & Product Philosophy

### Core Principles

1. **Events as Premium Experience**: Each event is a beautiful, shareable entity with:
   - AI-generated landing images (consistent style based on category/attributes)
   - Rich metadata for intelligent targeting
   - Shareable URLs that work for non-members (viral growth)
   - Smart defaults that make event creation effortless

2. **People as Flexible Entities**: Individuals can belong to:
   - **One or more family units** (households)
   - **Multiple groups** (HOAs, book clubs, running groups, etc.)
   - **Geographic contexts** (neighborhoods, cities, zip codes)
   - **Interest-based segments** (parents of 5-10 year olds, dog owners, etc.)

3. **Intelligent Invitation System**: Event hosts can:
   - Tag specific people directly
   - Define criteria: "anyone in my neighborhood with kids 5-10"
   - Combine criteria: "anyone in my HOA within 5 miles who likes hiking"
   - Make events public, private, or semi-public

---

## 📊 Gap Analysis: Current vs. Desired State

### Current Architecture Strengths ✅

- **Solid foundation**: FastAPI + Firebase, good separation of concerns
- **Working RSVP system**: Three-state RSVPs with capacity management
- **Household model**: Already tracks families with children
- **Profile system**: User profiles with visibility settings
- **Filtering**: Basic neighborhood/category filtering works
- **Test coverage**: Comprehensive pytest suite

### Current Limitations ⚠️

| Area | Current State | Desired State | Gap |
|------|---------------|---------------|-----|
| **People Model** | Tightly coupled to households (1:1 with uid) | Multiple memberships (families, groups) | Need person ↔ group mapping |
| **Group Types** | Only "households" | HOAs, clubs, custom groups | Need `groups` collection |
| **Event Invites** | Implicit (all in neighborhood) | Explicit criteria + targeting rules | Need invitation metadata |
| **Geographic Data** | Neighborhood strings | Lat/lng coordinates + radius queries | Need geospatial indexing |
| **Event Images** | None | AI-generated landing images | Need image generation pipeline |
| **Shareability** | Auth-only events | Public event landing pages | Need public/private modes |
| **Interest Tags** | None | Age ranges, hobbies, attributes | Need user/group tagging |

---

## 🏗️ Proposed Data Model (Firestore Schema)

### 1. **`people` Collection** (NEW - replaces user-household 1:1)

The atomic unit is now a **person**, not a user account tied to a household.

```typescript
{
  id: string                    // Person ID (can still match uid for primary account)
  uid?: string                  // Optional: Firebase Auth UID (if they have an account)
  email?: string                // Optional: for account holders
  
  // Identity
  firstName: string
  lastName: string
  displayName?: string          // Override for public display
  
  // Profile
  bio?: string
  profileImageUrl?: string
  
  // Memberships (flexible)
  familyIds: string[]           // Array of family IDs they belong to
  groupIds: string[]            // Array of group IDs (HOAs, clubs, etc.)
  
  // Location
  primaryAddress?: {
    street: string
    city: string
    state: string
    zip: string
    coordinates: {              // ⭐ KEY: For radius-based invites
      lat: number
      lng: number
    }
  }
  
  // Demographics & Interests
  birthYear?: number            // For age-based filtering
  interests: string[]           // ["hiking", "book clubs", "gardening"]
  
  // Relationships (optional)
  children?: Array<{            // For "parents with kids X-Y" filtering
    id: string                  // Child person ID
    relationship: "child" | "dependent"
  }>
  
  // Preferences
  visibility: "public" | "neighbors" | "private"
  notificationPreferences: {
    pushEnabled: boolean
    emailEnabled: boolean
    eventInvites: boolean
  }
  
  // Metadata
  createdAt: timestamp
  updatedAt: timestamp
  lastActive?: timestamp
}
```

**Migration Strategy**: Backfill from existing `households` and `users` collections.

---

### 2. **`groups` Collection** (NEW - replaces/extends households)

A **group** is any organizational unit: families, HOAs, clubs, neighborhoods, etc.

```typescript
{
  id: string
  
  // Identity
  name: string                  // "Smith Family" or "Bay Hill HOA"
  type: GroupType               // "family" | "hoa" | "club" | "neighborhood" | "custom"
  description?: string
  
  // Geographic
  neighborhood?: string         // For backward compatibility
  geoBoundary?: {               // Optional: polygon for HOA boundaries
    type: "Polygon"
    coordinates: number[][][]
  }
  centerCoordinates?: {         // For radius-based membership
    lat: number
    lng: number
  }
  
  // Membership
  memberIds: string[]           // Array of person IDs
  adminIds: string[]            // Group admins (can manage membership)
  
  // Family-specific (when type="family")
  householdType?: string        // "Family w/ Kids" etc.
  adultNames?: string[]         // Legacy field for display
  children?: Array<{
    personId: string
    birthYear: number
    birthMonth: number
    sex?: "M" | "F"
  }>
  
  // Access Control
  visibility: "public" | "private" | "members"
  joinPolicy: "open" | "request" | "invite_only"
  
  // Metadata
  createdAt: timestamp
  updatedAt: timestamp
  createdBy: string             // Person ID
}
```

**Types of Groups**:
- `family`: Traditional household (backward compatible)
- `hoa`: Homeowners associations
- `club`: Book clubs, running groups, etc.
- `neighborhood`: Geographic community
- `custom`: User-defined (e.g., "Dog Owners")

---

### 3. **`events` Collection** (ENHANCED)

Events become the premium product with rich metadata for targeting.

```typescript
{
  id: string
  
  // Core Identity
  title: string
  details: string
  category: EventCategory       // "neighborhood" | "playdate" | "help" | "pet" | "other"
  
  // ⭐ NEW: Event Image
  imageUrl?: string             // AI-generated landing image
  imagePrompt?: string          // Prompt used for generation
  imageStyle: "modern" | "whimsical" | "elegant"  // Consistent style
  
  // Timing
  type: "now" | "future"
  startAt: timestamp
  endAt?: timestamp
  expiresAt?: timestamp
  
  // Location
  location?: {
    name?: string               // "Smith's Backyard"
    address?: string
    coordinates?: {
      lat: number
      lng: number
    }
  }
  
  // Capacity
  capacity?: number
  
  // ⭐ NEW: Invitation Criteria (replaces simple neighborhoods array)
  inviteCriteria: {
    mode: "specific" | "criteria" | "public"
    
    // For mode="specific"
    specificPeopleIds?: string[]
    specificGroupIds?: string[]
    
    // For mode="criteria"
    rules?: Array<{
      type: "neighborhood" | "group" | "radius" | "age_range" | "interest" | "custom"
      
      // For neighborhood
      neighborhoods?: string[]
      
      // For group membership
      groupIds?: string[]
      
      // For geographic radius
      centerCoordinates?: { lat: number, lng: number }
      radiusMiles?: number
      
      // For age-based (children in household)
      childAgeMin?: number
      childAgeMax?: number
      
      // For interests
      requiredInterests?: string[]
      
      // Combination logic
      operator: "AND" | "OR"      // How to combine with other rules
    }>
    
    // For mode="public"
    publicAccessToken?: string    // Shareable URL token
    allowNonMembers: boolean
  }
  
  // Legacy (for backward compatibility during migration)
  neighborhoods?: string[]        // Deprecated, use inviteCriteria
  
  // Host & Management
  hostId: string                  // Person ID (not uid)
  coHostIds?: string[]
  status: "draft" | "active" | "canceled" | "completed"
  
  // Social
  shareUrl?: string               // Public landing page URL
  shareCount?: number             // How many times shared
  viewCount?: number              // Anonymous views
  
  // Metadata
  createdAt: timestamp
  updatedAt: timestamp
  canceledAt?: timestamp
  canceledBy?: string
}
```

**Key Innovation**: `inviteCriteria` enables complex targeting:

```javascript
// Example: "Anyone in Bay Hill HOA with kids 5-10, within 3 miles of my house"
inviteCriteria: {
  mode: "criteria",
  rules: [
    {
      type: "group",
      groupIds: ["bay-hill-hoa"],
      operator: "AND"
    },
    {
      type: "age_range",
      childAgeMin: 5,
      childAgeMax: 10,
      operator: "AND"
    },
    {
      type: "radius",
      centerCoordinates: { lat: 28.123, lng: -81.456 },
      radiusMiles: 3,
      operator: "AND"
    }
  ]
}
```

---

### 4. **`event_invites` Collection** (NEW)

Explicit invitation tracking for visibility and analytics.

```typescript
{
  id: string                      // Auto-generated
  eventId: string
  personId: string                // Who is invited
  
  // Invitation Source
  invitedBy: string               // Person ID who invited (or "auto" for criteria)
  inviteMethod: "direct" | "criteria" | "share_link"
  matchedCriteria?: string[]      // Which rules matched (for analytics)
  
  // Status
  status: "pending" | "viewed" | "accepted" | "declined"
  viewedAt?: timestamp
  respondedAt?: timestamp
  
  // Metadata
  createdAt: timestamp
}
```

**Purpose**: 
- Track who has been invited (even before they RSVP)
- Enable "Invited" tab vs "Going/Maybe" in UI
- Analytics on invite → conversion rates

---

### 5. **`event_attendees` Collection** (CURRENT - minor updates)

Existing RSVP model stays mostly the same:

```typescript
{
  id: string                      // {event_id}_{person_id}
  eventId: string
  personId: string                // Changed from uid
  status: "going" | "maybe" | "declined"
  rsvpAt: timestamp
  
  // Optional: Track how they found the event
  source?: "invite" | "discovery" | "share_link"
}
```

---

### 6. **`event_shares` Collection** (NEW)

Track viral sharing for growth analytics.

```typescript
{
  id: string
  eventId: string
  sharedBy: string                // Person ID (or "anonymous")
  sharedVia: "link" | "sms" | "email" | "social"
  recipientIdentifier?: string    // Email/phone if known
  
  // Tracking
  accessToken: string             // Unique token for this share
  viewCount: number
  signupsGenerated: number        // If recipient joined platform
  
  createdAt: timestamp
}
```

---

## 🎨 AI Image Generation Pipeline

### Image Generation Strategy

**Goal**: Every event has a beautiful, consistent-style AI-generated landing image.

#### Implementation Approach

1. **On Event Creation**:
   - Extract attributes: category, time of day, season, keywords from title/details
   - Generate prompt using template system
   - Call OpenAI DALL-E 3 API (or Midjourney/Stable Diffusion)
   - Store image URL in `events.imageUrl`

2. **Prompt Template System**:

```python
# app/services/image_generation.py

IMAGE_STYLES = {
    "neighborhood": "warm, inviting watercolor illustration",
    "playdate": "whimsical, colorful children's book illustration",
    "help": "friendly, hand-drawn sketch style",
    "pet": "playful, vibrant cartoon style",
    "other": "modern, clean illustration"
}

def generate_event_image_prompt(event_data: dict) -> str:
    """Generate AI image prompt from event attributes."""
    category = event_data.get("category", "other")
    title = event_data.get("title", "")
    details = event_data.get("details", "")
    
    base_style = IMAGE_STYLES.get(category, IMAGE_STYLES["other"])
    
    # Extract key concepts using simple NLP or GPT-4
    keywords = extract_keywords(f"{title} {details}")
    
    # Time context
    hour = event_data.get("startAt").hour if event_data.get("startAt") else 15
    time_context = "evening golden hour" if hour >= 17 else "bright daylight"
    
    prompt = f"""
    A {base_style} of a {category} event. 
    Scene: {keywords}. 
    Atmosphere: {time_context}, friendly neighborhood gathering.
    Style: Consistent with GatherGrove brand (warm, community-focused, approachable).
    No text or words in image.
    """
    return prompt.strip()

async def generate_and_store_image(event_id: str, event_data: dict) -> str:
    """Generate image and return URL."""
    prompt = generate_event_image_prompt(event_data)
    
    # Call DALL-E 3 API
    response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",  # Wide format for landing pages
        quality="standard",
        n=1
    )
    
    image_url = response.data[0].url
    
    # Download and upload to Firebase Storage for permanence
    permanent_url = await upload_to_firebase_storage(
        image_url, 
        f"event-images/{event_id}.png"
    )
    
    # Update event document
    db.collection("events").document(event_id).update({
        "imageUrl": permanent_url,
        "imagePrompt": prompt
    })
    
    return permanent_url
```

3. **Caching & Performance**:
   - Generate on event creation (async, doesn't block response)
   - Cache prompt → image mappings for similar events
   - Fallback to category-specific default images if generation fails
   - Rate limit: 50 images/day per project (DALL-E 3 pricing)

4. **Cost Optimization**:
   - DALL-E 3: ~$0.04 per 1024x1024 image
   - Budget: $2/day = 50 events/day (scale as needed)
   - Consider Stable Diffusion XL for lower cost at scale

---

## 🔍 Event Discovery & Invitation Engine

### Invitation Criteria Evaluation

```python
# app/services/invitation_matcher.py

from typing import List, Dict, Any
from geopy.distance import geodesic

async def evaluate_invite_criteria(
    event_id: str, 
    criteria: Dict[str, Any]
) -> List[str]:
    """
    Evaluate event invite criteria and return list of eligible person IDs.
    
    Returns:
        List of person IDs who match the criteria
    """
    mode = criteria.get("mode", "public")
    
    if mode == "specific":
        # Direct invites
        people_ids = criteria.get("specificPeopleIds", [])
        group_ids = criteria.get("specificGroupIds", [])
        
        # Expand group IDs to member person IDs
        for group_id in group_ids:
            group = await get_group(group_id)
            people_ids.extend(group.get("memberIds", []))
        
        return list(set(people_ids))
    
    elif mode == "criteria":
        # Evaluate rules and combine
        rules = criteria.get("rules", [])
        
        # Start with all people (or all in relevant groups if specified)
        candidates = await get_all_people_ids()
        
        for rule in rules:
            matched = await evaluate_rule(rule)
            
            if rule.get("operator") == "AND":
                candidates = [p for p in candidates if p in matched]
            else:  # OR
                candidates = list(set(candidates) | set(matched))
        
        return candidates
    
    elif mode == "public":
        # No restrictions, anyone can see/join
        return []  # Empty means public
    
    return []

async def evaluate_rule(rule: Dict[str, Any]) -> List[str]:
    """Evaluate a single criteria rule."""
    rule_type = rule.get("type")
    
    if rule_type == "neighborhood":
        neighborhoods = rule.get("neighborhoods", [])
        return await get_people_in_neighborhoods(neighborhoods)
    
    elif rule_type == "group":
        group_ids = rule.get("groupIds", [])
        people_ids = []
        for gid in group_ids:
            group = await get_group(gid)
            people_ids.extend(group.get("memberIds", []))
        return people_ids
    
    elif rule_type == "radius":
        center = rule.get("centerCoordinates")
        radius_miles = rule.get("radiusMiles", 5)
        return await get_people_within_radius(center, radius_miles)
    
    elif rule_type == "age_range":
        age_min = rule.get("childAgeMin", 0)
        age_max = rule.get("childAgeMax", 18)
        return await get_people_with_children_in_age_range(age_min, age_max)
    
    elif rule_type == "interest":
        interests = rule.get("requiredInterests", [])
        return await get_people_with_interests(interests)
    
    return []

async def get_people_within_radius(
    center: Dict[str, float], 
    radius_miles: float
) -> List[str]:
    """Find people within geographic radius."""
    center_point = (center["lat"], center["lng"])
    
    # Fetch all people (in production, use geospatial indexing)
    all_people = await get_all_people()
    
    matched = []
    for person in all_people:
        address = person.get("primaryAddress")
        if not address or not address.get("coordinates"):
            continue
        
        person_point = (
            address["coordinates"]["lat"],
            address["coordinates"]["lng"]
        )
        
        distance_miles = geodesic(center_point, person_point).miles
        
        if distance_miles <= radius_miles:
            matched.append(person["id"])
    
    return matched
```

### Auto-Invitation on Event Creation

```python
# app/routes/events.py - Enhanced create_event

@router.post("/events", summary="Create an event with auto-invitations")
async def create_event(body: EventIn, claims=Depends(verify_token)):
    # ... existing event creation logic ...
    
    # After event is created:
    if body.inviteCriteria:
        # Evaluate criteria and create invitations asynchronously
        asyncio.create_task(
            generate_invitations(event_id, body.inviteCriteria)
        )
    
    return event_data

async def generate_invitations(
    event_id: str, 
    criteria: Dict[str, Any]
):
    """Generate invitation records for eligible people."""
    eligible_people = await evaluate_invite_criteria(event_id, criteria)
    
    invites = []
    for person_id in eligible_people:
        invites.append({
            "id": f"{event_id}_{person_id}",
            "eventId": event_id,
            "personId": person_id,
            "invitedBy": "auto",
            "inviteMethod": "criteria",
            "status": "pending",
            "createdAt": datetime.now(timezone.utc)
        })
    
    # Batch write to Firestore
    batch = db.batch()
    for invite in invites:
        ref = db.collection("event_invites").document(invite["id"])
        batch.set(ref, invite)
    batch.commit()
    
    # Send push notifications
    await notify_invitees(eligible_people, event_id)
```

---

## 🌐 Public Event Landing Pages & Shareability

### Public Event URL Structure

```
https://gathergrove.com/events/{event_id}?token={access_token}
```

- **Without token**: Shows event to logged-in, eligible users
- **With token**: Shows event to anyone (even non-members)

### Implementation

```python
# app/routes/public_events.py (NEW)

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/events/{event_id}/public", response_class=HTMLResponse)
async def public_event_page(
    event_id: str,
    token: Optional[str] = Query(None),
    request: Request = None
):
    """Public landing page for events (shareable)."""
    
    # Fetch event
    event = await get_event(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    
    # Check access
    invite_criteria = event.get("inviteCriteria", {})
    is_public = invite_criteria.get("mode") == "public"
    
    if not is_public:
        # Verify token if provided
        if token:
            is_valid = await verify_share_token(event_id, token)
            if not is_valid:
                raise HTTPException(403, "Invalid share token")
        else:
            # Require authentication
            raise HTTPException(401, "Authentication required")
    
    # Track view
    await increment_view_count(event_id, token)
    
    # Render beautiful landing page
    return templates.TemplateResponse("event_landing.html", {
        "request": request,
        "event": event,
        "imageUrl": event.get("imageUrl"),
        "shareUrl": f"/events/{event_id}/public?token={token}",
        "canRSVP": True  # Always true for now, handle auth in RSVP endpoint
    })

async def generate_share_token(event_id: str, shared_by: str) -> str:
    """Generate unique shareable token for event."""
    import secrets
    token = secrets.token_urlsafe(16)
    
    # Store share record
    share_record = {
        "id": token,
        "eventId": event_id,
        "sharedBy": shared_by,
        "accessToken": token,
        "viewCount": 0,
        "signupsGenerated": 0,
        "createdAt": datetime.now(timezone.utc)
    }
    
    db.collection("event_shares").document(token).set(share_record)
    
    return token
```

### Share Flow

1. **User clicks "Share Event"**:
   - Backend generates unique token
   - Returns shareable URL: `https://gathergrove.com/events/abc123/public?token=xyz789`

2. **Recipient opens URL**:
   - Sees beautiful landing page with AI-generated image
   - Event details, time, location
   - "RSVP" button (prompts signup if not logged in)

3. **Conversion Tracking**:
   - Track views via token
   - Track signups attributed to share link
   - Show sharing user "5 people joined through your link!"

---

## 🛠️ API Routes: New & Modified

### New Routes

#### Groups API

```
POST   /groups                    Create a new group
GET    /groups                    List groups (filterable)
GET    /groups/{group_id}         Get group details
PATCH  /groups/{group_id}         Update group
DELETE /groups/{group_id}         Delete group
POST   /groups/{group_id}/members Add member to group
DELETE /groups/{group_id}/members/{person_id}  Remove member
```

#### People API (Enhanced)

```
POST   /people                    Create/update person (my profile)
GET    /people                    List people (advanced filters)
GET    /people/{person_id}        Get person details
PATCH  /people/{person_id}        Update person
GET    /people/me                 Get my person profile
PATCH  /people/me                 Update my profile
POST   /people/me/groups          Join a group
DELETE /people/me/groups/{group_id}  Leave a group
```

#### Events API (Enhanced)

```
POST   /events                    Create event (now with inviteCriteria)
GET    /events                    List events (filtered by invites)
GET    /events/{event_id}         Get event details
PATCH  /events/{event_id}         Update event
DELETE /events/{event_id}         Delete event

# NEW:
GET    /events/{event_id}/invites List who's invited
POST   /events/{event_id}/invites Add manual invitations
GET    /events/{event_id}/share   Generate share link
GET    /events/{event_id}/public  Public landing page

# Image generation
POST   /events/{event_id}/regenerate-image  Regenerate AI image
```

### Modified Routes

**Current `/events` endpoint**:
- Add `inviteCriteria` to request body
- Auto-generate invitations on create
- Filter list by invitation status

**Current `/people` endpoint**:
- Decouple from households (use `people` collection)
- Add filtering by group membership
- Add radius-based filtering

---

## 📋 Migration Strategy

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Set up new collections without breaking existing system

1. **Create new collections**: `people`, `groups`, `event_invites`, `event_shares`
2. **Backfill data**:
   - Migrate `households` → `groups` (type="family")
   - Create `people` records from existing users
   - Link people to their family groups
3. **Add dual-write logic**: Write to both old and new collections during transition
4. **No API changes yet**: Keep existing endpoints working

### Phase 2: Enhanced Events (Weeks 3-4)

**Goal**: Launch event images and basic criteria

1. **Add `inviteCriteria` field to events**:
   - Default to legacy behavior (neighborhoods array)
   - Support "specific" mode for direct invites
2. **Implement AI image generation**:
   - OpenAI DALL-E 3 integration
   - Firebase Storage for permanent hosting
   - Async generation pipeline
3. **Launch public event pages**:
   - Simple HTML template
   - Share link generation
   - View tracking

### Phase 3: Smart Invitations (Weeks 5-6)

**Goal**: Unlock criteria-based invites

1. **Implement invitation matcher service**:
   - Neighborhood criteria (already works)
   - Group membership criteria
   - Age range criteria
2. **Add geospatial support**:
   - Store coordinates in `people` collection
   - Implement radius-based matching (Firestore geoqueries or in-memory)
3. **Auto-invitation system**:
   - Generate invites on event create
   - Background job to evaluate criteria

### Phase 4: Full Groups & People (Weeks 7-8)

**Goal**: Launch multi-group membership

1. **New Groups API**: CRUD operations for groups
2. **Enhanced People API**: Multiple group memberships
3. **Group admin features**: Invite management, group settings
4. **Deprecation notices**: Mark old `/households` as deprecated

### Phase 5: Advanced Features (Weeks 9+)

**Goal**: Polish and optimize

1. **Interest-based matching**: Add interests to people, filter by them
2. **Smart recommendations**: "Suggested events for you" based on profile
3. **Advanced analytics**: Invitation → conversion funnels
4. **Performance optimization**: Caching, geospatial indexing

---

## 🎯 Backward Compatibility Plan

### During Migration

**Existing clients can continue using**:
- `GET /events` (returns events using legacy `neighborhoods` array)
- `POST /events` (accepts old format without `inviteCriteria`)
- `GET /households` (continues to work)
- `GET /people` (returns derived view from `groups` where type="family")

**New features available immediately**:
- Event images (auto-generated for all events)
- Public event pages (shareable URLs)
- Direct person invites (via new `inviteCriteria` format)

**Gradual migration**:
- Frontend can adopt new APIs incrementally
- Mobile apps can continue with v1 endpoints
- Deprecation warnings added to old endpoints
- 6-month deprecation window before removal

---

## 🚨 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Image generation costs** | High volume could be expensive | Start with DALL-E, migrate to SD XL for scale; cache aggressively |
| **Geospatial queries at scale** | Firestore not optimized for geo | Use GeoFirestore extension; consider PostGIS for large datasets |
| **Data migration complexity** | Breaking changes during migration | Dual-write strategy; comprehensive testing; rollback plan |
| **Privacy concerns (radius)** | Users may not want location shared | Opt-in only; coarse coordinates (zip-level); clear privacy policy |
| **Invitation spam** | Hosts could abuse criteria | Rate limits on event creation; report/block features |
| **Public event abuse** | Trolls could share inappropriate events | Moderation queue; community reporting; host reputation scores |

---

## 💡 Feedback & Considerations

### What's Great About This Proposal ✅

1. **Extensible architecture**: New criteria types can be added without schema changes
2. **Backward compatible**: Existing system keeps working during migration
3. **User-focused**: Makes event creation easier while adding power features
4. **Viral potential**: Shareable events drive growth organically
5. **Data-driven**: Rich invitation metadata enables analytics & optimization

### Potential Concerns ⚠️

1. **Complexity**: Criteria evaluation engine is non-trivial
   - **Mitigation**: Start simple (neighborhood + groups), add complexity iteratively

2. **Geolocation privacy**: Users may resist sharing coordinates
   - **Mitigation**: Make optional; use coarse granularity (zip code level); transparent privacy controls

3. **Image generation latency**: DALL-E 3 takes 10-20 seconds
   - **Mitigation**: Async generation; show placeholder; fallback to category defaults

4. **Invitation overload**: Users could get too many invites
   - **Mitigation**: Smart throttling; digest notifications; preference controls

### Missing Criteria? 🤔

**Suggested additions**:
- **Time-based**: "People active in last 30 days"
- **Social graph**: "Friends of friends"
- **Past behavior**: "People who attended my last 3 events"
- **Skill-based**: "People who speak Spanish"
- **Equipment-based**: "People with RVs" (for camping events)

**These can be added as new rule types later without schema changes!**

---

## 📊 Success Metrics

### Phase 1-2 (MVP Launch)

- ✅ 100% backward compatibility (no broken tests)
- ✅ AI images generated for 95%+ of events
- ✅ Public event pages render in <2s
- ✅ 10+ beta users create events with new criteria

### Phase 3-4 (Full Rollout)

- 📈 50% of events use criteria-based invites (vs legacy neighborhoods)
- 📈 20% increase in event RSVPs (better targeting)
- 📈 5+ new groups created per week (HOAs, clubs)
- 📈 Share link → signup conversion >5%

### Phase 5 (Mature Product)

- 📈 Average user belongs to 2.5+ groups
- 📈 80% of events use advanced criteria
- 📈 30% of new signups from shared event links
- 📈 NPS score >40 (event creation experience)

---

## 🚀 Next Steps

### Immediate (Next 3 Days)

1. **Review & feedback**: Stakeholder review of this proposal
2. **Technical validation**: Verify Firestore geospatial extensions work as expected
3. **API design review**: Finalize new endpoint schemas
4. **Cost estimation**: Calculate OpenAI API costs at projected scale

### Week 1

1. **Create new Firestore collections** (empty, with indexes)
2. **Write migration scripts** for households → groups, users → people
3. **Set up OpenAI API keys** and test DALL-E 3 integration
4. **Update README** with new schema documentation

### Week 2+

1. **Implement Phase 1** (foundation collections + backfill)
2. **Build image generation pipeline**
3. **Create public event template** (HTML/CSS)
4. **Write comprehensive tests** for new features

---

## 📝 Open Questions for Team

1. **Image style**: Should we offer multiple style options, or enforce brand consistency?
2. **Geolocation**: Opt-in or required? How coarse (address, zip, city)?
3. **Public events**: Should they require approval before becoming shareable?
4. **Group limits**: Max groups per person? Max members per group?
5. **Pricing**: Should advanced criteria be a premium feature?

---

## 📚 Appendix: Example Use Cases

### Use Case 1: Neighborhood Playdate
**Sarah wants to host a playdate for families with kids 3-7 in Bay Hill**

```json
{
  "title": "Morning Playdate at the Park",
  "category": "playdate",
  "startAt": "2025-12-30T10:00:00Z",
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
        "childAgeMin": 3,
        "childAgeMax": 7,
        "operator": "AND"
      }
    ]
  }
}
```

**Result**: 15 families auto-invited, 8 RSVP "going", beautiful AI image of kids playing in park

---

### Use Case 2: HOA Meetup Within Walking Distance
**John hosts an HOA meeting, wants only members within 1 mile**

```json
{
  "title": "HOA Quarterly Meeting",
  "category": "neighborhood",
  "startAt": "2025-12-28T19:00:00Z",
  "inviteCriteria": {
    "mode": "criteria",
    "rules": [
      {
        "type": "group",
        "groupIds": ["bay-hill-hoa"],
        "operator": "AND"
      },
      {
        "type": "radius",
        "centerCoordinates": { "lat": 28.123, "lng": -81.456 },
        "radiusMiles": 1,
        "operator": "AND"
      }
    ]
  }
}
```

**Result**: 42 HOA members within 1 mile invited, 28 RSVP, AI image of neighborhood meeting

---

### Use Case 3: Public Dog Park Meetup
**Maria wants to share a dog meetup with anyone, even non-members**

```json
{
  "title": "Saturday Dog Park Social",
  "category": "pet",
  "startAt": "2025-12-29T15:00:00Z",
  "inviteCriteria": {
    "mode": "public",
    "allowNonMembers": true
  }
}
```

**Result**: Public landing page created, Maria shares link on Facebook, 45 views, 12 RSVPs (4 from non-members who signed up), AI image of dogs playing

---

## 🎉 Conclusion

This proposal transforms GatherGrove into a **truly extensible events platform** where:

✅ **Events are premium experiences** (AI images, smart targeting, shareability)  
✅ **People have flexible identities** (multiple groups, rich profiles)  
✅ **Invitations are intelligent** (criteria-based, not just broadcast)  
✅ **Growth is organic** (shareable public events drive signups)  
✅ **Architecture is future-proof** (new criteria types easily added)

The migration path is **incremental and low-risk**, with backward compatibility maintained throughout. The current codebase provides a solid foundation—we're enhancing, not rebuilding.

**Recommendation**: Proceed with Phase 1 (foundation) immediately, validate with beta users, then scale to full rollout based on feedback.

---

**Ready to build the future of neighborhood events? 🚀**
