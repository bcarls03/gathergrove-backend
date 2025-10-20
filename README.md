# 🌿 GatherGrove Backend

<p align="center">
  <a href="https://codecov.io/gh/bcarls03/gathergrove-backend">
    <img src="https://codecov.io/gh/bcarls03/gathergrove-backend/branch/main/graph/badge.svg" alt="codecov">
  </a>
  <a href="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml">
    <img src="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml/badge.svg" alt="Run Tests">
  </a>
</p>

Backend API for the **GatherGrove** app — a private, trust-based neighborhood platform built with **FastAPI + Firebase**.

---

## 🚀 Quickstart (local)

~~~bash
uvicorn app.main:app --reload --port 8000
open http://127.0.0.1:8000/docs
~~~

**Auth while developing (Swagger headers):**
- `X-Uid` – your temporary user id  
- `X-Email` – an email (any string for dev)  
- `X-Admin` – `"true"` or `"false"`

**Auth in production (Firebase):** send a Firebase ID token:
~~~
Authorization: Bearer <idToken>
~~~

**CI/dev toggles (already set in CI):**
- `ALLOW_DEV_AUTH=1` → allow the `X-*` headers above  
- `SKIP_FIREBASE_INIT=1` (or `SKIP_FIREBASE=1`) → skip Admin SDK init  
- When dev mode is enabled, a default UID/email is used if headers are missing.

---

## 🧭 Users API Overview

The **Users API** manages profile documents in Firestore for authenticated GatherGrove users.  
All routes are secured with Firebase Authentication and only operate on the caller’s own document.

### 🔐 Authentication

All endpoints require a valid Firebase **ID token** in the request header:

~~~bash
-H "Authorization: Bearer <token>"
~~~

> ⚠️ **Security note**  
> The `isAdmin` field is **ignored** unless the caller’s Firebase ID token includes the custom claim:  
> ~~~json
> { "admin": true }
> ~~~  
> This prevents privilege escalation by non-admin users.

---

## 🧩 Users Endpoints

### **1️⃣ POST `/users`** — Create or update your user (owner-only upsert)

- **Writes:** `users/{uid}`  
- **Auto-sets:** `createdAt` (first write), `updatedAt` (always)

~~~bash
curl -sS -X POST http://127.0.0.1:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian Carlberg","isAdmin":true}' | python3 -m json.tool
~~~

~~~json
{
  "uid": "abc123UID",
  "email": "brian.carlberg@gmail.com",
  "name": "Brian Carlberg",
  "isAdmin": false,
  "createdAt": "2025-10-06T11:02:09Z",
  "updatedAt": "2025-10-11T15:02:40Z"
}
~~~

### **2️⃣ PATCH `/users/me`** — Partially update your own user

~~~bash
curl -sS -X PATCH http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian C."}' | python3 -m json.tool
~~~

### **3️⃣ GET `/users/me`** — Fetch your own user

~~~bash
curl -sS -X GET http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
~~~

### **4️⃣ GET `/users/{user_id}`** — Fetch a specific user (owner-only)

- **403** if `{user_id}` ≠ caller’s UID  
- **404** if document doesn’t exist

~~~bash
curl -sS -X GET http://127.0.0.1:8000/users/abc123UID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
~~~

---

## 🗓️ Events API

Create and browse neighborhood events. Time fields use **UTC**.

> **Time rules**  
> • `type: "future"` → **requires** `startAt`  
> • `type: "now"` → `startAt` defaults to now; `expiresAt` defaults to `startAt + 24h`

### 1) **POST `/events`** — Create (host = current user)

~~~bash
curl -sS -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{
    "type":"future",
    "title":"Neighborhood hot cocoa night",
    "details":"Bring your favorite mug!",
    "startAt":"2025-12-15T23:00:00Z",
    "neighborhoods":["Bay Hill","Eagles Point"]
  }' | python3 -m json.tool
~~~

### 2) **GET `/events`** — List upcoming and happening-now

Query params: `neighborhood=Bay Hill` (optional), `type=now|future` (optional)

~~~bash
curl -sS "http://127.0.0.1:8000/events?type=future&neighborhood=Bay%20Hill" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

### 3) **GET `/events/{event_id}`** — Get by ID

~~~bash
curl -sS http://127.0.0.1:8000/events/<EVENT_ID> \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

