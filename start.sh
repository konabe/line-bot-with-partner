#!/usr/bin/env bash
set -euo pipefail

: "Start script to run the application with gunicorn. Uses $PORT (default 8080)."
PORT=${PORT:-8080}
WORKERS=${WORKERS:-2}
THREADS=${THREADS:-4}
TIMEOUT=${TIMEOUT:-30}

exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WORKERS} --threads ${THREADS} --timeout ${TIMEOUT} "src.app:app"
