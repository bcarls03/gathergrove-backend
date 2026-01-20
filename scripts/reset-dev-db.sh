#!/usr/bin/env bash
# Reset the development database (in-memory fake DB)
# Usage: ./scripts/reset-dev-db.sh

set -euo pipefail

echo "🔄 Resetting dev database..."
curl -X POST http://localhost:8000/dev/reset-db -H "Content-Type: application/json" | python3 -m json.tool

echo ""
echo "✅ Dev database reset complete!"
echo "   You can now test onboarding from scratch."