### 4) **POST `/events/{event_id}/rsvp`** — RSVP (going/maybe/declined)

Body: `{ "status": "going" | "maybe" | "declined" }`

~~~bash
curl -sS -X POST http://127.0.0.1:8000/events/<EVENT_ID>/rsvp \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"status":"going"}' | python3 -m json.tool
~~~

### 5) **PATCH `/events/{event_id}`** — Edit (host-only)

~~~bash
curl -sS -X PATCH http://127.0.0.1:8000/events/<EVENT_ID> \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"title":"Neighborhood hot cocoa night (updated)"}' | python3 -m json.tool
~~~

### 6) **DELETE `/events/{event_id}`** — Delete (host or admin)

~~~bash
curl -sS -X DELETE http://127.0.0.1:8000/events/<EVENT_ID> \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

---

## 🏡 Households API

Simple, paginated household directory (used by People API).

### **GET `/households`**

Query params:  
- `neighborhood` (optional)  
- `type` = `family|emptyNest|singleCouple` (optional)  
- `pageSize` (1–50, default 20), `pageToken` (opaque cursor)

~~~bash
curl -sS "http://127.0.0.1:8000/households?neighborhood=Bay%20Hill&type=family" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

---

## 👥 People API

People is a derived view **from households** with extra filters.

### **GET `/people`**

Query params:  
- `neighborhood` (optional)  
- `type` = `family|emptyNest|singleCouple` (optional)  
- `ageMin`, `ageMax` (filter by children’s ages)  
- `pageSize` (1–50, default 20), `pageToken`

Response:
~~~json
{
  "items": [
    { "id": "H123", "type": "family", "neighborhood": "Bay Hill", "childAges": [6, 10] }
  ],
  "nextPageToken": "H123"
}
~~~

~~~bash
curl -sS "http://127.0.0.1:8000/people?neighborhood=Bay%20Hill&type=family" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

### ⭐ Favorites (on the user document)

**POST `/people/{household_id}/favorite`** — add a household to the caller’s favorites  
**DELETE `/people/{household_id}/favorite`** — remove it

~~~bash
# Favorite
curl -sS -X POST http://127.0.0.1:8000/people/favH/favorite \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" | python3 -m json.tool

# Unfavorite
curl -sS -X DELETE http://127.0.0.1:8000/people/favH/favorite \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" | python3 -m json.tool
~~~

---

## 🗂️ Firestore Structure (MVP)

| Collection          | Document ID         | Description                                  |
|--------------------|---------------------|----------------------------------------------|
| `users`            | `{uid}`             | One per registered Firebase user             |
| `events`           | `{event_id}`        | Event documents                              |
| `event_attendees`  | `{event_id}_{uid}`  | RSVP records per user per event              |
| `households`       | `{household_id}`    | Household directory used by People API       |

Each user document includes:
~~~json
{
  "uid": "...",
  "email": "...",
  "name": "...",
  "isAdmin": false,
  "favorites": ["householdId1", "householdId2"],
  "createdAt": "...",
  "updatedAt": "..."
}
~~~

---

## 🧠 Developer Notes

- All timestamps are stored in **UTC** (`datetime.now(timezone.utc)`).  
- `merge=True` is used for partial updates to preserve existing fields.  
- Admin-only behavior is enforced by backend **token claims**, not Firestore field values.  
- CI runs against an in-memory Firestore **fake** (dev mode) so tests don’t hit the cloud.  
- For local testing with real tokens, always get a fresh Firebase ID token:
  ~~~bash
  echo "$TOKEN" | wc -c   # should be ~900–1000 chars
  ~~~

---

## 🧪 Testing

~~~bash
# run the whole suite
pytest -q

# focused runs
pytest -q -k users
pytest -q -k events
pytest -q -k households
pytest -q -k people
pytest -q -k favorites
~~~

_Current status: tests passing locally and in CI (Python 3.12 & 3.13)._

---

### ✅ Roadmap (near-term)

- [ ] `GET /users/me/favorites` → return full household cards for saved favorites  
- [ ] People paging tests (pageSize/pageToken round-trip)  
- [ ] Event attendee list `GET /events/{id}/attendees`  
- [ ] Admin list users endpoint (e.g., `/users/all`)  
- [ ] More auth edge-case tests

---

📘 **Tech Stack:**
- FastAPI  
- Firebase Auth + Firestore  
- Python 3.13  
- Uvicorn (local dev server)
