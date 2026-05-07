# FinSense - Financial Conversation Intelligence

FinSense is a local full-stack app for analyzing spoken financial conversations. It records or uploads audio, transcribes and translates speech, extracts financial entities, summarizes intent, and scores risk. The system stores conversations in MongoDB and visualizes timelines in a Streamlit dashboard.

## Features
- Audio capture or upload (Streamlit)
- Multilingual transcription + English translation (Groq Whisper + LLaMa)
- Financial entity extraction (spaCy + LLM supplement)
- Summary, emotion, and risk scoring
- Conversation history with editable transcripts
- Timeline visualization

## Architecture
- Frontend: Streamlit dashboard at `frontend/dashboard.py`
- Backend: FastAPI service at `backend/app.py`
- Database: Local MongoDB (data stored in `data/db`)
- Models/services: `backend/services/*`

## Quick Start (Windows)
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your Groq API key in `.env` (see below).
4. Run the unified startup script:
   ```bash
   .\start.bat
   ```

This launches:
- MongoDB
- FastAPI backend (http://127.0.0.1:8000)
- Streamlit frontend (http://localhost:8501)

## Environment Variables
Create a `.env` file in the repo root:
```
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=armor
COLLECTION_NAME=conversations
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=
```
Notes:
- `GROQ_API_KEY` is required for transcription/translation.
- `OPENAI_API_KEY` is optional and currently unused by default services.

## API Endpoints
- `POST /upload_audio` - Upload audio and get analysis
- `GET /history` - Fetch all conversations
- `POST /edit_conversation` - Update transcript/translation fields
- `POST /delete_conversation` - Delete a conversation by `_id`

## Example Pipeline Test
You can test the backend with a sample audio file:
```bash
python scripts/run_pipeline.py
```

## Troubleshooting
- If Streamlit warns about missing Groq key, set `GROQ_API_KEY` in `.env` and refresh.
- First run can be slow due to model downloads and warmup.
- Ensure `mongod` is available on PATH for local MongoDB startup.

## Project Layout
- `backend/` - API, services, DB access
- `frontend/` - Streamlit UI and charts
- `data/` - Local DB files, audio, transcripts
- `logs/` - Service logs
- `scripts/` - Utility scripts
- `start_app.py` - Unified launcher