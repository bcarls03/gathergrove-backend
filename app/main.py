# app/main.py
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.firebase import db  # real Firestore OR dev fake when SKIP_* is set
from app.deps.auth import verify_token  # auth lives here
from app.routes import events, households, people, push, users

app = FastAPI(title="GatherGrove Backend", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
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


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(users.router)
app.include_router(events.router)
app.include_router(households.router)
app.include_router(people.router)

# ✅ IMPORTANT:
# Frontend posts to {VITE_API_BASE_URL}/push/register
# so we mount push at /push/* (no /api prefix).
app.include_router(push.router)

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
