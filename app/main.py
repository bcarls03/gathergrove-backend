from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.firebase import db

app = FastAPI(title="GatherGrove Backend", version="0.1.0")
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
def root():
    return {"message": "GatherGrove API running"}

@app.get("/firebase", tags=["meta"])
def firebase_ping():
    """
    Writes a server timestamp to health/ping and returns it.
    Verifies that Firestore is reachable with the Admin SDK.
    """
    doc_ref = db.collection("health").document("ping")
    doc_ref.set({"updatedAt": firestore.SERVER_TIMESTAMP}, merge=True)
    snap = doc_ref.get()
    data = snap.to_dict() or {}
    ts = data.get("updatedAt")
    iso = ts.isoformat() if ts else None
    return {"ok": True, "updatedAt": iso}

# --- Auth setup & /whoami route ---

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

@app.get("/whoami", tags=["auth"])
def whoami(user=Depends(verify_token)):
    return {"uid": user["uid"], "email": user.get("email")}

from app.routes import users
app.include_router(users.router)

