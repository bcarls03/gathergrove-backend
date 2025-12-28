# 🌿 GatherGrove Backend

<p align="center">
  <a href="https://codecov.io/gh/bcarls03/gathergrove-backend">
    <img src="https://codecov.io/gh/bcarls03/gathergrove-backend/branch/main/graph/badge.svg" alt="codecov">
  </a>
  <a href="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml">
    <img src="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml/badge.svg" alt="Run Tests">
  </a>
</p>

**Backend API for GatherGrove** — A private, trust-based neighborhood social platform that connects families and households through events, profiles, and community engagement.

Built with **FastAPI + Firebase (Auth & Firestore)** | Python 3.12+ | RESTful API Architecture

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Quickstart](#-quickstart)
- [Project Structure](#-project-structure)
- [Core Features](#-core-features)
- [API Routes](#-api-routes)
  - [Authentication](#-authentication)
  - [Users API](#-users-api)
  - [Events API](#-events-api)
  - [Households API](#-households-api)
  - [People API](#-people-api)
  - [Profile API](#-profile-api)
  - [Push Notifications API](#-push-notifications-api)
- [Data Models](#-data-models)
- [Authentication & Authorization](#-authentication--authorization)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎯 Overview

GatherGrove is a neighborhood-focused social platform designed to strengthen community bonds through:

- **Event Management**: Create, discover, and RSVP to neighborhood events (happening now or scheduled)
- **Household Directory**: Browse and filter families by neighborhood, household type, and children's ages
- **User Profiles**: Personal profiles with favorites, visibility settings, and neighborhood preferences
- **Push Notifications**: Real-time updates for events and community activity
- **Trust-Based Security**: Firebase Authentication with role-based access control

**Key Design Principles:**
- Privacy-first: All data scoped to authenticated neighborhood members
- UTC timestamps throughout for timezone consistency
- In-memory fake Firestore for fast local development and CI testing
- Comprehensive test coverage with pytest

---

## 🚀 Quickstart

### Local Development

**Prerequisites:**
- Python 3.12+ (3.13 supported)
- Firebase Admin SDK credentials (for production mode)

**1️⃣ Clone and Install**
```bash
git clone https://github.com/bcarls03/gathergrove-backend.git
cd gathergrove-backend
pip install -r requirements.txt
```

**2️⃣ Run Development Server**
```bash
# Option A: Use the dev script (sets dev flags automatically)
./scripts/dev.sh

# Option B: Manual start with dev auth
export ALLOW_DEV_AUTH=1
export SKIP_FIREBASE_INIT=1
uvicorn app.main:app --reload --port 8000
```

**3️⃣ Open API Documentation**
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

**4️⃣ Test the API**
```bash
# Health check
curl http://127.0.0.1:8000/health

# Test Firebase/DB connection
curl http://127.0.0.1:8000/firebase

# Check your identity (dev mode)
curl http://127.0.0.1:8000/whoami \
  -H "X-Uid: brian" \
  -H "X-Email: brian@example.com" \
  -H "X-Admin: false"
```

---

## 📁 Project Structure

```
gathergrove-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, route registration
│   ├── core/
│   │   └── firebase.py         # Firebase Admin SDK + in-memory fake DB
│   ├── deps/
│   │   └── auth.py             # Authentication dependency (dev/prod modes)
│   ├── models/
│   │   ├── events.py           # Event-related Pydantic models
│   │   └── rsvp.py             # RSVP models and enums
│   └── routes/
│       ├── events.py           # Event creation, listing, RSVPs
│       ├── users.py            # User management and favorites
│       ├── households.py       # Household directory
│       ├── people.py           # People directory (derived from households)
│       ├── profile.py          # User profiles with settings
│       └── push.py             # Push notification token management
├── docs/
│   └── schema.md               # Comprehensive Firestore schema documentation
├── scripts/
│   ├── dev.sh                  # Local development startup script
│   └── validate_events.sh      # Event validation script
├── secrets/
│   └── gathergrove-dev-firebase-adminsdk.json  # Firebase credentials (gitignored)
├── tests/
│   ├── conftest.py             # Pytest fixtures and test setup
│   ├── test_events.py          # Event API tests
│   ├── test_users.py           # User API tests
│   ├── test_households.py      # Household API tests
│   ├── test_people*.py         # People API tests (pagination, filters)
│   └── test_favorites.py       # Favorites functionality tests
├── .github/
│   └── workflows/
│       └── tests.yml           # CI: Python 3.12 & 3.13 test matrix
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── openapi.json                # Generated OpenAPI schema
└── README.md                   # This file
```

---

## 🎨 Core Features

### 1. Event Management
- **Event Types**: 
  - `now`: Happening right now (expires in 24h by default)
  - `future`: Scheduled events with explicit start times
- **Categories**: `neighborhood`, `playdate`, `help`, `pet`, `other`
- **RSVPs**: Three-state system (`going`, `maybe`, `cant`/`declined`)
- **Capacity Management**: Optional capacity limits enforced on `going` RSVPs
- **Soft Cancellation**: Events can be canceled without deletion
- **Filtering**: By neighborhood, time window (now/future), category
- **Pagination**: Cursor-based pagination with opaque tokens

### 2. User & Household Directory
- **Households Collection**: Central household data store
- **People API**: Derived view with advanced filters:
  - Filter by children's age ranges (ageMin/ageMax)
  - Search by last name (prefix matching)
  - Filter by household type and neighborhood
  - Cursor-based pagination
- **Favorites System**: Users can favorite households for quick access

### 3. User Profiles
- **Profile Settings**:
  - Display name overrides
  - Visibility control (`neighbors`, `private`, `public`)
  - Bio/about section
  - Notification preferences
- **Relationship Management**:
  - Favorites list (household IDs)
  - Include/exclude lists for feed customization

### 4. Push Notifications
- **Token Management**: Register/update/delete device tokens
- **Multi-Platform**: iOS, Android, Web support
- **User-Scoped**: Tokens tied to authenticated users

---

## 🔌 API Routes

### 🔐 Authentication

All routes (except `/health` and `/`) require authentication.

**Development Mode** (`ALLOW_DEV_AUTH=1` or `SKIP_FIREBASE_INIT=1`):
- Use headers: `X-Uid`, `X-Email`, `X-Admin`
- Example:
  ```bash
  -H "X-Uid: brian" \
  -H "X-Email: brian@example.com" \
  -H "X-Admin: false"
  ```

**Production Mode**:
- Use Firebase ID token: `Authorization: Bearer <firebase_id_token>`
- Admin status determined by custom claim: `{ "admin": true }`

### 👤 Users API

**Base Path**: `/users`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/users` | Create/update own user (upsert) | Owner |
| `PATCH` | `/users/me` | Partially update own user | Owner |
| `GET` | `/users/me` | Get own user document | Owner |
| `GET` | `/users/{user_id}` | Get specific user by ID | Owner/Admin |
| `PATCH` | `/users/{uid}` | Update user by UID | Owner/Admin |
| `GET` | `/users` | List all users (paginated) | Admin |
| `GET` | `/users/me/favorites` | List favorited households | Owner |
| `POST` | `/users/me/favorites/{household_id}` | Add household to favorites | Owner |
| `DELETE` | `/users/me/favorites/{household_id}` | Remove from favorites | Owner |

**Key Features**:
- `isAdmin` field ignored unless caller has `admin: true` token claim (prevents privilege escalation)
- Auto-timestamps: `createdAt` (on create), `updatedAt` (always)
- Favorites stored as array of household IDs on user document

**Example: Create User**
```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"name":"Brian Carlberg","isAdmin":false}'
```

### 📅 Events API

**Base Path**: `/events`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/events` | Create event (caller becomes host) | User |
| `GET` | `/events` | List events (filterable, paginated) | User |
| `GET` | `/events/{event_id}` | Get event by ID | User |
| `PATCH` | `/events/{event_id}` | Update event | Host/Admin |
| `PATCH` | `/events/{event_id}/cancel` | Soft-cancel event | Host/Admin |
| `DELETE` | `/events/{event_id}` | Hard-delete event | Host/Admin |
| `GET` | `/events/{event_id}/rsvp` | Get RSVP summary + user status | User |
| `POST` | `/events/{event_id}/rsvp` | RSVP to event | User |
| `DELETE` | `/events/{event_id}/rsvp` | Remove RSVP (leave event) | User |
| `GET` | `/events/{event_id}/attendees` | List all attendees (bucketed) | User |
| `GET` | `/events/{event_id}/attendees/going` | List going attendees | User |

**Query Parameters** (`GET /events`):
- `type`: `now` | `future` (filter by time window)
- `neighborhood`: Filter to single neighborhood
- `category`: `neighborhood` | `playdate` | `help` | `pet` | `other`
- `limit`: 1-50 (default 20)
- `nextPageToken`: Opaque pagination cursor

**Time Window Logic**:
- `type=now`: `startAt <= now < (endAt OR expiresAt)`
- `type=future`: `startAt > now`
- Omitted: Both now and future (excludes expired)
- **Always excludes**: Events where `expiresAt <= now`

**RSVP Status**:
- `going`: Confirmed attendance (counts toward capacity)
- `maybe`: Tentative
- `declined`/`cant`: Not attending

**Example: Create Future Event**
```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{
    "type": "future",
    "title": "Neighborhood Potluck",
    "details": "Bring a dish to share!",
    "startAt": "2025-12-28T18:00:00Z",
    "endAt": "2025-12-28T21:00:00Z",
    "neighborhoods": ["Bay Hill", "Eagles Point"],
    "category": "neighborhood",
    "capacity": 20
  }'
```

**Example: RSVP to Event**
```bash
curl -X POST http://127.0.0.1:8000/events/{event_id}/rsvp \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"status":"going"}'
```

### 🏡 Households API

**Base Path**: `/households`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/households` | List households (filterable) | User |
| `POST` | `/households` | Create/update own household | Owner |

**Query Parameters**:
- `neighborhood`: Filter by neighborhood name
- `household_type` or `type`: Filter by type (checks both `type` and `householdType` fields)

**Household Types** (legacy + new):
- Legacy: `family`, `emptyNest`, `singleCouple`
- New: `Family w/ Kids`, `Empty Nesters`, `Single/Couple`, etc.

**Field Normalization**:
- `adultNames`: Always returned as array of strings
- `kids`/`Kids`: Case-insensitive handling
- Sorted by `lastName` (case-insensitive), then by ID

### 👥 People API

**Base Path**: `/people`

The People API is a **derived view from households** with enhanced filtering capabilities.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/people` | List people/households (advanced filters) | User |
| `POST` | `/people/{household_id}/favorite` | Add household to favorites | User |
| `DELETE` | `/people/{household_id}/favorite` | Remove from favorites | User |

**Query Parameters**:
- `neighborhood`: Single neighborhood filter
- `type`: `family` | `empty_nesters` | `singles_couples`
- `ageMin`: Minimum child age (0-18)
- `ageMax`: Maximum child age (0-18)
- `search`: Last name prefix search (case-insensitive)
- `pageSize`: 1-50 (default 20)
- `pageToken`: Opaque base64-encoded cursor

**Age Filter Logic**:
- Returns households where **any child** falls within `[ageMin, ageMax]`
- Both parameters optional
- Defaults: `ageMin=0`, `ageMax=18`

**Example: Find Families with Young Kids**
```bash
curl "http://127.0.0.1:8000/people?type=family&ageMin=3&ageMax=7&neighborhood=Bay%20Hill" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false"
```

**Response Shape**:
```json
{
  "items": [
    {
      "id": "h123",
      "lastName": "Smith",
      "type": "family",
      "neighborhood": "Bay Hill",
      "adultNames": ["John Smith", "Jane Smith"],
      "childAges": [5, 7],
      "householdType": "Family w/ Kids"
    }
  ],
  "nextPageToken": "eyJjdXJzb3IiOiJoMTIzIn0="
}
```

### 🧑‍💼 Profile API

**Base Path**: `/profile`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/profile` | Get own profile (creates if missing) | User |
| `PATCH` | `/profile` | Update profile settings | User |
| `GET` | `/profile/favorites` | Get favorites list (household IDs) | User |
| `PUT` | `/profile/favorites/{household_id}` | Add to favorites | User |
| `DELETE` | `/profile/favorites/{household_id}` | Remove from favorites | User |
| `GET` | `/profile/overrides` | Get include/exclude lists | User |
| `PUT` | `/profile/overrides` | Update include/exclude lists | User |

**Profile Fields**:
- `display_last_name`: Override household last name display
- `visibility`: `neighbors` (default) | `private` | `public`
- `bio`: Free-text about section (max 500 chars)
- `favorites`: Array of household IDs
- `neighbors_include`: Always show these households
- `neighbors_exclude`: Hide these households
- `notifications_enabled`: Push notification toggle

**Example: Update Profile**
```bash
curl -X PATCH http://127.0.0.1:8000/profile \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{
    "bio": "Love neighborhood events!",
    "visibility": "neighbors",
    "notifications_enabled": true
  }'
```

### 🔔 Push Notifications API

**Base Path**: `/push`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/push/register` | Register/update device push token | User |
| `GET` | `/push/tokens` | List own registered tokens | User |
| `DELETE` | `/push/tokens/{token}` | Delete a push token | User |

**Token Registration**:
```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "platform": "ios"
}
```

**Platforms**: `ios`, `android`, `web`, `unknown`

**Security**:
- Tokens scoped to authenticated user (UID from token claim)
- `uid` field in request body ignored (prevents token theft)
- Admin debug mode: `allow_uid_override=true` query param (admin-only)

---

## 📊 Data Models

### Firestore Collections

#### `users` Collection
**Document ID**: `{uid}` (Firebase Auth UID)

```typescript
{
  uid: string              // Firebase Auth UID
  email: string            // User email
  name: string             // Display name
  isAdmin: boolean         // Informational only (use token claim)
  favorites: string[]      // Array of household IDs
  createdAt: timestamp     // UTC
  updatedAt: timestamp     // UTC
}
```

#### `events` Collection
**Document ID**: Auto-generated

```typescript
{
  id: string
  type: "now" | "future"
  title: string
  details?: string
  startAt: timestamp       // UTC, required for future
  endAt?: timestamp        // UTC
  expiresAt?: timestamp    // UTC, defaults to startAt+24h for "now"
  capacity?: number        // Optional attendance cap
  neighborhoods: string[]  // e.g. ["Bay Hill", "Eagles Point"]
  category?: "neighborhood" | "playdate" | "help" | "pet" | "other"
  hostUid: string          // Event creator
  status?: "active" | "canceled"
  canceledAt?: timestamp
  canceledBy?: string
  createdAt: timestamp
  updatedAt: timestamp
}
```

**Business Rules**:
- `type: "future"` → `startAt` required
- `type: "now"` → `startAt` defaults to `now()`, `expiresAt` defaults to `startAt + 24h`
- Capacity enforced only for `status: "going"` RSVPs
- Canceled events remain readable but RSVP operations return 409

#### `event_attendees` Collection
**Document ID**: `{event_id}_{uid}` (composite key)

```typescript
{
  eventId: string          // Reference to events/{id}
  uid: string              // Reference to users/{uid}
  status: "going" | "maybe" | "declined"
  rsvpAt: timestamp        // UTC
}
```

**Notes**:
- `declined` stored internally, exposed as `cant` in API
- Upsert semantics: POST updates existing RSVP

#### `households` Collection
**Document ID**: `{household_id}` or `{uid}`

```typescript
{
  id: string
  lastName: string         // Or householdLastName
  type?: string            // Legacy: family/emptyNest/singleCouple
  householdType?: string   // New: "Family w/ Kids", etc.
  neighborhood: string     // Or neighborhoodName/neighborhoodCode
  adultNames: string[]     // Adult names in household
  children?: Array<{       // Child records
    age: number
    sex?: "M" | "F"
  }>
  kids?: any               // Alternative children field
  createdAt: timestamp
  updatedAt: timestamp
}
```

**Field Variations** (all supported via normalization):
- Neighborhood: `neighborhood`, `neighborhoodName`, `neighborhoodCode`, `neighborhoodId`
- Type: `type`, `householdType`, `kind`
- Children: `children`, `Kids`, `kids`

#### `profiles` Collection
**Document ID**: `{uid}`

```typescript
{
  uid: string
  email: string
  display_last_name?: string
  visibility: "neighbors" | "private" | "public"
  bio?: string
  favorites: string[]          // Household IDs
  neighbors_include: string[]  // Always show
  neighbors_exclude: string[]  // Always hide
  notifications_enabled: boolean
  created_at: timestamp
  updated_at: timestamp
}
```

#### `pushTokens` Collection
**Document ID**: `{uid}_{token_hash}` or similar

```typescript
{
  uid: string              // Owner
  token: string            // Device push token
  platform: "ios" | "android" | "web" | "unknown"
  registeredAt: timestamp
  updatedAt: timestamp
}
```

### Pydantic Models (API Layer)

Located in `app/models/` and route files:

**Event Models**:
- `EventIn`: Create event request
- `EventPatch`: Partial update request
- `RSVPIn`: RSVP status update
- `EventRsvpHousehold`: Attendee household info
- `EventRsvpBuckets`: Attendees grouped by status

**User Models**:
- `UserIn`: User creation request
- `UserPatch`: Partial user update

**Profile Models**:
- `ProfileUpdate`: Profile update request
- `ProfileOut`: Profile response

---

## 🔒 Authentication & Authorization

### Development Mode

**Enabled when**:
- `ALLOW_DEV_AUTH=1`
- `SKIP_FIREBASE_INIT=1`
- `SKIP_FIREBASE=1` (legacy)
- `CI=true`

**Header-Based Auth**:
```bash
-H "X-Uid: brian"
-H "X-Email: brian@example.com"
-H "X-Admin: false"  # or "true"
```

**Behavior**:
- No Firebase Admin SDK initialization
- In-memory fake Firestore database
- Headers optional (defaults to safe dev identity)
- Fast startup, no cloud dependencies

### Production Mode

**Firebase ID Token Required**:
```bash
-H "Authorization: Bearer <firebase_id_token>"
```

**Token Verification**:
1. Extract token from `Authorization: Bearer` header
2. Verify with `firebase_admin.auth.verify_id_token()`
3. Extract claims: `uid`, `email`, `admin`
4. Return 401 for invalid/expired tokens

**Admin Access**:
- `isAdmin` field on user document is **informational only**
- Real admin status from token custom claim: `{ "admin": true }`
- Set via Firebase Admin SDK or Functions
- Prevents privilege escalation attacks

**Access Control Patterns**:
```python
# Owner-only
if claims["uid"] != target_uid:
    raise HTTPException(status_code=403)

# Owner or admin
if claims["uid"] != target_uid and not claims.get("admin"):
    raise HTTPException(status_code=403)

# Host-only (events)
if event["hostUid"] != claims["uid"] and not claims.get("admin"):
    raise HTTPException(status_code=403)
```

---

## 🛠️ Development

### Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `ALLOW_DEV_AUTH` | `"1"` | Enable dev header auth |
| `SKIP_FIREBASE_INIT` | `"1"` | Skip Firebase Admin init |
| `SKIP_FIREBASE` | `"1"` | Legacy skip Firebase flag |
| `CI` | `"true"` | CI environment indicator |
| `GOOGLE_APPLICATION_CREDENTIALS` | `path` | Firebase credentials JSON |
| `FIREBASE_CRED_PATH` | `path` | Alternative cred path |
| `CORS_ORIGIN` | `url` | Single extra CORS origin |
| `CORS_EXTRA_ORIGINS` | `url,url` | Comma-separated CORS origins |
| `DEV_UID` | `string` | Default dev user ID |
| `DEV_EMAIL` | `string` | Default dev email |
| `DEV_ADMIN` | `"true"/"false"` | Default dev admin status |

### Firebase Setup (Production)

1. **Create Firebase Project**: https://console.firebase.google.com
2. **Download Service Account Key**:
   - Project Settings → Service Accounts
   - Generate New Private Key
   - Save to `secrets/gathergrove-dev-firebase-adminsdk.json`
3. **Set Environment Variable**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/secrets/gathergrove-dev-firebase-adminsdk.json"
   ```
4. **Create Firestore Database**:
   - Enable Firestore in Firebase Console
   - Set security rules (see `docs/security-rules.firestore` if available)

### CORS Configuration

**Default Allowed Origins**:
```python
[
  "http://localhost:3000",   # React dev server
  "http://127.0.0.1:3000",
  "http://localhost:5173",   # Vite dev server
  "http://127.0.0.1:5173"
]
```

**Add Extra Origins**:
```bash
# Single origin
export CORS_ORIGIN="http://192.168.1.100:5173"

# Multiple origins
export CORS_EXTRA_ORIGINS="http://192.168.1.100:5173,https://myapp.com"
```

### Helper Scripts

**`scripts/dev.sh`**: Start dev server with dev mode enabled
```bash
#!/usr/bin/env bash
set -euo pipefail
export ALLOW_DEV_AUTH=1
export SKIP_FIREBASE_INIT=1
export CI=true
python -m uvicorn app.main:app --port 8000 --reload
```

**`scripts/validate_events.sh`**: Validate event data (if implemented)

### Code Style & Linting

**Tools in `requirements.txt`**:
- `black`: Code formatter
- `ruff`: Fast linter
- `mypy` (implied): Type checking

**Run Formatter**:
```bash
black app/ tests/
```

**Run Linter**:
```bash
ruff check app/ tests/
```

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py              # Fixtures, dev mode setup
├── test_events.py           # Event CRUD, RSVPs, pagination
├── test_users.py            # User CRUD, admin checks
├── test_users_favorites.py  # Favorites operations
├── test_households.py       # Household listing, filters
├── test_people.py           # People API basic tests
├── test_people_pagination.py  # Pagination edge cases
├── test_people_filters_extra.py  # Age filters, search
└── test_favorites.py        # Additional favorites tests
```

### Running Tests

**All Tests**:
```bash
pytest
pytest -v  # Verbose
pytest -q  # Quiet
```

**Specific Test Files**:
```bash
pytest tests/test_events.py
pytest tests/test_users.py -v
```

**By Keyword**:
```bash
pytest -k "test_rsvp"
pytest -k "users or events"
pytest -k "not pagination"
```

**With Coverage**:
```bash
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing
```

**Coverage Report Location**: `htmlcov/index.html`

### Test Configuration

**`pytest.ini`**:
```ini
[pytest]
pythonpath = .
testpaths = tests
filterwarnings =
    ignore:The `dict` method is deprecated:DeprecationWarning
```

### Test Fixtures

**`conftest.py` provides**:
- `client`: TestClient with non-admin default identity
- `set_claims(uid, email, admin)`: Change authenticated user
- `seed_households()`: Populate test household data

**Example Test**:
```python
def test_create_event(client, set_claims):
    set_claims(uid="host1", admin=False)
    resp = client.post("/events", json={
        "type": "future",
        "title": "Test Event",
        "startAt": "2025-12-30T18:00:00Z",
        "neighborhoods": ["Bay Hill"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Event"
    assert data["hostUid"] == "host1"
```

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/tests.yml`):
- **Triggers**: Push to `main`, PRs to `main`
- **Matrix**: Python 3.12 (required) & 3.13 (allowed to fail)
- **Steps**:
  1. Checkout code
  2. Setup Python with pip cache
  3. Install dependencies + pytest
  4. Run tests with coverage
  5. Upload coverage to Codecov (Python 3.12 only)

**Environment**:
```yaml
env:
  SKIP_FIREBASE_INIT: "1"
  ALLOW_DEV_AUTH: "1"
  USE_FAKE_DB: "1"
  PYTHONPATH: "."
  PYTHONDONTWRITEBYTECODE: "1"
```

---

## 🚢 Deployment

### Production Checklist

**1. Environment Configuration**
- [ ] Set `GOOGLE_APPLICATION_CREDENTIALS` to service account key path
- [ ] Remove or set to `"0"`: `ALLOW_DEV_AUTH`, `SKIP_FIREBASE_INIT`
- [ ] Configure production CORS origins
- [ ] Set secure secrets management (e.g., AWS Secrets Manager, GCP Secret Manager)

**2. Database Setup**
- [ ] Create production Firestore database
- [ ] Deploy Firestore security rules
- [ ] Set up Firestore indexes (if needed for complex queries)
- [ ] Configure backups

**3. Authentication**
- [ ] Configure Firebase Authentication providers
- [ ] Set custom claims for admin users:
  ```python
  from firebase_admin import auth
  auth.set_custom_user_claims(uid, {"admin": True})
  ```

**4. Application Deployment**
- [ ] Deploy to production environment (Cloud Run, ECS, Kubernetes, etc.)
- [ ] Configure health check endpoint: `/health`
- [ ] Set up logging and monitoring
- [ ] Configure auto-scaling

**5. Security**
- [ ] Enable HTTPS only
- [ ] Set up rate limiting (e.g., nginx, API gateway)
- [ ] Configure Firebase App Check (optional)
- [ ] Review and test authentication flows
- [ ] Audit admin user access

### Deployment Targets

**Google Cloud Run** (recommended):
```bash
gcloud run deploy gathergrove-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/firebase.json
```

**Docker**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY secrets/ ./secrets/
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/firebase.json
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**AWS ECS/Fargate**: Deploy via CloudFormation or Terraform with task definition pointing to ECR image

### Monitoring

**Health Endpoints**:
- `GET /health` → `{"status": "ok"}`
- `GET /firebase` → Validates Firestore connection

**Recommended Metrics**:
- Request rate, latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Firebase Admin SDK latency
- Active connections
- Memory/CPU usage

**Logging**:
- Application logs: `uvicorn` outputs to stdout
- Firestore operations: Firebase Admin SDK logs
- Authentication failures: Custom logging in `auth.py`

---

## 👥 Contributing

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gathergrove-backend.git
   cd gathergrove-backend
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code following existing patterns
   - Add/update tests for new functionality
   - Update documentation as needed

4. **Run Tests**
   ```bash
   pytest
   black app/ tests/
   ruff check app/ tests/
   ```

5. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Open Pull Request**
   - Target: `main` branch
   - Include: Description, testing notes, breaking changes (if any)
   - Wait for CI to pass

### Coding Standards

**Style**:
- Use `black` for formatting (line length 100)
- Follow PEP 8 naming conventions
- Type hints encouraged (but not enforced everywhere)

**Architecture Patterns**:
- **Routes**: Thin handlers, delegate to helper functions
- **Models**: Pydantic for request/response validation
- **Auth**: Always use `Depends(verify_token)` for authenticated routes
- **Database**: Use `db.collection(...).document(...).set/get/update` patterns
- **Timestamps**: Always UTC via `datetime.now(timezone.utc)`
- **Errors**: Use FastAPI `HTTPException` with appropriate status codes

**Git Commit Messages**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/updates
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### Key Files to Review

When modifying functionality, check these files:
- `app/main.py`: Route registration, CORS
- `app/deps/auth.py`: Authentication logic
- `app/core/firebase.py`: Database initialization
- `docs/schema.md`: Firestore schema documentation
- `tests/conftest.py`: Test fixtures and setup

---

## 📝 Additional Documentation

- **Firestore Schema**: See `docs/schema.md` for complete data model documentation
- **OpenAPI Spec**: Auto-generated at `/openapi.json` or http://127.0.0.1:8000/openapi.json
- **API Docs**: Interactive Swagger UI at `/docs`

### 🚀 Extensibility & Future Architecture

**NEW**: Comprehensive proposal for evolving GatherGrove into an events-first, highly extensible platform:

- **[📋 Executive Summary](docs/summary.md)** - Start here! High-level overview for all stakeholders
- **[📖 Full Proposal](docs/extensibility-proposal.md)** - Complete technical proposal with data models, migration strategy, and risk analysis (30 pages)
- **[🏗️ Architecture Diagrams](docs/architecture-diagram.md)** - Visual comparison of current vs. future state
- **[✅ Phase 1 Implementation Guide](docs/phase1-implementation-checklist.md)** - Step-by-step checklist for foundation phase
- **[🔌 API Examples](docs/api-examples-new-features.md)** - Real-world examples of new capabilities (smart targeting, AI images, public events)
- **[🤔 Review Guide](docs/review-guide.md)** - Key questions and considerations for stakeholder review

**Key Features in Proposal**:
- 🎨 AI-generated event images (DALL-E 3)
- 🎯 Smart invitation criteria (neighborhood + age + radius + groups + interests)
- 🔗 Public shareable events (viral growth)
- 👥 Flexible group system (multiple memberships: families, HOAs, clubs, etc.)
- 📊 Explicit invitation tracking and analytics

---

## 🐛 Known Issues & Limitations

- **Pagination**: Cursor tokens are opaque base64 strings (not human-readable)
- **Real-time Updates**: Not supported (requires polling or webhooks)
- **File Uploads**: Not implemented (would need Cloud Storage integration)
- **Search**: Limited to prefix matching on last name (no full-text search)
- **Transactions**: Most operations are non-transactional (eventual consistency)

---

## 📄 License

See `LICENSE` file for details.

---

## 📧 Contact & Support

**Maintainer**: Brian Carlberg  
**Repository**: https://github.com/bcarls03/gathergrove-backend  
**Issues**: https://github.com/bcarls03/gathergrove-backend/issues

---

**Built with ❤️ for neighborhood communities**

*Last Updated: December 2025 | Version 0.1.0*
