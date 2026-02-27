# KPI Dashboard Implementation - Maintainer Mode

## Overview

Minimal-diff implementation for computing GatherGrove Pilot KPIs from existing operational collections.

**Principle:** No new analytics platform. Compute metrics from existing data (events, households, connections, RSVPs).

---

## Changes Made

### 1. Added `onboarding_completed_at` Field (KPI #1)
**File:** `app/models/household.py`  
**Lines:** 1 field added (~4 lines)  
**Purpose:** Track when households complete onboarding (immutable timestamp)

**Set on creation:** `app/routes/users.py` - `create_household()` function

---

### 2. Created Founder Config (KPI #6)
**File:** `app/config.py` (NEW - 13 lines)  
**Purpose:** Define founder UIDs (no schema change)

**Usage:** Empty set by default. Add actual Firebase UIDs as needed:
```python
FOUNDER_UIDS = {
    "firebase_uid_here",
}
```

---

### 3. Created KPI Dashboard Endpoint (All KPIs)
**File:** `app/routes/kpis.py` (NEW - 630 lines)  
**Endpoint:** `GET /internal/kpis/dashboard`  
**Auth:** Requires `verify_token` (add admin check before production)

**Returns:** JSON with all 9 KPIs computed from operational collections

---

### 4. Registered KPI Router
**File:** `app/main.py`  
**Lines:** 2 lines changed (import + router registration)

---

### 5. Added Test Coverage
**File:** `tests/test_kpis.py` (NEW - 178 lines)  
**Coverage:** Endpoint structure, auth, basic calculations

---

## KPI Computation Methods

### KPI #1: New Households per Week
- **Source:** `households.onboarding_completed_at`
- **Logic:** Count households where `onboarding_completed_at >= now - 7 days`

### KPI #2: Weekly Active Households (WAH)
- **Sources:** `events`, `event_attendees`, `connections`, `threads`
- **Signals:**
  - Created event (past 7 days)
  - RSVP'd to event (past 7 days)
  - Accepted connection (past 7 days)
  - Thread activity (past 7 days)
- **Logic:** Unique household IDs with ≥1 signal

### KPI #3: % WAH with ≥3 Connections
- **Source:** `connections` (status = "accepted")
- **Logic:** Build bidirectional graph, count households with 3+ connections, divide by WAH

### KPI #4: 7-Day Activation Rate
- **Sources:** `households`, `event_attendees`, `events`
- **Proxy:** RSVP "going" + event ended = attended (no actual attendance tracking)
- **Logic:** % households that "attended" event within 7 days of onboarding

### KPI #5: 4-Week Retention
- **Sources:** Same as KPI #2 (activity signals)
- **Logic:** Get cohort onboarded 4-5 weeks ago, check if active in week 4-5

### KPI #6: % Events by Non-Founders
- **Sources:** `events.host_user_id`, `FOUNDER_UIDS` config
- **Logic:** Count events where `host_user_id NOT IN FOUNDER_UIDS`

### KPI #7: Events per Active Household
- **Sources:** `events`, MAH calculation (30-day window)
- **Logic:** Total events / MAH count

### KPI #8: Invite → Signup Conversion
- **Status:** DEFERRED (no invite system exists)

### KPI #9: Revenue per MAH
- **Status:** DEFERRED (no payment system exists)

---

## Usage

### Local Development
```bash
# Start backend
cd gathergrove-backend
./start-backend.sh

# Call KPI endpoint (requires auth)
curl -H "X-Uid: admin" -H "X-Email: admin@example.com" \
  http://localhost:8001/internal/kpis/dashboard
```

### Production Notes
1. Add proper admin authorization (check `claims.get("admin")` or whitelist UIDs)
2. Consider caching (compute hourly/daily instead of real-time)
3. Add `FOUNDER_UIDS` to config with actual Firebase UIDs
4. Set `onboarding_completed_at` for existing households (backfill script needed)

---

## Testing

```bash
cd gathergrove-backend
python3 -m pytest tests/test_kpis.py -xvs
```

All tests pass ✅

---

## Total Changes
- **New files:** 3 (config.py, routes/kpis.py, tests/test_kpis.py)
- **Modified files:** 3 (models/household.py, routes/users.py, main.py)
- **Total lines added:** ~830 lines (mostly KPI calculation logic)
- **Schema changes:** 1 field (`households.onboarding_completed_at`)
- **New dependencies:** 0

---

## Next Steps

1. **Backfill onboarding timestamps:** Set `onboarding_completed_at = created_at` for existing households
2. **Add founder UIDs:** Update `app/config.py` with actual Firebase UIDs
3. **Add admin auth:** Protect `/internal/kpis/*` endpoints
4. **Schedule periodic snapshots:** Cron job or cloud function to save KPI snapshots daily/weekly
5. **Build frontend dashboard:** Display KPI trends over time
