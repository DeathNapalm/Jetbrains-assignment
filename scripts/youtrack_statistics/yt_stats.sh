#!/usr/bin/env bash
set -euo pipefail

YOUTRACK_URL="${YOUTRACK_URL:-http://localhost:8080}"
TOKEN="${YOUTRACK_TOKEN:-$(grep YOUTRACK_TOKEN "$(dirname "$0")/.env" | cut -d= -f2-)}"

auth=(-H "Authorization: Bearer $TOKEN" -H "Accept: application/json")

projects=$(curl -sf "$YOUTRACK_URL/api/admin/projects?\$top=100&fields=id" "${auth[@]}" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

users=$(curl -sf "$YOUTRACK_URL/api/users?\$top=1000&fields=id" "${auth[@]}" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")

issues=$(curl -sf -X POST "$YOUTRACK_URL/api/issuesGetter/count?fields=count" \
  "${auth[@]}" -H "Content-Type: application/json" -d '{"query":""}' \
  | python3 -c "import sys,json; c=json.load(sys.stdin)['count']; print(c if c >= 0 else '(still counting...)')")

echo "Projects : $projects"
echo "Users    : $users"
echo "Issues   : $issues"
