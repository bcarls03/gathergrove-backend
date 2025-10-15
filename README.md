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

## 🧭 Users API Overview

The **Users API** manages profile documents in Firestore for authenticated GatherGrove users.  
All routes are secured with Firebase Authentication and only operate on the caller’s own document.

---

### 🔐 Authentication

All endpoints require a valid Firebase **ID token** in the request header:

```bash
-H "Authorization: Bearer <token>"
```

> ⚠️ **Important Security Note**  
> The `isAdmin` field is **ignored** unless the caller’s Firebase ID token includes the custom claim:  
> ```json
> { "admin": true }
> ```  
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
```bash
curl -sS -X POST http://127.0.0.1:8000/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian Carlberg","isAdmin":true}' | python3 -m json.tool
```

**Example response:**
```json
{
  "uid": "abc123UID",
  "email": "brian.carlberg@gmail.com",
  "name": "Brian Carlberg",
  "isAdmin": false,    // Ignored for non-admins
  "createdAt": "2025-10-06T11:02:09Z",
  "updatedAt": "2025-10-11T15:02:40Z"
}
```

---

#### **2️⃣ PATCH `/users/me`**

**Partially update your own user document**

- **Purpose:** Update one or more fields (e.g., `name`).  
- **Automatically sets:** `updatedAt`.  
- **Security:** Ignores `isAdmin` unless caller is admin.

**Example request:**
```bash
curl -sS -X PATCH http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Brian C."}' | python3 -m json.tool
```

---

#### **3️⃣ GET `/users/me`**

**Fetch your own user document**

**Example request:**
```bash
curl -sS -X GET http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Returns:**
```json
{
  "uid": "abc123UID",
  "email": "brian.carlberg@gmail.com",
  "name": "Brian C.",
  "isAdmin": false,
  "createdAt": "...",
  "updatedAt": "..."
}
```

---

#### **4️⃣ GET `/users/{user_id}`**

**Fetch a specific user document (owner-only)**

- Returns 403 if `{user_id}` ≠ caller’s UID.  
- Returns 404 if document doesn’t exist.

**Example request:**
```bash
curl -sS -X GET http://127.0.0.1:8000/users/abc123UID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### 🗂️ Firestore Structure

| Collection | Document ID | Description |
|-------------|--------------|-------------|
| `users` | `{uid}` | One per registered Firebase user |

Each document includes:
```json
{
  "uid": "...",
  "email": "...",
  "name": "...",
  "isAdmin": false,
  "createdAt": "...",
  "updatedAt": "..."
}
```

---

### 🧠 Developer Notes

- All timestamps are stored in **UTC** (`datetime.now(timezone.utc)`).  
- `merge=True` ensures existing fields are preserved during updates.  
- Admin-only behavior is enforced by backend claim checks, not Firestore field values.  
- For local testing, always get a fresh token before each curl test:
  ```bash
  echo "$TOKEN" | wc -c   # should be ~930 chars
  ```

---

### ✅ Next Planned Enhancements

- [ ] Add `DELETE /users/me` for account removal  
- [ ] Add admin-only endpoint for viewing all users (e.g. `/users/all`)  
- [ ] Add pytest coverage: POST → GET → PATCH → forbidden GET → 404 GET  

---

📘 **Tech Stack:**
- FastAPI  
- Firebase Auth + Firestore  
- Python 3.13  
- Uvicorn (local dev server)
