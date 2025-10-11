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

# Build payload into a temporary file. Include ownerId if provided; otherwise try to discover it.
PAYLOAD_FILE=$(mktemp)
cat > "$PAYLOAD_FILE" <<JSON
{
  "name": "$SERVICE_NAME",
  "serviceType": "web",
  "ownerId": "${OWNER_ID:-}",
  "repo": "$REPO_URL",
  "branch": "$BRANCH",
  "plan": "$PLAN",
  "runtime": "docker",
  "autoDeploy": true
}
JSON

# If OWNER_ID not provided, try to discover via Render API
if [ -z "${OWNER_ID:-}" ]; then
  echo "OWNER_ID not set — trying to discover via /v1/services..."
  SERVICES_JSON=$(curl -sS -H "$AUTH_HEADER" -H "Accept: application/json" https://api.render.com/v1/services) || true
  if [ -n "$SERVICES_JSON" ] && command -v jq >/dev/null 2>&1; then
    # Try to extract first service.ownerId
    DISCOVERED_OWNER=$(echo "$SERVICES_JSON" | jq -r '.[0].service.ownerId // .[0].ownerId // empty') || true
    if [ -n "$DISCOVERED_OWNER" ]; then
      OWNER_ID="$DISCOVERED_OWNER"
      echo "Discovered ownerId from services: $OWNER_ID"
      jq --arg ownerId "$OWNER_ID" '.ownerId=$ownerId' "$PAYLOAD_FILE" > "$PAYLOAD_FILE.tmp" && mv "$PAYLOAD_FILE.tmp" "$PAYLOAD_FILE" || true
    else
      echo "Could not discover ownerId from services response. Please set OWNER_ID env var to your account/team id." >&2
    fi
  else
    echo "Could not query services or jq not available. Please set OWNER_ID env var manually." >&2
  fi
fi

# Validate JSON payload if jq available
if command -v jq >/dev/null 2>&1; then
  if ! jq empty "$PAYLOAD_FILE" 2>/dev/null; then
    echo "ERROR: Generated payload is not valid JSON" >&2
    echo "Payload was:" >&2
    cat "$PAYLOAD_FILE" >&2
    rm -f "$PAYLOAD_FILE"
    exit 1
  fi
fi

# Show payload for review
echo "\n=== Request payload ==="
if command -v jq >/dev/null 2>&1; then
  jq . "$PAYLOAD_FILE"
else
  cat "$PAYLOAD_FILE"
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
  -H "Accept: application/json" \
  --data-binary "@$PAYLOAD_FILE" ) || true

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
  # If server responded with invalid JSON, try alternative payload shapes
  BODY_CONTENT=$(cat "$TMPBODY") || true
  if echo "$BODY_CONTENT" | grep -qi "invalid json"; then
    echo "Server returned 'invalid JSON'. Trying alternative payload shapes..."
    # Fallback 1: use 'type' and 'env' fields
    FALLBACK1_FILE=$(mktemp)
    cat <<JSON > "$FALLBACK1_FILE"
{
  "name": "$SERVICE_NAME",
  "type": "web",
  "repo": "$REPO_URL",
  "branch": "$BRANCH",
  "plan": "$PLAN",
  "env": "docker",
  "autoDeploy": true
}
JSON
    echo "\n=== Fallback payload 1 ==="
    if command -v jq >/dev/null 2>&1; then jq . "$FALLBACK1_FILE"; else cat "$FALLBACK1_FILE"; fi
    HTTP_CODE_FB1=$(curl $CURL_OPTS -o "$TMPBODY" -w "%{http_code}" -X POST "$API_ENDPOINT" \
      -H "$AUTH_HEADER" -H "Content-Type: application/json" -H "Accept: application/json" --data-binary "@$FALLBACK1_FILE" ) || true
    echo "HTTP $HTTP_CODE_FB1"
    if [ "$HTTP_CODE_FB1" -ge 200 ] && [ "$HTTP_CODE_FB1" -lt 300 ]; then
      if command -v jq >/dev/null 2>&1; then SERVICE_ID=$(cat "$TMPBODY" | jq -r '.id // empty') || true; fi
      echo "Fallback 1 succeeded. Service id: ${SERVICE_ID:-(unknown)}"
      rm -f "$FALLBACK1_FILE"
      rm -f "$PAYLOAD_FILE"
      exit 0
    fi
    rm -f "$FALLBACK1_FILE"

    # Fallback 2: another variant
    FALLBACK2_FILE=$(mktemp)
    cat <<JSON > "$FALLBACK2_FILE"
{
  "name": "$SERVICE_NAME",
  "service": "web",
  "repo": "$REPO_URL",
  "branch": "$BRANCH",
  "plan": "$PLAN",
  "env": "docker",
  "autoDeploy": true
}
JSON
    echo "\n=== Fallback payload 2 ==="
    if command -v jq >/dev/null 2>&1; then jq . "$FALLBACK2_FILE"; else cat "$FALLBACK2_FILE"; fi
    HTTP_CODE_FB2=$(curl $CURL_OPTS -o "$TMPBODY" -w "%{http_code}" -X POST "$API_ENDPOINT" \
      -H "$AUTH_HEADER" -H "Content-Type: application/json" -H "Accept: application/json" --data-binary "@$FALLBACK2_FILE" ) || true
    echo "HTTP $HTTP_CODE_FB2"
    if [ "$HTTP_CODE_FB2" -ge 200 ] && [ "$HTTP_CODE_FB2" -lt 300 ]; then
      if command -v jq >/dev/null 2>&1; then SERVICE_ID=$(cat "$TMPBODY" | jq -r '.id // empty') || true; fi
      echo "Fallback 2 succeeded. Service id: ${SERVICE_ID:-(unknown)}"
      rm -f "$FALLBACK2_FILE"
      rm -f "$PAYLOAD_FILE"
      exit 0
    fi
    rm -f "$FALLBACK2_FILE"
  fi

  echo "Service creation failed. Check the API response above and Render API docs: https://render.com/docs/api"
fi

rm -f "$TMPBODY"
rm -f "$PAYLOAD_FILE"

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
