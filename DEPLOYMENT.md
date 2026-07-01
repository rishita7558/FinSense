# Deployment Guide

This project uses GitHub Actions for CI/CD and Docker for runtime packaging.

## Workflow Overview
- `CI` runs on pull requests and pushes to `main`.
- `Deploy` runs after a successful push to `main` and publishes the latest image to GHCR, then SSHes into the production server to update the stack.
- `Deploy` can also be triggered manually from the GitHub Actions tab with `workflow_dispatch`.

## Required GitHub Secrets
Set the following secrets in the repository settings:

- `GHCR_USERNAME` - username used for GHCR authentication on the production server
- `GHCR_TOKEN` - token with permission to pull from GHCR
- `GROQ_API_KEY` - required by the Capture Conversation flow
- `PROD_SSH_HOST` - production server hostname or IP
- `PROD_SSH_USER` - SSH username
- `PROD_SSH_KEY` - private SSH key for the production server
- `PROD_SSH_PORT` - SSH port, usually `22`
- `PROD_DEPLOY_PATH` - directory on the server where deployment files will be copied

The deployment script also consumes `GHCR_IMAGE`, which the workflow exports automatically as `ghcr.io/<owner>/finsense:latest` during rollout.

## Server Requirements
- Docker Engine and Docker Compose v2
- OpenSSH server access from GitHub Actions runners
- Outbound access to GHCR
- Ports `8000` and `8501` available, or mapped behind a reverse proxy

## Deployment Flow
1. Push code to `main`.
2. CI validates formatting, linting, tests, security checks, and Docker build.
3. The deploy workflow builds and pushes the image to GHCR.
4. The workflow copies the production compose file and scripts to the server over SSH.
5. The server logs in to GHCR, pulls the latest image, recreates backend and frontend containers, and verifies health endpoints.

## Production Compose
Use [deploy/docker-compose.prod.yml](deploy/docker-compose.prod.yml) on the server. It runs:
- MongoDB
- Redis
- Backend API
- Streamlit frontend

The same image is used for both backend and frontend containers, with different commands supplied by Docker Compose.

## Manual Rollback
To roll back, set `GHCR_IMAGE` to a previous image tag on the server and re-run `scripts/deploy.sh`.
