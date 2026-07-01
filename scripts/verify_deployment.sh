#!/usr/bin/env bash
set -euo pipefail

TARGET_SERVICE="${1:-backend}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000/health}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8501/_stcore/health}"

retry_check() {
  local url="$1"
  local label="$2"
  local attempts=20
  local delay=3

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null; then
      echo "$label is healthy"
      return 0
    fi
    sleep "$delay"
  done

  echo "$label failed health verification" >&2
  return 1
}

if [[ "$TARGET_SERVICE" == "backend" ]]; then
  retry_check "$BACKEND_URL" "Backend"
elif [[ "$TARGET_SERVICE" == "frontend" ]]; then
  retry_check "$FRONTEND_URL" "Frontend"
else
  retry_check "$BACKEND_URL" "Backend"
  retry_check "$FRONTEND_URL" "Frontend"
fi
