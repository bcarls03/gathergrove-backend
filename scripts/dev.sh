#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Enable dev auth mode (allows X-Dev-UID header)
export ALLOW_DEV_AUTH=1

# Point to Firebase credentials for real Firestore
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/secrets/gathergrove-dev-firebase-adminsdk.json"

# Remove SKIP_FIREBASE_INIT to use real Firestore instead of fake in-memory DB
# export SKIP_FIREBASE_INIT=1  # <-- COMMENTED OUT to use real Firestore

echo "🔥 Using real Firestore with credentials at: $GOOGLE_APPLICATION_CREDENTIALS"
echo "🚀 Starting backend on http://localhost:8000"
echo ""

.venv/bin/python3 -m uvicorn app.main:app --port 8000 --reload
