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

---

## 🧭 Users API Overview

The **Users API** manages profile documents in Firestore for authenticated GatherGrove users.  
All routes are secured with Firebase Authentication and only operate on the caller’s own document.

---

### 🔐 Authentication

All endpoints require a valid Firebase **ID token** in the request header:

~~~bash
-H "Authorization: Bearer <token>"
~~~

> ⚠️ **Important Security Note**  
> The `isAdmin` field is **ignored** unless the caller’s Firebase ID token includes the custom claim:  
> ~~~json
> { "admin": true }
> ~~~  
> This prevents privilege escalation by non-admin users.  

---

### 🧩 Endpoints

#### **1️⃣ POST `/users`**

**Create or update your user document (owner-only upsert)**

- **Purpose:** Create the user record if it doesn’t exist, or update name/email.  
- **Writes:** `users/{uid}` in Firestore  
- **Automatically sets:**  
  - `createdAt` (first write only)  
  - `updatedAt` (on every request)

**Example request:**
~~~bash
curl -sS -X POST http://127.0.0.1:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian Carlberg","isAdmin":true}' | python3 -m json.tool
~~~

**Example response:**
~~~json
{
  "uid": "abc123UID",
  "email": "brian.carlberg@gmail.com",
  "name": "Brian Carlberg",
  "isAdmin": false,    // Ignored for non-admins
  "createdAt": "2025-10-06T11:02:09Z",
  "updatedAt": "2025-10-11T15:02:40Z"
}
~~~

---

#### **2️⃣ PATCH `/users/me`**

**Partially update your own user document**

- **Purpose:** Update one or more fields (e.g., `name`).  
- **Automatically sets:** `updatedAt`.  
- **Security:** Ignores `isAdmin` unless caller is admin.

**Example request:**
~~~bash
curl -sS -X PATCH http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian C."}' | python3 -m json.tool
~~~

---

#### **3️⃣ GET `/users/me`**

**Fetch your own user document**

**Example request:**
~~~bash
curl -sS -X GET http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
~~~

**Returns:**
~~~json
{
  "uid": "abc123UID",
  "email": "brian.carlberg@gmail.com",
  "name": "Brian C.",
  "isAdmin": false,
  "createdAt": "...",
  "updatedAt": "..."
}
~~~

---

#### **4️⃣ GET `/users/{user_id}`**

**Fetch a specific user document (owner-only)**

- Returns 403 if `{user_id}` ≠ caller’s UID.  
- Returns 404 if document doesn’t exist.

**Example request:**
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

### 1) POST `/events` — Create an event (host = current user)

**Dev headers example (Swagger):**
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

### 2) GET `/events` — List upcoming and happening-now

Query params:  
- `neighborhood=Bay Hill` (optional)  
- `type=now|future` (optional)

~~~bash
curl -sS "http://127.0.0.1:8000/events?type=future&neighborhood=Bay%20Hill" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

### 3) GET `/events/{event_id}` — Get an event by ID
~~~bash
curl -sS http://127.0.0.1:8000/events/<EVENT_ID> \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  | python3 -m json.tool
~~~

### 4) POST `/events/{event_id}/rsvp` — RSVP to an event
Body: `{ "status": "going" | "maybe" | "declined" }`

~~~bash
curl -sS -X POST http://127.0.0.1:8000/events/<EVENT_ID>/rsvp \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"status":"going"}' | python3 -m json.tool
~~~

---

## 🗂️ Firestore Structure

| Collection          | Document ID         | Description                                  |
|--------------------|---------------------|----------------------------------------------|
| `users`            | `{uid}`             | One per registered Firebase user             |
| `events`           | `{event_id}`        | Event documents                              |
| `event_attendees`  | `{event_id}_{uid}`  | RSVP records per user per event              |

Each user document includes:
~~~json
{
  "uid": "...",
  "email": "...",
  "name": "...",
  "isAdmin": false,
  "createdAt": "...",
  "updatedAt": "..."
}
~~~

---

## 🧠 Developer Notes

- All timestamps are stored in **UTC** (`datetime.now(timezone.utc)`).  
- `merge=True` ensures existing fields are preserved during updates.  
- Admin-only behavior is enforced by backend **token claims**, not Firestore field values.  
- For local testing with real tokens, always get a fresh Firebase ID token:
  ~~~bash
  echo "$TOKEN" | wc -c   # should be ~900–1000 chars
  ~~~

---

## 🧪 Testing

~~~bash
# run the whole suite
pytest -q

# run just the event lifecycle
pytest -q -k test_event_lifecycle
~~~

(Current status: tests pass locally.)

---

### ✅ Next Planned Enhancements

- [ ] Add `DELETE /users/me` for account removal  
- [ ] Add admin-only endpoint for viewing all users (e.g. `/users/all`)  
- [ ] Add pytest coverage: POST → GET → PATCH → forbidden GET → 404 GET  
- [ ] Event editing (`PATCH /events/{id}`) and stricter validation  

---

📘 **Tech Stack:**
- FastAPI  
- Firebase Auth + Firestore  
- Python 3.13  
- Uvicorn (local dev server)
