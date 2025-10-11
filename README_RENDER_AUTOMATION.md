# Render API automation

This repo includes two helper scripts to create and configure a Render service via the Render API.

Prerequisites
- A Render API key. Create one at https://dashboard.render.com/account/api-keys
- `curl` and `jq` (optional but helpful)

Files
- `scripts/render_create_service.sh` - creates a web service from this repo
- `scripts/render_set_env_vars.sh` - sets environment variables (LINE tokens, PORT)

Usage

1. Create a Render API key and export it:

```bash
export RENDER_API_KEY=your_api_key_here
```

2. Create the service (defaults can be overridden via environment variables):

```bash
# optional overrides: SERVICE_NAME, REPO_URL, BRANCH, PLAN, RUNTIME
./scripts/render_create_service.sh
```

The script outputs the API response; extract the `id` field as the SERVICE_ID for the next step.

3. Set environment variables for the service:

```bash
export SERVICE_ID=<service id from previous step>
export LINE_CHANNEL_SECRET=your_line_channel_secret
export LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
export PORT=8080
./scripts/render_set_env_vars.sh
```

Notes
- The scripts use Render API v1 endpoints. If the API changes, update the scripts accordingly.
- For security, secrets are sent as secure env vars. Never commit secrets to the repo.
