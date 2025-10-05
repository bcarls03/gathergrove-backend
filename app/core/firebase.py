import os
from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

def _expand_path(p: str) -> str:
    # expand ${VARS} and ~
    return os.path.expanduser(os.path.expandvars(p))

if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    cred_path = _expand_path(cred_path)
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(f"Service account JSON not found at: {cred_path!r}")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()
