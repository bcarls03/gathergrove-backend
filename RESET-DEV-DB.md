# Reset Dev Database - Quick Guide

## 🎯 Best Recommendation: Use the Reset Script

When testing onboarding and need to start fresh, simply run:

```bash
cd gathergrove-backend
./scripts/reset-dev-db.sh
```

This clears all test data from the in-memory fake database.

---

## 📋 All Available Methods

### **Method 1: Reset Script (Easiest)** ⭐️ RECOMMENDED

```bash
cd gathergrove-backend
./scripts/reset-dev-db.sh
```

**Pros:**
- ✅ One command
- ✅ Clears all backend data instantly
- ✅ No need to clear browser storage
- ✅ Works while backend is running

**When to use:** Before each onboarding test run

---

### **Method 2: API Endpoint (For Integration)**

```bash
curl -X POST http://localhost:8000/dev/reset-db
```

**Pros:**
- ✅ Can be called from frontend
- ✅ Can be automated in tests
- ✅ Returns JSON response

**When to use:** In automated tests or scripts

---

### **Method 3: Restart Backend (Nuclear Option)**

```bash
# Kill backend
pkill -f "uvicorn app.main:app"

# Restart backend
cd gathergrove-backend
./scripts/dev.sh
```

**Pros:**
- ✅ Guaranteed clean slate
- ✅ Reloads all code changes

**Cons:**
- ❌ Takes 5-10 seconds
- ❌ Loses dev server connection

**When to use:** When you've made backend code changes

---

### **Method 4: Clear Browser Only (Frontend State)**

In browser console (F12):
```javascript
localStorage.clear()
sessionStorage.clear()
location.reload()
```

**Pros:**
- ✅ Fast (instant)
- ✅ Clears frontend onboarding state

**Cons:**
- ❌ Doesn't clear backend data
- ❌ Will still get "User already exists" error

**When to use:** Only if backend data doesn't matter

---

## 🔄 Recommended Workflow

### **Full Onboarding Test (Fresh Start)**

```bash
# 1. Reset backend data
cd gathergrove-backend
./scripts/reset-dev-db.sh

# 2. In browser console (F12):
localStorage.clear()
sessionStorage.clear()
location.reload()

# 3. Go to: http://localhost:5173/onboarding/access
# 4. Sign in and test full flow
```

### **Quick Backend-Only Reset**

If you only need to clear backend data (keep browser state):

```bash
cd gathergrove-backend
./scripts/reset-dev-db.sh
```

Then refresh the page.

---

## 💡 Pro Tips

### **Add to VS Code Tasks** (Optional)

Create `.vscode/tasks.json` in gathergrove-backend:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Reset Dev Database",
      "type": "shell",
      "command": "./scripts/reset-dev-db.sh",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

Then: `Cmd+Shift+P` → "Tasks: Run Task" → "Reset Dev Database"

### **Create an Alias** (Optional)

Add to your `~/.zshrc`:

```bash
alias reset-db="cd ~/dev/gathergrove-backend && ./scripts/reset-dev-db.sh"
```

Then from anywhere: `reset-db`

---

## 🛡️ Safety Features

The reset endpoint **only works** when:
- ✅ `SKIP_FIREBASE_INIT=1` is set (fake DB mode)
- ✅ Using in-memory fake database
- ❌ **Will NOT work** on production/real Firestore

This prevents accidental data deletion in production.

---

## 🐛 Troubleshooting

### "User profile already exists" Error

**Problem:** Backend has stored profile for test user  
**Solution:** Run `./scripts/reset-dev-db.sh`

### "This endpoint only works in dev mode"

**Problem:** Backend is using real Firestore  
**Solution:** Check `scripts/dev.sh` has `SKIP_FIREBASE_INIT=1`

### Script Permission Denied

**Problem:** Script not executable  
**Solution:** `chmod +x scripts/reset-dev-db.sh`

---

## 📊 What Gets Cleared

When you reset the dev database:

- ✅ **Users** - All user profiles deleted
- ✅ **Households** - All household data cleared
- ✅ **Events** - All events removed
- ✅ **Groups** - All neighborhood groups cleared
- ✅ **Favorites** - All favorites wiped
- ✅ **RSVPs** - All RSVP data cleared

**Note:** Browser localStorage is NOT affected. Clear that separately if needed.

---

## 🎬 Quick Start

Just remember this one command:

```bash
./scripts/reset-dev-db.sh
```

Run it from `gathergrove-backend` directory before each onboarding test.
