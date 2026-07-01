from fastapi import FastAPI, UploadFile, File, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import tempfile
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from backend.services.speech_service import transcribe_audio
from backend.services.live_speech_service import transcribe_audio as transcribe_live_audio
from backend.services.emotion_detection import detect_emotion
from backend.services.risk_scoring import compute_risk_score
from backend.services.timeline_service import generate_timeline
from backend.services.language_detection import detect_language
from backend.services.entity_extraction import extract_financial_entities
from backend.services.summary_service import generate_summary
from backend.database.conversation_repo import (
    save_conversation,
    get_all_conversations,
    update_conversation,
    delete_conversation
)
from backend.config import CORS_ORIGINS, STREAMING_WINDOW_SIZE
from backend.realtime.events import TranscriptSegment
from backend.realtime.orchestrator import RealtimeOrchestrator
from backend.realtime.state_store import ConversationStateStore
from backend.realtime.ws_manager import WebSocketManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "data/sample_audio"
state_store = ConversationStateStore()
realtime_orchestrator = RealtimeOrchestrator(state_store, window_size=STREAMING_WINDOW_SIZE)
ws_manager = WebSocketManager()

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "finsense-backend"}


class StreamSegmentPayload(BaseModel):
    segment_id: Optional[str] = None
    sequence: int
    text: str
    is_final: bool = False
    confidence: float = 0.0
    speaker: Optional[str] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None


def _transcribe_chunk_to_segment(audio_path: str, session_id: str, sequence: int, language_hint: Optional[str] = None, is_final: bool = True):
    transcripts = transcribe_live_audio(audio_path, language_hint=language_hint)
    segment_text = transcripts.get("english_text") or transcripts.get("native_text") or ""
    return TranscriptSegment(
        session_id=session_id,
        segment_id=f"{session_id}-{sequence}",
        sequence=sequence,
        text=segment_text,
        is_final=is_final,
        confidence=1.0,
    )


@app.post("/stream/start")
async def start_stream():
    state = await realtime_orchestrator.start_session()
    return {
        "session_id": state.session_id,
        "websocket_url": f"/ws/live/{state.session_id}",
        "segment_url": f"/stream/segment/{state.session_id}",
    }


@app.post("/stream/segment/{session_id}")
async def stream_segment(session_id: str, payload: StreamSegmentPayload):
    segment = TranscriptSegment(
        session_id=session_id,
        segment_id=payload.segment_id or f"{session_id}-{payload.sequence}",
        sequence=payload.sequence,
        text=payload.text,
        is_final=payload.is_final,
        confidence=payload.confidence,
        speaker=payload.speaker,
        start_ms=payload.start_ms,
        end_ms=payload.end_ms,
    )
    state = await realtime_orchestrator.ingest_segment(segment)
    await ws_manager.broadcast(session_id, {"type": "state_update", "state": state.to_dict()})
    return state.to_dict()


@app.post("/stream/audio/{session_id}")
async def stream_audio_chunk(
    session_id: str,
    file: UploadFile = File(...),
    sequence: int = Form(...),
    language_hint: Optional[str] = Form(None),
    is_final: bool = Form(True),
):
    file_ext = os.path.splitext(file.filename or "chunk.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=UPLOAD_FOLDER) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        segment = _transcribe_chunk_to_segment(temp_path, session_id, sequence, language_hint=language_hint, is_final=is_final)
        state = await realtime_orchestrator.ingest_segment(segment)
        await ws_manager.broadcast(session_id, {"type": "state_update", "state": state.to_dict()})
        return {"success": True, "state": state.to_dict(), "segment": segment.to_dict()}
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.post("/stream/finalize/{session_id}")
async def finalize_stream(session_id: str):
    state = await realtime_orchestrator.finalize_session(session_id)
    
    final_text = state.final_transcript or state.latest_partial_text
    if final_text.strip():
        entities = list(state.entities.values())
        
        # Timeline service expects a dict for emotion: {"label": "..."}
        emotion_label = state.sentiment_timeline[-1].get("label") if state.sentiment_timeline else "Neutral"
        emotion_dict = {"label": emotion_label}
        
        risk = {"score": state.risk_score, "risk_level": "High" if state.risk_score >= 50 else "Moderate" if state.risk_score >= 20 else "Low"}
        
        timeline = generate_timeline(final_text, entities, emotion_dict, risk)
        
        record = {
            "transcript": final_text,
            "translated_transcript": final_text,
            "language": "🔴 Live Stream",
            "entities": entities,
            "summary": state.rolling_summary or {"topic": state.current_topic, "intent": state.current_intent},
            "emotion": emotion_label,
            "risk": risk,
            "timeline": timeline,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_conversation(record)
        
    await ws_manager.broadcast(session_id, {"type": "final_state", "state": state.to_dict()})
    return state.to_dict()


@app.websocket("/ws/live/{session_id}")
async def live_updates(websocket: WebSocket, session_id: str):
    await ws_manager.connect(session_id, websocket)
    try:
        current_state = await state_store.get_state(session_id)
        if current_state:
            await websocket.send_json({"type": "state_snapshot", "state": current_state.to_dict()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
    except Exception:
        ws_manager.disconnect(session_id, websocket)


@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...), language_hint: Optional[str] = Form(None)):

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    transcripts = transcribe_audio(file_path, language_hint=language_hint)
    native_transcript = transcripts["native_text"]
    english_transcript = transcripts["english_text"]

    # Use Whisper's audio-based detection (analyzes sound, not script characters)
    # Falls back to Unicode detection only if Whisper returns nothing
    language = transcripts.get("detected_language") or detect_language(native_transcript)

    # Use the English translation for NLP extracting to guarantee high precision
    entities = extract_financial_entities(english_transcript)
    summary = generate_summary(english_transcript)
    emotion = detect_emotion(english_transcript)
    risk = compute_risk_score(entities, emotion)

    # Save both transcripts into the timeline and record
    timeline = generate_timeline(native_transcript, entities, emotion, risk)

    record = {
        "transcript": native_transcript,
        "translated_transcript": english_transcript,
        "language": language,
        "entities": entities,
        "summary": summary,
        "emotion": emotion,
        "risk": risk,
        "timeline": timeline,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    save_conversation(record)
    
    # MongoDB injects a non-serializable ObjectId into the dict, so we cast it
    if "_id" in record:
        record["_id"] = str(record["_id"])

    return record


@app.get("/history")
def history():
    return get_all_conversations()


@app.post("/edit_conversation")
async def edit_conversation(request: Request):
    body = await request.json()
    doc_id = body.get("_id")
    if not doc_id:
        return {"success": False, "error": "Missing _id field"}
    
    success = update_conversation(doc_id, body)
    return {"success": success}


@app.post("/delete_conversation")
async def delete_conversation_endpoint(request: Request):
    body = await request.json()
    doc_id = body.get("_id")
    if not doc_id:
        return {"success": False, "error": "Missing _id field"}
    
    success = delete_conversation(doc_id)
    return {"success": success}