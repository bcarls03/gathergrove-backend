# app/main.py
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.firebase import db  # real Firestore OR dev fake when SKIP_* is set
from app.deps.auth import verify_token  # auth lives here
from app.routes import events, households, people, push, users, groups, connections, dev, invitations, threads

app = FastAPI(title="GatherGrove Backend", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://localhost:4174",
]

extra = os.getenv("CORS_EXTRA_ORIGINS", "")
if extra:
    FRONTEND_ORIGINS.extend([o.strip() for o in extra.split(",") if o.strip()])

# Optional: allow a single extra origin via env var (useful for LAN testing)
single = os.getenv("CORS_ORIGIN", "").strip()
if single:
    FRONTEND_ORIGINS.append(single)

# De-dupe
FRONTEND_ORIGINS = sorted({o for o in FRONTEND_ORIGINS if o})

# Allow all Vercel preview URLs (*.vercel.app)
allow_origin_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Meta routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "GatherGrove API running"}


@app.get("/firebase", tags=["meta"], summary="Firebase Ping")
def firebase_ping():
    # Touch firestore / dev fake so we can validate connection quickly
    list(db.collections())
    return {"ok": True}


@app.get("/whoami", tags=["auth"], summary="Whoami")
def whoami(claims=Depends(verify_token)):
    return claims


@app.post("/dev/reset-db", tags=["dev"], summary="Reset Database (Dev Only)")
def reset_dev_database():
    """
    Reset the in-memory fake database (dev mode only).
    This clears all users, households, events, and other data.
    Only works when SKIP_FIREBASE_INIT=1 (using fake DB).
    """
    if not (os.getenv("SKIP_FIREBASE_INIT") == "1" or os.getenv("SKIP_FIREBASE") == "1"):
        return {"error": "This endpoint only works in dev mode with fake DB"}, 403
    
    # Access the internal _data dict of the fake DB
    if hasattr(db, '_data'):
        db._data.clear()
        return {
            "success": True,
            "message": "Dev database cleared successfully",
            "collections_cleared": 0
        }
    else:
        return {
            "error": "Not using fake database or unable to clear",
            "using_real_db": True
        }, 400


