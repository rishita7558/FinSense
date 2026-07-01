#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${GHCR_IMAGE:?GHCR_IMAGE must be set}"
: "${GHCR_USERNAME:?GHCR_USERNAME must be set}"
: "${GHCR_TOKEN:?GHCR_TOKEN must be set}"
: "${GROQ_API_KEY:?GROQ_API_KEY must be set}"

printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin

docker compose -f deploy/docker-compose.prod.yml up -d mongo redis

docker compose -f deploy/docker-compose.prod.yml pull backend frontend
docker compose -f deploy/docker-compose.prod.yml up -d --no-deps --force-recreate backend
./scripts/verify_deployment.sh backend

docker compose -f deploy/docker-compose.prod.yml up -d --no-deps --force-recreate frontend
./scripts/verify_deployment.sh frontend
