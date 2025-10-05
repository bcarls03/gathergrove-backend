from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.firebase import db
from firebase_admin import firestore

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