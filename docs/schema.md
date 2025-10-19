# 📘 Firestore Schema — GatherGrove Backend

## 🧍 Users
**Collection:** `users`
- `uid` (string, **doc ID**)
- `email` (string)
- `name` (string)
- `isAdmin` (bool, default `false`) — **informational only**; real admin is via auth token claim
- `favorites` (array<string>, optional)
- `createdAt` (timestamp, UTC)
- `updatedAt` (timestamp, UTC)

---

## 🏡 Households  *(MVP-light)*
**Collection:** `households`
- `id` (string, **doc ID**)
- `name` (string, required)
- `type` (enum: `family`, `single`, `couple`, `roommates`, `other`)
- `neighborhood` (string)
- `createdAt` (timestamp)
- `updatedAt` (timestamp)

---

## 📅 Events
**Collection:** `events`  
Time fields are **UTC**.  
Rules:  
- `type: "future"` → **requires** `startAt`  
- `type: "now"` → `startAt` defaults to now; `expiresAt` defaults to `startAt + 24h`

**Fields**
- `id` (string, **doc ID**)
- `type` (enum: `now`, `future`)
- `title` (string)
- `details` (string, optional)
- `startAt` (timestamp)
- `endAt` (timestamp, optional)
- `expiresAt` (timestamp, optional)
- `capacity` (int, optional)
- `neighborhoods` (array<string>) — e.g. `["Bay Hill","Eagles Point"]`
- `hostUid` (string → ref `users/{uid}`)
- `createdAt` (timestamp)
- `updatedAt` (timestamp)

---

## ✅ Event Attendees (RSVPs)
**Collection:** `event_attendees`  
**Doc ID:** `{event_id}_{uid}`

**Fields**
- `eventId` (string → ref `events/{id}`)
- `uid` (string → ref `users/{uid}`)
- `status` (enum: `going`, `maybe`, `declined`)
- `rsvpAt` (timestamp)

---

## ⭐ Favorites
For MVP, favorites are stored on the user doc:
- `users/{uid}.favorites` (array of household or entity IDs)

*(Can be expanded later to first-class endpoints/collections.)*

---

## 📬 Posts *(Future-ready)*
**Collection:** `posts` *(planned)*  
- `id` (string, **doc ID**)  
- `authorId` (string → ref `users/{uid}`)  
- `type` (enum: `happeningNow`, `futureEvent`)  
- `title` (string)  
- `details` (string)  
- `timestamp` (timestamp)  
- `expiresAt` (timestamp, for `happeningNow`)  
- `neighborhood` (string)  
- `reactions` (map: `{ "👍": 3, "❤️": 2 }`)  
- `commentCount` (int)

---

## 🔔 Notifications *(Future-ready)*
**Collection:** `notifications`
- `id` (string)
- `recipientId` (string → ref `users/{uid}`)
- `type` (enum: `postCreated`, `eventReminder`, `dmMessage`)
- `message` (string)
- `relatedId` (string → could reference `posts/{id}` or `messages/{id}`)
- `read` (bool)
- `createdAt` (timestamp)

---

## 💬 Messages *(Future-ready)*
**Collection:** `messages`
- `id` (string)
- `senderId` (string → ref `users/{uid}`)
- `recipientIds` (array<string> of user UIDs)
- `text` (string)
- `timestamp` (timestamp)
- `readBy` (array<string> of user UIDs)
- `type` (enum: `dm`, `group`, `eventThread`)

---

## 🔐 Access Rules (Planned)
Security rules & backend checks enforce:
- Auth required for all reads/writes.
- Users may create/read/update **only their own** `users/{uid}` document.
- Events may be **PATCH/DELETE** only by the **host (`hostUid`)** or an **admin**.
- Admin is determined by **token claim** `admin: true` (do **not** trust stored `isAdmin`).

---

📅 **Version:** v0.2 — October 2025  
Covers the shipped MVP: **Users**, **Events**, **Event RSVPs**, and a lightweight **Households** model. Future-ready sections outline next-phase collections.
