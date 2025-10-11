#!/usr/bin/env bash
set -euo pipefail

# Usage: RENDER_API_KEY must be set in the environment
# Optionally set: SERVICE_NAME, PLAN (free), BRANCH (main), PORT (8080)

: "${RENDER_API_KEY?Please set RENDER_API_KEY environment variable (create it in Render dashboard -> API Keys)}"
SERVICE_NAME="${SERVICE_NAME:-mcp-server}"
PLAN="${PLAN:-free}"
BRANCH="${BRANCH:-main}"
PORT="${PORT:-8080}"
REPO_URL="$(git config --get remote.origin.url || true)"

if [ -z "$REPO_URL" ]; then
  echo "Could not detect git remote origin. Please set REPO_URL environment variable to your repo (e.g. https://github.com/owner/repo)"
  exit 1
fi

# Normalize git@github.com:owner/repo.git -> https://github.com/owner/repo
if [[ "$REPO_URL" =~ ^git@ ]]; then
  REPO_URL="${REPO_URL/git@github.com:/https://github.com/}"
fi
REPO_URL="${REPO_URL%.git}"

API_ENDPOINT="https://api.render.com/v1/services"
AUTH_HEADER="Authorization: Bearer ${RENDER_API_KEY}"

# DEBUG mode: set DEBUG=1 to enable curl verbose output and show the curl command
if [ "${DEBUG:-0}" != "0" ]; then
  CURL_OPTS="-v"
else
  CURL_OPTS="-sS"
fi

cat <<-EOF
Will create Render service with the following settings:
  SERVICE_NAME: $SERVICE_NAME
  REPO_URL: $REPO_URL
  BRANCH: $BRANCH
  PLAN: $PLAN
  PORT: $PORT

This will call Render API endpoint: $API_ENDPOINT
Proceed? (y/N)
EOF
read -r CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted by user"
  exit 0
fi

# Build payload using Render API expected fields. If the API schema changes, update accordingly.
PAYLOAD=$(cat <<JSON
{
  "name": "$SERVICE_NAME",
  "serviceType": "web",
  "repo": "$REPO_URL",
  "branch": "$BRANCH",
  "plan": "$PLAN",
  "runtime": "docker",
  "autoDeploy": true
}
JSON
)

# Show payload for review
echo "\n=== Request payload ==="
if command -v jq >/dev/null 2>&1; then
  echo "$PAYLOAD" | jq .
else
  echo "$PAYLOAD"
fi

echo "\nSending request to Render API..."
# Use a temp file for body to safely separate http code
TMPBODY=$(mktemp)
if [ "${DEBUG:-0}" != "0" ]; then
  echo "Running curl with options: $CURL_OPTS -X POST $API_ENDPOINT"
  echo "Request body:" >&2
  echo "$PAYLOAD" | sed -n '1,200p' >&2
fi

HTTP_CODE=$(curl $CURL_OPTS -o "$TMPBODY" -w "%{http_code}" -X POST "$API_ENDPOINT" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" ) || true

echo "HTTP $HTTP_CODE"
if [ -s "$TMPBODY" ]; then
  if command -v jq >/dev/null 2>&1; then
    cat "$TMPBODY" | jq . || cat "$TMPBODY"
  else
    cat "$TMPBODY"
  fi
else
  echo "(no response body)"
fi

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  # Try to extract id if jq available
  if command -v jq >/dev/null 2>&1; then
    SERVICE_ID=$(cat "$TMPBODY" | jq -r '.id // empty') || true
    if [ -n "$SERVICE_ID" ]; then
      echo "Service created with id: $SERVICE_ID"
      echo "You can now set env vars with: SERVICE_ID=$SERVICE_ID RENDER_API_KEY=... ./scripts/render_set_env_vars.sh"
    fi
  fi
  echo "Service create request succeeded."
else
  echo "Service creation failed. Check the API response above and Render API docs: https://render.com/docs/api"
fi

rm -f "$TMPBODY"

# Notes for user
cat <<NOTES

Notes:
- If the API call fails, confirm the exact request shape in Render's API docs: https://render.com/docs/api
- After creation, go to Render dashboard, set the actual values for LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN (or re-run with those values in envVars)
- You can set environment variables before running this script, e.g.
  export RENDER_API_KEY=... \
         SERVICE_NAME=my-line-bot \
         BRANCH=main \
         PLAN=free
  ./scripts/create_render_service.sh

NOTES
