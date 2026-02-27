"""
Internal KPI Dashboard - Pilot Metrics

READ-ONLY aggregation endpoint for pilot KPI tracking.
Computes all metrics from existing operational collections.

Access: Internal/admin only (add auth guard before production)
"""

from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, Any, Set, List, Optional

from fastapi import APIRouter, Depends
from app.core.firebase import db
from app.deps.auth import verify_token
from app.config import FOUNDER_UIDS

router = APIRouter(prefix="/internal/kpis", tags=["internal"])


# ==================== HELPERS ====================

def _now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def _parse_dt(v: Any) -> Optional[datetime]:
    """Parse datetime from Firestore (handles both datetime objects and ISO strings)."""
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _list_docs(coll):
    """List all documents from a Firestore collection (works with real and fake DB)."""
    if hasattr(coll, "stream"):  # real Firestore
        return [(d.id, d.to_dict() or {}) for d in coll.stream()]
    if hasattr(coll, "_docs"):  # dev fake
        return list(coll._docs.items())
    return []


def _get_household_from_user(uid: str) -> Optional[str]:
    """Get household ID for a user (checks both householdId and household_id)."""
    user_ref = db.collection("users").document(uid)
    
    if hasattr(user_ref, "get"):  # real Firestore
        doc = user_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            return data.get("householdId") or data.get("household_id")
    elif hasattr(user_ref, "_doc"):  # dev fake
        data = user_ref._doc or {}
        return data.get("householdId") or data.get("household_id")
    
    return None


# ==================== KPI CALCULATIONS ====================

def calculate_new_households_per_week() -> Dict[str, Any]:
    """
    KPI #1: New Households per Week
    
    Count households that completed onboarding in the past 7 days.
    """
    now = _now()
    cutoff = now - timedelta(days=7)
    
    new_households = 0
    
    for hh_id, hh_data in _list_docs(db.collection("households")):
        onboarding_ts = _parse_dt(hh_data.get("onboarding_completed_at"))
        
        if onboarding_ts and onboarding_ts >= cutoff:
            new_households += 1
    
    return {
        "metric": "new_households_per_week",
        "value": new_households,
        "period": "past_7_days",
        "calculated_at": now.isoformat()
    }


def calculate_weekly_active_households() -> Dict[str, Any]:
    """
    KPI #2: Weekly Active Households (WAH)
    
    Count unique households with ≥1 meaningful action in past 7 days:
    - Created event
    - RSVP'd to event
    - Accepted connection
    - Thread activity
    """
    now = _now()
    cutoff = now - timedelta(days=7)
    
    active_households: Set[str] = set()
    
    # Signal 1: Created event
    for event_id, event_data in _list_docs(db.collection("events")):
        # Skip canceled events
        status = str(event_data.get("status", "active")).strip().lower()
        if status in ("canceled", "cancelled"):
            continue
        
        created_at = _parse_dt(event_data.get("createdAt"))
        if created_at and created_at >= cutoff:
            host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
            if host_uid:
                hh_id = _get_household_from_user(host_uid)
                if hh_id:
                    active_households.add(hh_id)
    
    # Signal 2: RSVP'd to event
    for rsvp_id, rsvp_data in _list_docs(db.collection("event_attendees")):
        rsvp_at = _parse_dt(rsvp_data.get("rsvpAt"))
        if rsvp_at and rsvp_at >= cutoff:
            uid = rsvp_data.get("uid")
            if uid:
                hh_id = _get_household_from_user(uid)
                if hh_id:
                    active_households.add(hh_id)
    
    # Signal 3: Accepted connection
    for conn_id, conn_data in _list_docs(db.collection("connections")):
        if conn_data.get("status") == "accepted":
            responded_at = _parse_dt(conn_data.get("responded_at"))
            if responded_at and responded_at >= cutoff:
                from_hh = conn_data.get("from_household_id")
                to_hh = conn_data.get("to_household_id")
                if from_hh:
                    active_households.add(from_hh)
                if to_hh:
                    active_households.add(to_hh)
    
    # Signal 4: Thread activity (messages)
    for thread_id, thread_data in _list_docs(db.collection("threads")):
        updated_at = _parse_dt(thread_data.get("updated_at"))
        if updated_at and updated_at >= cutoff:
            participants = thread_data.get("participants", [])
            for hh_id in participants:
                active_households.add(hh_id)
    
    return {
        "metric": "weekly_active_households",
        "value": len(active_households),
        "period": "past_7_days",
        "calculated_at": now.isoformat()
    }


