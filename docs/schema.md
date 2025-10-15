# 📘 Firestore Schema — GatherGrove Backend

## 🧍 Users
**Collection:** `users`
- `uid` (string, doc ID)
- `email` (string)
- `name` (string)
- `isAdmin` (bool, default false)
- `createdAt` (timestamp)
- `householdId` (string → ref `households/{id}`)
- `lastActive` (timestamp)
- `favorites` (array of household IDs)

---

## 🏡 Households
**Collection:** `households`
- `id` (string, doc ID)
- `lastName` (string, required)
- `adults` (array of strings, optional)
- `children` (array of objects: `{ age:int, sex:string }`)
- `type` (enum: `family`, `emptyNest`, `singleCouple`)
- `neighborhood` (string)
- `favorites` (array of user or household IDs)
- `createdAt` (timestamp)

---

## 📬 Posts
**Collection:** `posts`
- `id` (string, doc ID)
- `authorId` (string → ref `users/{uid}`)
- `type` (enum: `happeningNow`, `futureEvent`)
- `title` (string)
- `details` (string)
- `timestamp` (timestamp)
- `expiresAt` (timestamp, for `happeningNow`)
- `neighborhood` (string)
- `rsvp` (array of user UIDs)
- `reactions` (map: `{ 👍: 3, ❤️: 2 }`)
- `commentCount` (int)

---

## 📅 Events
*(Subset of posts where `type = futureEvent`)*  
- `capacity` (int, optional)
- `rsvp` (array of user UIDs)
- `startTime` (timestamp)
- `endTime` (timestamp)

---

## ⭐ Favorites
Handled per household in `households.favorites` array for MVP.

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
- `recipientIds` (array of user UIDs)
- `text` (string)
- `timestamp` (timestamp)
- `readBy` (array of user UIDs)
- `type` (enum: `dm`, `group`, `eventThread`)

---

## 🔐 Access Rules (Planned)
Firestore Security Rules will:
- Restrict reads/writes to authenticated users only.
- Allow users to modify only their own documents.
- Enforce `isAdmin` for moderation and post removal.

---

📅 **Version:** v1.0 — October 2025  
This schema supports the GatherGrove MVP rollout for Bayhill & Eagles Pointe and scales for V2 features (DMs, event threads, notifications).
