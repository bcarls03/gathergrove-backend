# app/deps/auth.py
import os
from typing import Optional, Dict, Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

# Environment switches:
# - ALLOW_DEV_AUTH=1        → accept X-Uid/X-Email/X-Admin headers (local dev)
# - SKIP_FIREBASE_INIT=1    → don't initialize Admin SDK, use dev headers
# - SKIP_FIREBASE=1         → legacy toggle, treated same as above
# - CI=true                 → use dev headers/identity
# - otherwise               → require Firebase ID token (Authorization: Bearer <idToken>)
ALLOW_DEV = os.getenv("ALLOW_DEV_AUTH") == "1"
SKIP_INIT = os.getenv("SKIP_FIREBASE_INIT") == "1" or os.getenv("SKIP_FIREBASE") == "1"
IS_CI = os.getenv("CI") == "true"


def verify_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    # Dev-only headers (also exposed in Swagger)
    x_uid: Optional[str] = Header(None, alias="X-Uid", description="Dev-only: user UID"),
    x_email: Optional[str] = Header(None, alias="X-Email", description="Dev-only: user email"),
    x_admin: Optional[str] = Header(None, alias="X-Admin", description='Dev-only: "true"/"false"'),
) -> Dict[str, Any]:
    """
    DEV path (ALLOW_DEV_AUTH=1 or SKIP_FIREBASE_INIT=1 or CI=true):
      - Accept X-Uid/X-Email/X-Admin if provided; otherwise default to a safe dev identity.
      - IMPORTANT: Dev path must NOT require Bearer.
    PROD path:
      - Require Authorization: Bearer <idToken> and verify with firebase_admin.auth.
    """
    use_dev_path = ALLOW_DEV or SKIP_INIT or IS_CI

    # ✅ DEV PATH (no bearer required)
    if use_dev_path:
        uid = (x_uid or os.getenv("DEV_UID") or "dev-uid").strip()
        email = (x_email or os.getenv("DEV_EMAIL") or f"{uid}@example.com").strip()
        admin_raw = str(x_admin or os.getenv("DEV_ADMIN") or "false").strip().lower()
        admin = admin_raw in ("1", "true", "yes", "y", "on")
        return {"uid": uid, "email": email, "admin": admin}

    # 🔒 PROD PATH (bearer required)
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token>",
        )

    token = creds.credentials
    try:
        from firebase_admin import auth

        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return {
        "uid": decoded.get("uid") or decoded.get("user_id") or decoded.get("sub"),
        "email": decoded.get("email"),
        "admin": bool(decoded.get("admin")),
    }


def require_user(user: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """
    Convenience dependency for routes.
    Use as:
      user = Depends(require_user)
      viewer_uid = user["uid"]
    """
    if not user or not user.get("uid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return user


def get_current_user_uid(user: Dict[str, Any] = Depends(require_user)) -> str:
    """
    Convenience dependency that returns just the user's UID string.
    Use as:
      current_user_uid: str = Depends(get_current_user_uid)
    """
    return user["uid"]