@app.post("/dev/seed-test-groups", tags=["dev"], summary="Seed Test Groups (Dev Only)")
def seed_test_groups():
    """Seed test neighborhood groups for auto-join testing (dev mode only)"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc).isoformat()
    
    groups_data = [
        # Subdivision Example 1: Oakwood Hills with admin and verified members
        {
            "id": "oakwood-hoa-001",
            "type": "neighborhood",
            "name": "Oakwood Hills",
            "members": [
                {
                    "user_id": "admin-user-001",
                    "role": "admin",
                    "joined_at": now,
                    "verification_status": "admin_verified",
                    "verified_by": ["admin-user-001"]
                },
                {
                    "user_id": "member-user-002",
                    "role": "member",
                    "joined_at": now,
                    "verification_status": "admin_verified",
                    "verified_by": ["admin-user-001"]
                }
            ],
            "metadata": {
                "neighborhood_type": "subdivision",
                "hoa_name": "Oakwood Hills",
                "city": "Portland",
                "state": "OR",
                "zip": "97203",
                "amenities": ["pool", "clubhouse", "tennis courts"],
                "management_company": "ABC Management Co.",
                "website": "https://oakwoodhills.com",
                "board_contact": "board@oakwoodhills.com",
                "boundaries": {
                    "streets": ["Oakwood Hills Dr", "Oakwood Hills Ct", "Oakwood Hills Ln"],
                    "zip": "97203"
                }
            },
            "created_at": now,
            "updated_at": now
        },
        
        # Subdivision Example 2: Cedar Ridge with pending members
        {
            "id": "cedar-ridge-hoa-002",
            "type": "neighborhood",
            "name": "Cedar Ridge HOA",
            "members": [
                {
                    "user_id": "admin-user-100",
                    "role": "admin",
                    "joined_at": now,
                    "verification_status": "admin_verified",
                    "verified_by": ["admin-user-100"]
                },
                {
                    "user_id": "pending-user-101",
                    "role": "member",
                    "joined_at": now,
                    "verification_status": "pending",
                    "verified_by": []
                },
                {
                    "user_id": "vouched-user-102",
                    "role": "member",
                    "joined_at": now,
                    "verification_status": "neighbor_vouched",
                    "verified_by": ["admin-user-100", "member-user-002"]
                }
            ],
            "metadata": {
                "neighborhood_type": "subdivision",
                "hoa_name": "Cedar Ridge",
                "city": "Portland",
                "state": "OR",
                "zip": "97006",
                "amenities": ["park", "playground"],
                "boundaries": {
                    "streets": ["Cedar Ridge Ln", "Cedar Ridge Way", "Cedar Ridge Ct"],
                    "zip": "97006"
                }
            },
            "created_at": now,
            "updated_at": now
        },
        
        # Subdivision Example 3: Maple Grove (no members yet)
        {
            "id": "maple-grove-hoa-003",
            "type": "neighborhood",
            "name": "Maple Grove",
            "members": [],
            "metadata": {
                "neighborhood_type": "subdivision",
                "hoa_name": "Maple Grove",
                "city": "Portland",
                "state": "OR",
                "zip": "97223",
                "amenities": ["gym", "pool"],
                "management_company": "XYZ Property Management",
                "boundaries": {
                    "streets": ["Maple Grove Ct", "Maple Grove Dr"],
                    "zip": "97223"
                }
            },
            "created_at": now,
            "updated_at": now
        },
        
        # Subdivision Example 4: Nicole Lane (Loveland, OH) - for testing with real addresses
        {
            "id": "nicole-lane-005",
            "type": "neighborhood",
            "name": "Nicole Lane",
            "members": [
                {
                    "user_id": "admin-user-001",
                    "role": "admin",
                    "joined_at": now,
                    "verification_status": "admin_verified",
                    "verified_by": ["admin-user-001"]
                }
            ],
            "metadata": {
                "neighborhood_type": "subdivision",
                "hoa_name": "Nicole Lane",
                "city": "Loveland",
                "state": "OH",
                "zip": "45140",
                "boundaries": {
                    "streets": ["Nicole Lane"],
                    "zip": "45140"
                }
            },
            "created_at": now,
            "updated_at": now
        },
        
        # Open Neighborhood Example (radius-based)
        {
            "id": "pearl-district-004",
            "type": "neighborhood",
            "name": "Pearl District Neighborhood",
            "members": [],
            "metadata": {
                "neighborhood_type": "open_neighborhood",
                "center_lat": 45.5250,
                "center_lng": -122.6800,
                "radius_miles": 0.5
            },
            "created_at": now,
            "updated_at": now
        }
    ]
    
    for group in groups_data:
        group_id = group.pop("id")
        db.collection("groups").document(group_id).set(group)
    
    return {"message": f"Seeded {len(groups_data)} test groups (4 subdivisions + 1 open neighborhood)", "groups": [g["name"] for g in groups_data]}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(users.router)
app.include_router(events.router)
app.include_router(invitations.router)  # NEW: Event invitations (platform + SMS)
app.include_router(households.router)
app.include_router(people.router)
app.include_router(connections.router)
app.include_router(threads.router)  # NEW: Messaging threads
app.include_router(dev.router)  # ✅ Dev-only routes (seeding, testing)

# ✅ IMPORTANT:
# Frontend posts to {VITE_API_BASE_URL}/push/register
# so we mount push at /push/* (no /api prefix).
app.include_router(push.router)

# Universal groups API (households, activities, interests, etc.)
app.include_router(groups.router, prefix="/api")

# Optional profile router
try:
    from app.routes import profile as profile_module

    app.include_router(profile_module.router)
except Exception:
    # Legacy fallback (keep, but harmless if missing)
    try:
        import app_routes_profile as profile_module  # type: ignore

        app.include_router(profile_module.router)
    except Exception:
        pass
