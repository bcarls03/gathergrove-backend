#!/usr/bin/env bash
set -euo pipefail
export ALLOW_DEV_AUTH=1
export SKIP_FIREBASE_INIT=1
export CI=true
python -m uvicorn app.main:app --port 8000 --reload