def calculate_connections_percentage(active_households: Set[str]) -> Dict[str, Any]:
    """
    KPI #3: % WAH with ≥3 Mutual Connections
    
    Count how many active households have 3+ accepted connections.
    """
    household_connections: Dict[str, Set[str]] = defaultdict(set)
    
    # Build connection graph (bidirectional)
    for conn_id, conn_data in _list_docs(db.collection("connections")):
        if conn_data.get("status") == "accepted":
            from_hh = conn_data.get("from_household_id")
            to_hh = conn_data.get("to_household_id")
            
            if from_hh and to_hh:
                household_connections[from_hh].add(to_hh)
                household_connections[to_hh].add(from_hh)
    
    # Count active households with 3+ connections
    households_with_3_plus = sum(
        1 for hh_id in active_households 
        if len(household_connections.get(hh_id, set())) >= 3
    )
    
    wah_count = len(active_households)
    percentage = (households_with_3_plus / wah_count * 100) if wah_count > 0 else 0
    
    return {
        "metric": "pct_wah_with_3plus_connections",
        "value": round(percentage, 2),
        "households_with_3plus": households_with_3_plus,
        "total_wah": wah_count,
        "calculated_at": _now().isoformat()
    }


def calculate_7day_activation() -> Dict[str, Any]:
    """
    KPI #4: 7-Day Activation Rate
    
    % of households that attended an event within 7 days of onboarding.
    
    Proxy: RSVP "going" + event has ended = attended
    (No actual attendance tracking exists)
    """
    now = _now()
    
    total_households = 0
    activated_households = 0
    
    for hh_id, hh_data in _list_docs(db.collection("households")):
        onboarding_ts = _parse_dt(hh_data.get("onboarding_completed_at"))
        
        if not onboarding_ts:
            continue  # Skip households without onboarding timestamp
        
        total_households += 1
        cutoff = onboarding_ts + timedelta(days=7)
        
        # Get all member UIDs for this household
        member_uids = hh_data.get("member_uids", [])
        
        # Check if any member RSVP'd "going" to an event that ended within 7 days
        for uid in member_uids:
            for rsvp_id, rsvp_data in _list_docs(db.collection("event_attendees")):
                if rsvp_data.get("uid") != uid or rsvp_data.get("status") != "going":
                    continue
                
                event_id = rsvp_data.get("eventId") or rsvp_data.get("event_id")
                if not event_id:
                    continue
                
                # Get event to check if it ended
                event_ref = db.collection("events").document(event_id)
                event_data = None
                
                if hasattr(event_ref, "get"):  # real Firestore
                    doc = event_ref.get()
                    if doc.exists:
                        event_data = doc.to_dict()
                elif hasattr(event_ref, "_doc"):  # dev fake
                    event_data = event_ref._doc
                
                if not event_data:
                    continue
                
                # Check if event ended within 7-day window
                event_end = _parse_dt(event_data.get("endAt")) or _parse_dt(event_data.get("expiresAt"))
                
                if event_end and onboarding_ts <= event_end <= cutoff:
                    activated_households += 1
                    break  # Count household once
            else:
                continue
            break  # Household activated, move to next
    
    activation_rate = (activated_households / total_households * 100) if total_households > 0 else 0
    
    return {
        "metric": "7day_activation_rate",
        "value": round(activation_rate, 2),
        "activated_households": activated_households,
        "total_households": total_households,
        "note": "Proxy: RSVP going + event ended (no actual attendance tracking)",
        "calculated_at": now.isoformat()
    }


