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

# Build payload. Note: Render's API fields may change; inspect API docs if this fails:
PAYLOAD=$(cat <<JSON
{
  "name": "$SERVICE_NAME",
  "service": "docker", 
  "type": "web",
  "repo": "$REPO_URL",
  "branch": "$BRANCH",
  "plan": "$PLAN",
  "autoDeploy": true,
  "envVars": [
    {"key": "PORT", "value": "$PORT"},
    {"key": "LINE_CHANNEL_SECRET", "value": "", "sync": false},
    {"key": "LINE_CHANNEL_ACCESS_TOKEN", "value": "", "sync": false}
  ]
}
JSON
)

# Show payload for review
echo "\n=== Request payload ==="
echo "$PAYLOAD" | jq . || echo "$PAYLOAD"

echo "\nSending request to Render API..."
HTTP_RESPONSE=$(curl -sS -w "\n%{http_code}" -X POST "$API_ENDPOINT" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD") || true

HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed -n '1,$p' | sed -n '1,$p' | sed -e '$d')
HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)

echo "HTTP $HTTP_CODE"
if [ "$HTTP_BODY" != "" ]; then
  echo "$HTTP_BODY" | jq . || echo "$HTTP_BODY"
fi

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  echo "Service created successfully (or request accepted)."
else
  echo "Service creation failed. Check the API response above and Render API docs."
fi

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
