# 📘 Firestore Schema — GatherGrove Backend

## 🧍 Users
**Collection:** `users`
- `uid` (string, doc ID)
- `email` (string)
- `name` (string)
- `isAdmin` (bool, default false)
- `createdAt` (timestamp)
- `householdId` (string → ref `households/{id}`)

## 🏡 Households
**Collection:** `households`
- `id` (string, doc ID)
- `lastName` (string, required)
- `adults` (array of strings)
- `children` (array of objects: `{ age:int, sex:string }`)
- `type` (enum: `family`, `emptyNest`, `singleCouple`)
- `favorites` (array of user UIDs)
- `neighborhood` (string)

## 📬 Posts
**Collection:** `posts`
- `id` (string)
- `authorId` (string → ref `users/{uid}`)
- `type` (enum: `happeningNow`, `futureEvent`)
- `title` (string)
- `details` (string)
- `timestamp` (timestamp)
- `expiresAt` (timestamp, for `happeningNow`)
- `neighborhood` (string)
- `rsvp` (array of user UIDs)

## 📅 Events
*(subset of posts with type = `futureEvent`)*

## ⭐ Favorites
Managed within each `household` → `favorites` array for MVP.