def calculate_4week_retention() -> Dict[str, Any]:
    """
    KPI #5: 4-Week Retention
    
    % of households that onboarded 4-5 weeks ago and had activity in week 4-5.
    """
    now = _now()
    cohort_start = now - timedelta(weeks=5)
    cohort_end = now - timedelta(weeks=4)
    
    cohort_households: List[tuple] = []
    
    # Get households that onboarded 4-5 weeks ago
    for hh_id, hh_data in _list_docs(db.collection("households")):
        onboarding_ts = _parse_dt(hh_data.get("onboarding_completed_at"))
        
        if onboarding_ts and cohort_start <= onboarding_ts < cohort_end:
            cohort_households.append((hh_id, onboarding_ts))
    
    if not cohort_households:
        return {
            "metric": "4week_retention",
            "value": 0,
            "retained_households": 0,
            "cohort_size": 0,
            "note": "No households onboarded 4-5 weeks ago",
            "calculated_at": now.isoformat()
        }
    
    retained_households = 0
    
    for hh_id, onboarding_ts in cohort_households:
        week_4_start = onboarding_ts + timedelta(weeks=4)
        week_5_end = onboarding_ts + timedelta(weeks=5)
        
        # Check if household had ANY activity in week 4-5 (reuse WAH logic)
        had_activity = False
        
        # Check event creation
        for event_id, event_data in _list_docs(db.collection("events")):
            created_at = _parse_dt(event_data.get("createdAt"))
            if created_at and week_4_start <= created_at < week_5_end:
                host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
                if host_uid and _get_household_from_user(host_uid) == hh_id:
                    had_activity = True
                    break
        
        if not had_activity:
            # Check RSVPs
            for rsvp_id, rsvp_data in _list_docs(db.collection("event_attendees")):
                rsvp_at = _parse_dt(rsvp_data.get("rsvpAt"))
                if rsvp_at and week_4_start <= rsvp_at < week_5_end:
                    uid = rsvp_data.get("uid")
                    if uid and _get_household_from_user(uid) == hh_id:
                        had_activity = True
                        break
        
        if not had_activity:
            # Check connections
            for conn_id, conn_data in _list_docs(db.collection("connections")):
                if conn_data.get("status") == "accepted":
                    responded_at = _parse_dt(conn_data.get("responded_at"))
                    if responded_at and week_4_start <= responded_at < week_5_end:
                        from_hh = conn_data.get("from_household_id")
                        to_hh = conn_data.get("to_household_id")
                        if hh_id in (from_hh, to_hh):
                            had_activity = True
                            break
        
        if had_activity:
            retained_households += 1
    
    retention_rate = (retained_households / len(cohort_households) * 100) if cohort_households else 0
    
    return {
        "metric": "4week_retention",
        "value": round(retention_rate, 2),
        "retained_households": retained_households,
        "cohort_size": len(cohort_households),
        "calculated_at": now.isoformat()
    }


def calculate_non_founder_events() -> Dict[str, Any]:
    """
    KPI #6: % Events Hosted by Non-Founder
    
    Count events where host_user_id is NOT in FOUNDER_UIDS.
    """
    total_events = 0
    non_founder_events = 0
    
    for event_id, event_data in _list_docs(db.collection("events")):
        # Skip canceled events
        status = str(event_data.get("status", "active")).strip().lower()
        if status in ("canceled", "cancelled"):
            continue
        
        total_events += 1
        host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
        
        if host_uid and host_uid not in FOUNDER_UIDS:
            non_founder_events += 1
    
    percentage = (non_founder_events / total_events * 100) if total_events > 0 else 0
    
    return {
        "metric": "pct_events_by_non_founders",
        "value": round(percentage, 2),
        "non_founder_events": non_founder_events,
        "total_events": total_events,
        "calculated_at": _now().isoformat()
    }


def calculate_events_per_active_household(active_households: Set[str]) -> Dict[str, Any]:
    """
    KPI #7: Events per Active Household
    
    Average number of events created per MAH (Monthly Active Household).
    """
    now = _now()
    cutoff = now - timedelta(days=30)
    
    household_event_counts: Dict[str, int] = defaultdict(int)
    
    # Get MAH using 30-day window (recompute for monthly)
    mah_households: Set[str] = set()
    
    for event_id, event_data in _list_docs(db.collection("events")):
        # Skip canceled events
        status = str(event_data.get("status", "active")).strip().lower()
        if status in ("canceled", "cancelled"):
            continue
        
        created_at = _parse_dt(event_data.get("createdAt"))
        if created_at and created_at >= cutoff:
            host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
            if host_uid:
                hh_id = _get_household_from_user(host_uid)
                if hh_id:
                    mah_households.add(hh_id)
                    household_event_counts[hh_id] += 1
    
    # Add other MAH signals (RSVPs, connections, threads)
    for rsvp_id, rsvp_data in _list_docs(db.collection("event_attendees")):
        rsvp_at = _parse_dt(rsvp_data.get("rsvpAt"))
        if rsvp_at and rsvp_at >= cutoff:
            uid = rsvp_data.get("uid")
            if uid:
                hh_id = _get_household_from_user(uid)
                if hh_id:
                    mah_households.add(hh_id)
    
    total_events = sum(household_event_counts.values())
    avg_events = total_events / len(mah_households) if mah_households else 0
    
    return {
        "metric": "events_per_active_household",
        "value": round(avg_events, 2),
        "total_events": total_events,
        "mah_count": len(mah_households),
        "period": "past_30_days",
        "calculated_at": now.isoformat()
    }


