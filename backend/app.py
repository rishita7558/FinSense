from fastapi import FastAPI, UploadFile, File, Request, Form
import shutil
import os
from typing import Optional
from datetime import datetime

from backend.services.speech_service import transcribe_audio
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

app = FastAPI()

UPLOAD_FOLDER = "data/sample_audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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