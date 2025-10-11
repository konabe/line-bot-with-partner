#!/usr/bin/env bash
set -euo pipefail

# Set environment variables for a Render service
# Usage:
#   RENDER_API_KEY=... SERVICE_ID=... ./scripts/render_set_env_vars.sh
# This script will set LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, PORT=8080

if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "ERROR: RENDER_API_KEY environment variable is required"
  exit 1
fi
if [ -z "${SERVICE_ID:-}" ]; then
  echo "ERROR: SERVICE_ID environment variable is required"
  exit 1
fi

API_URL="https://api.render.com/v1/services/${SERVICE_ID}/env-vars"

# Compose payload
cat <<-JSON > /tmp/env_payload.json
[
  { "key": "LINE_CHANNEL_SECRET", "value": "${LINE_CHANNEL_SECRET:-}", "secure": true },
  { "key": "LINE_CHANNEL_ACCESS_TOKEN", "value": "${LINE_CHANNEL_ACCESS_TOKEN:-}", "secure": true },
  { "key": "PORT", "value": "${PORT:-8080}", "secure": false }
]
JSON

echo "Setting environment variables for service ${SERVICE_ID}"

resp=$(curl -sS -X POST "$API_URL" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @/tmp/env_payload.json)

echo
echo "Response from Render API:"
echo "$resp"

echo "You can verify env vars in Render dashboard or via API."

exit 0
