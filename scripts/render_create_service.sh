#!/usr/bin/env bash
set -euo pipefail

# Render API service creation script
# Usage:
#   RENDER_API_KEY=... ./scripts/render_create_service.sh
# Optional env vars:
#   SERVICE_NAME (default: mcp-server)
#   REPO_URL (default: https://github.com/konabe/line-bot-with-partner.git)
#   BRANCH (default: main)
#   PLAN (default: free)
#   RUNTIME (default: docker)

if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "ERROR: RENDER_API_KEY environment variable is required"
  exit 1
fi

SERVICE_NAME="${SERVICE_NAME:-mcp-server}"
REPO_URL="${REPO_URL:-https://github.com/konabe/line-bot-with-partner.git}"
BRANCH="${BRANCH:-main}"
PLAN="${PLAN:-starter}"
RUNTIME="${RUNTIME:-docker}"

API_URL="https://api.render.com/v1/services"

cat <<-JSON > /tmp/render_service_payload.json
{
  "name": "${SERVICE_NAME}",
  "serviceType": "web",
  "repo": "${REPO_URL}",
  "branch": "${BRANCH}",
  "plan": "${PLAN}",
  "runtime": "${RUNTIME}",
  "autoDeploy": true
}
JSON

echo "Creating Render service '${SERVICE_NAME}' from '${REPO_URL}' (branch=${BRANCH}, plan=${PLAN}, runtime=${RUNTIME})"

resp=$(curl -sS -X POST "$API_URL" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @/tmp/render_service_payload.json)

echo
echo "Response from Render API:"
echo "$resp"

echo
echo "If creation succeeded the response JSON should include the created service ID and details."

echo "Example: extract service id with jq (if installed):"
echo "  echo '$resp' | jq -r '.id'"

echo "Next: set environment variables with scripts/render_set_env_vars.sh"

exit 0
