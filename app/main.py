# app/main.py
import os
from typing import Optional

from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.firebase import db  # real Firestore OR dev fake when SKIP_FIREBASE=1

app = FastAPI(title="GatherGrove Backend", version="0.1.0")

# ----- CORS -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Auth (dev + prod) -----
security = HTTPBearer(auto_error=False)

def verify_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    # Dev-only headers (they’ll show up in Swagger)
    x_uid:   Optional[str] = Header(None, alias="X-Uid",   description="Dev-only: user UID"),
    x_email: Optional[str] = Header(None, alias="X-Email", description="Dev-only: user email"),
    x_admin: Optional[str] = Header(None, alias="X-Admin", description='Dev-only: "true"/"false"'),
):
    """
    DEV: if SKIP_FIREBASE=1, accept X-Uid/X-Email/X-Admin and skip Firebase.
    PROD: require Bearer token and verify with firebase_admin.
    """
    dev_mode = os.getenv("SKIP_FIREBASE") == "1"

    if dev_mode:
        uid = x_uid or "dev-uid"
        email = x_email or "dev@example.com"
        admin = str(x_admin or "false").lower() in ("1", "true", "yes", "y", "on")
        return {"uid": uid, "email": email, "admin": admin}

    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing Authorization: Bearer <token>")
    token = creds.credentials
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token")

    return {
        "uid": decoded["uid"],
        "email": decoded.get("email"),
        "admin": bool(decoded.get("admin", False)),
    }

# ----- Meta routes -----
@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
def root():
    return {"message": "GatherGrove API running"}

@app.get("/firebase", tags=["meta"], summary="Firebase Ping")
def firebase_ping():
    # Works with dev fake and real Firestore
    list(db.collections())
    return {"ok": True}

@app.get("/whoami", tags=["auth"], summary="Whoami")
def whoami(claims=Depends(verify_token)):
    return claims

# ----- Mount routers after verify_token is defined -----
from app.routes import users
app.include_router(users.router)
