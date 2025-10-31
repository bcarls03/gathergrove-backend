#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://127.0.0.1:8000}
HDRS=(-H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false")
JSON='Content-Type: application/json'

echo "Health:" && curl -s "$BASE/health" && echo

echo "Create future event"
curl -s -X POST "$BASE/events" "${HDRS[@]}" -H "$JSON" \
  -d '{"type":"future","title":"Block Party","details":"test","category":"neighborhood","startAt":"2025-11-10T20:00:00Z","endAt":"2025-11-10T22:00:00Z"}' | jq .

ID=$(curl -s -X GET "$BASE/events" "${HDRS[@]}" \
  | python -c 'import sys,json; d=json.load(sys.stdin); items=d["items"] if isinstance(d,dict) else d; print(items[-1]["id"] if items else "")')

echo "Patch $ID"
curl -s -X PATCH "$BASE/events/$ID" "${HDRS[@]}" -H "$JSON" \
  -d '{"title":"Block Party (updated)","details":"updated details"}' | jq .

echo "Delete $ID"
curl -s -X DELETE "$BASE/events/$ID" "${HDRS[@]}" | jq .

echo "Cleanup leftovers"
for eid in $(curl -s -X GET "$BASE/events" "${HDRS[@]}" \
  | python -c 'import sys,json; d=json.load(sys.stdin); items=d["items"] if isinstance(d,dict) else d; print("\n".join(e["id"] for e in items))'); do
  echo "Deleting $eid"
  curl -s -X DELETE "$BASE/events/$eid" "${HDRS[@]}" >/dev/null
done

echo "Final list:"
curl -s -X GET "$BASE/events" "${HDRS[@]}" | jq .