# ==================== API ENDPOINT ====================

@router.get("/dashboard")
def get_kpi_dashboard(claims=Depends(verify_token)) -> Dict[str, Any]:
    """
    Internal KPI Dashboard - All Pilot Metrics
    
    Computes all KPIs from existing operational collections.
    
    Access: Internal/admin only (add proper auth guard before production).
    """
    # TODO: Add admin check (e.g., claims.get("admin") or uid in ADMIN_UIDS)
    # For now, any authenticated user can access (dev mode)
    
    # Calculate KPI #2 first (needed for #3 and #7)
    wah_result = calculate_weekly_active_households()
    
    # Get active households set for dependent KPIs
    # Recalculate to get the set (not just count)
    now = _now()
    cutoff = now - timedelta(days=7)
    active_households: Set[str] = set()
    
    for event_id, event_data in _list_docs(db.collection("events")):
        # Skip canceled events
        status = str(event_data.get("status", "active")).strip().lower()
        if status in ("canceled", "cancelled"):
            continue
        
        created_at = _parse_dt(event_data.get("createdAt"))
        if created_at and created_at >= cutoff:
            host_uid = event_data.get("host_user_id") or event_data.get("hostUid")
            if host_uid:
                hh_id = _get_household_from_user(host_uid)
                if hh_id:
                    active_households.add(hh_id)
    
    for rsvp_id, rsvp_data in _list_docs(db.collection("event_attendees")):
        rsvp_at = _parse_dt(rsvp_data.get("rsvpAt"))
        if rsvp_at and rsvp_at >= cutoff:
            uid = rsvp_data.get("uid")
            if uid:
                hh_id = _get_household_from_user(uid)
                if hh_id:
                    active_households.add(hh_id)
    
    for conn_id, conn_data in _list_docs(db.collection("connections")):
        if conn_data.get("status") == "accepted":
            responded_at = _parse_dt(conn_data.get("responded_at"))
            if responded_at and responded_at >= cutoff:
                from_hh = conn_data.get("from_household_id")
                to_hh = conn_data.get("to_household_id")
                if from_hh:
                    active_households.add(from_hh)
                if to_hh:
                    active_households.add(to_hh)
    
    for thread_id, thread_data in _list_docs(db.collection("threads")):
        updated_at = _parse_dt(thread_data.get("updated_at"))
        if updated_at and updated_at >= cutoff:
            participants = thread_data.get("participants", [])
            for hh_id in participants:
                active_households.add(hh_id)
    
    # Calculate all KPIs
    kpis = {
        "kpi_1_new_households_per_week": calculate_new_households_per_week(),
        "kpi_2_weekly_active_households": wah_result,
        "kpi_3_pct_wah_with_3plus_connections": calculate_connections_percentage(active_households),
        "kpi_4_7day_activation": calculate_7day_activation(),
        "kpi_5_4week_retention": calculate_4week_retention(),
        "kpi_6_pct_non_founder_events": calculate_non_founder_events(),
        "kpi_7_events_per_active_household": calculate_events_per_active_household(active_households),
        "kpi_8_invite_signup_conversion": {
            "metric": "invite_signup_conversion",
            "value": None,
            "status": "DEFERRED",
            "note": "No invite system exists yet"
        },
        "kpi_9_revenue_per_mah": {
            "metric": "revenue_per_mah",
            "value": None,
            "status": "DEFERRED",
            "note": "No payment system exists yet"
        }
    }
    
    return {
        "dashboard_name": "GatherGrove Pilot KPIs",
        "generated_at": _now().isoformat(),
        "data_source": "operational_collections",
        "kpis": kpis
    }
