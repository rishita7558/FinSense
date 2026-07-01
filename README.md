# FinSense - Financial Conversation Intelligence

FinSense is a server-side, cloud-deployable platform for analyzing spoken financial conversations. It supports two execution modes:

- Capture Conversation: Groq-powered transcription and translation for batch audio uploads.
- Live Streaming: Real-time browser-based microphone capture powered by the ultra-fast Groq API for instantaneous insights.

The product stores conversation records in MongoDB, exposes a FastAPI backend, and renders operational and historical views in a professional, premium-grade Streamlit dashboard featuring modern glassmorphism and custom typography.

## Product Highlights
- Premium UI with glassmorphic elements, modern gradients, and responsive micro-animations.
- Batch audio analysis for uploaded recordings.
- Browser microphone live client for realtime sessions.
- Incremental transcript buffering with partial and final segment handling.
- Live financial insight updates for topic, intent, risk, sentiment, and entities.
- Editable conversation history with timeline visualization.
- Cloud-ready Docker deployment with Redis-backed state support.

## System Architecture
The application is built around a high-performance data pipeline spanning the frontend, backend, and external AI services:

- **1. User Interface (Streamlit)**: Serves as the presentation layer. Captures browser-based microphone audio or batch file uploads.
- **2. API Gateway (FastAPI)**: Routes incoming audio chunks and batch files to the appropriate transcription services.
- **3. AI Transcription (Groq API)**: Processes both batch uploads and live streaming audio using `Whisper-Large-V3` for near-instant speech-to-text.
- **4. Orchestration & NLP**: 
  - *Live Sessions*: Uses the Incremental Realtime Orchestrator to parse incoming transcripts on the fly.
  - *Offline Sessions*: Passes transcripts to Batch NLP Services for summarization and entity extraction.
- **5. State & Persistence**: Uses Redis (or in-memory) for real-time state management, and persists all finalized conversation records to MongoDB.
- **6. Real-time Feedback**: Streams live topic, intent, and risk analysis back to the dashboard via WebSockets.

## Technology Stack
- Frontend: Streamlit (Premium UI theme)
- Backend API: FastAPI + Uvicorn
- Transcription / Translation: Groq API (Whisper-Large-V3, Llama 3)
- Entity extraction: spaCy + rules
- State and caching: Redis, with in-memory fallback
- Persistence: MongoDB
- Deployment: Docker and Docker Compose

## Repository Layout
- `backend/` - API routes, services, realtime orchestrator, and persistence helpers
- `frontend/` - Streamlit dashboard and charting components
- `data/` - Local DB files, sample audio, and transcripts
- `logs/` - Service logs
- `scripts/` - Utility scripts and pipeline checks
- `notebooks/` - Model experiments and evaluation notebooks
- `start_app.py` - Local startup orchestration

## Prerequisites
- Python 3.10 or newer
- MongoDB for local development, or a reachable MongoDB instance in cloud deployments
- Groq API key (Required for both Capture Conversation and Live Streaming)
- Optional Redis instance for shared realtime state

## Local Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in the required values.
4. Optional, for local contributor tooling:
  ```bash
  pip install -r requirements-dev.txt
  ```
5. Start the full local stack:
   ```bash
   .\start.bat
   ```

This starts:
- MongoDB
- FastAPI backend at `http://127.0.0.1:8000`
- Streamlit dashboard at `http://localhost:8501`

## Environment Variables
Use this baseline configuration in `.env`:
```ini
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=armor
COLLECTION_NAME=conversations
GROQ_API_KEY=your_groq_api_key_here
REDIS_URL=
STREAMING_WINDOW_SIZE=8
API_URL=http://127.0.0.1:8000
```

Notes:
- `GROQ_API_KEY` is strictly required for both Batch uploads and Live Streaming.
- `REDIS_URL` is optional; if omitted, the app uses in-memory realtime state.
- `API_URL` lets the dashboard target a deployed backend.

## Running the Project
- Start the application locally with `start.bat`.
- Test the batch pipeline with:
  ```bash
  python scripts/run_pipeline.py
  ```
- Run the Docker deployment with:
  ```bash
  docker compose up --build
  ```

## Runtime Endpoints
- `POST /upload_audio` - Batch upload and analysis through Groq
- `POST /stream/start` - Start a realtime session
- `POST /stream/audio/{session_id}` - Upload browser mic chunks
- `POST /stream/segment/{session_id}` - Submit transcript segments directly
- `POST /stream/finalize/{session_id}` - Finalize and reconcile the realtime state
- `GET /history` - Fetch persisted conversations
- `WS /ws/live/{session_id}` - Subscribe to live state updates
- `POST /edit_conversation` - Update transcript fields
- `POST /delete_conversation` - Delete a conversation

## Deployment Notes
- The backend is containerized and can be deployed behind a reverse proxy.
- MongoDB and Redis can run as local services during development or managed services in production.
- For production, keep the FastAPI backend stateless and persist only session state and records in external services.

## CI/CD
The repository includes GitHub Actions workflows for continuous integration and automated deployment.

- `.github/workflows/ci.yml` runs formatting, linting, tests, security checks, and a Docker build on pull requests and pushes to `main`.
- `.github/workflows/deploy.yml` publishes the image to GHCR and deploys the latest release to the production server over SSH after a successful `main` push.
- [DEPLOYMENT.md](DEPLOYMENT.md) contains the required secrets, server prerequisites, and rollout flow.

## Troubleshooting
- The first model load may take longer while Whisper warms up.
- Ensure MongoDB is reachable before starting the backend.
- If Capture Conversation fails, confirm that `GROQ_API_KEY` is present in `.env`.

## Project Status
The repository is organized for a high-performance architecture: leveraging Groq's ultra-fast LPUs for all speech-to-text inference, a robust WebSocket realtime backend, and a premium Streamlit frontend designed for professional environments.