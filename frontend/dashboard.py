import streamlit as st
import requests
import time
from timeline_chart import create_timeline_chart

API = "http://127.0.0.1:8000"

def fetch_with_retry(method, endpoint, retries=5, delay=3, **kwargs):
    """Attempt an HTTP request multiple times if connection fails (e.g. backend still booting)."""
    for attempt in range(retries):
        try:
            if method == "GET":
                resp = requests.get(f"{API}{endpoint}", **kwargs)
            else:
                resp = requests.post(f"{API}{endpoint}", **kwargs)
            return resp
        except requests.exceptions.ConnectionError:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

from backend.config import GROQ_API_KEY
import os

st.set_page_config(page_title="FinSense - Financial Conversations", layout="wide")

st.title("FinSense – Financial Conversation Intelligence")
st.markdown("Record or upload financial discussions to track decisions, extract insights, and assess risks.")

if not GROQ_API_KEY:
    st.warning("⚠️ Groq API Key Not Found! Please enter your free API Key below to enable ultra-fast transcription and analysis.")
    new_key = st.text_input("Groq API Key (gsk_...)", type="password")
    if new_key:
        with open(".env", "a") as f:
            f.write(f"\nGROQ_API_KEY={new_key}")
        st.success("API Key saved! Please refresh the page.")
    st.stop()

if "result" not in st.session_state:
    st.session_state.result = None

tab1, tab2 = st.tabs(["Capture Conversation", "Conversation History"])

with tab1:
    col_upload, col_record = st.columns(2)
    
    with col_upload:
        st.subheader("Upload Audio")
        uploaded_file = st.file_uploader("Upload an existing audio file (.wav, .mp3)", type=["wav", "mp3"])
        
    with col_record:
        st.subheader("Record Audio")
        audio_value = st.audio_input("Record a financial conversation directly")

    audio_to_process = audio_value or uploaded_file

    # Language hint selector for better regional accuracy
    lang_options = {
        "Auto-Detect": "",
        "Telugu": "te",
        "Hindi": "hi",
        "Tamil": "ta",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Marathi": "mr",
        "Bengali": "bn",
        "Gujarati": "gu",
        "English": "en",
        "Tinglish (Telugu+English)": "te",
        "Hinglish (Hindi+English)": "hi"
    }
    selected_lang = st.selectbox(
        "🌐 Select spoken language (improves accuracy for regional languages)",
        options=list(lang_options.keys()),
        index=0
    )
    lang_hint = lang_options[selected_lang]

    if audio_to_process and st.button("Analyze Conversation", type="primary"):
        with st.spinner("Transcribing and extracting insights (this may take a minute as AI models load)..."):
            try:
                filename = getattr(audio_to_process, "name", "recording.wav")
                
                # Send language hint alongside the audio file
                form_data = {}
                if lang_hint:
                    form_data["language_hint"] = (None, lang_hint)
                    
                response = fetch_with_retry(
                    "POST", 
                    "/upload_audio",
                    retries=8,
                    delay=6,
                    files={"file": (filename, audio_to_process.getvalue()), **form_data}
                )
                if response.status_code == 200:
                    st.session_state.result = response.json()
                    st.success("Analysis complete!")
                else:
                    st.error(f"Error from backend: {response.text}")
            except Exception as e:
                st.error("Backend Server is still starting up. Please try again in 10 seconds.")

    if st.session_state.result:
        res = st.session_state.result
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📜 Transcript")
            
            st.markdown("**Native Audio Script:**")
            edited_native = st.text_area(
                "Edit native transcript",
                value=res.get("transcript", ""),
                key="capture_native",
                height=120,
                label_visibility="collapsed"
            )
            
            st.markdown("**English Translation:**")
            edited_english = st.text_area(
                "Edit English translation",
                value=res.get("translated_transcript", ""),
                key="capture_english",
                height=120,
                label_visibility="collapsed"
            )
            
            # Save edits button
            doc_id = res.get("_id")
            if doc_id and st.button("💾 Save Transcript Edits", key="save_capture"):
                try:
                    save_resp = requests.post(f"{API}/edit_conversation", json={
                        "_id": doc_id,
                        "transcript": edited_native,
                        "translated_transcript": edited_english
                    })
                    if save_resp.status_code == 200 and save_resp.json().get("success"):
                        st.success("Transcript edits saved!")
                        res["transcript"] = edited_native
                        res["translated_transcript"] = edited_english
                    else:
                        st.error("Failed to save edits.")
                except Exception as e:
                    st.error(f"Error saving: {e}")
            
            st.markdown("**Captured Entities:**")
            entities = res.get("entities", [])
            formatted_entities = []
            for e in entities:
                keyword = e.get("entity", "").title() if isinstance(e, dict) else str(e).title()
                amount = e.get("amount", "") if isinstance(e, dict) else ""
                formatted_entities.append(f"{keyword} ({amount})" if amount else keyword)
            st.warning(", ".join(formatted_entities) if formatted_entities else "None detected")
            
            st.subheader("🏷️ Extracted Details")
            st.write("**Language:**", res.get("language", "Unknown"))
            
        with col2:
            st.subheader("💡 AI Structured Insights")
            summary = res.get("summary", {})
            
            if isinstance(summary, dict):
                st.write(f"**Topic:** {summary.get('topic', 'N/A')}")
                st.write(f"**Intent:** {summary.get('intent', 'N/A')}")
                
                decisions = summary.get('decisions', [])
                if decisions:
                    st.write("**Decisions:**")
                    for d in decisions:
                        st.write(f"- {d}")
                        
                risks = summary.get('risks', [])
                if risks:
                    st.write("**Identified Risks:**")
                    for r in risks:
                        st.error(f"- {r}")
            else:
                st.success(summary)
            
            st.subheader("📊 Quantitative Risk")
            st.write("**Emotion:**", res.get("emotion", "Neutral"))
            st.write("**Risk Score:**", str(res.get("risk", {}).get("score", "N/A")))
            
with tab2:
    st.subheader("Conversation History")
    
    if st.button("Refresh History", type="primary"):
        try:
            with st.spinner("Fetching conversations from database..."):
                response = fetch_with_retry("GET", "/history", retries=8, delay=6)
            
            if response.status_code == 200:
                st.session_state["history_data"] = response.json()
            else:
                st.error("Failed to fetch history.")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

    data = st.session_state.get("history_data", [])
    
    if data:
        timeline_data = []
        
        for idx, conv in enumerate(data):
            doc_id = conv.get("_id", "")
            language = conv.get("language", "")
            timestamp = conv.get("created_at", "")
            
            # ── Card container ──
            with st.container(border=True):
                # Title row
                meta_parts = []
                if language:
                    meta_parts.append(language)
                if timestamp:
                    meta_parts.append(timestamp)
                st.caption(f"Conversation {idx + 1}  —  {' · '.join(meta_parts)}" if meta_parts else f"Conversation {idx + 1}")
                
                # Two-column layout: transcripts on left, insights on right
                left, right = st.columns(2)
                
                with left:
                    edited_transcript = st.text_area(
                        "Native Transcript",
                        value=conv.get("transcript", ""),
                        key=f"transcript_{idx}",
                        height=90
                    )
                    edited_translation = st.text_area(
                        "English Translation",
                        value=conv.get("translated_transcript", ""),
                        key=f"translation_{idx}",
                        height=90
                    )
                
                with right:
                    # Entities
                    entities = conv.get("entities", [])
                    ent_parts = []
                    for e in entities:
                        if isinstance(e, dict):
                            kw = e.get("entity", "").title()
                            amt = e.get("amount", "")
                            ent_parts.append(f"{kw} ({amt})" if amt else kw)
                        else:
                            ent_parts.append(str(e).title())
                    st.write(f"**Entities:** {', '.join(ent_parts) if ent_parts else 'None'}")
                    
                    # Summary
                    summary = conv.get("summary", {})
                    if isinstance(summary, dict):
                        st.write(f"**Topic:** {summary.get('topic', 'N/A')}")
                        st.write(f"**Intent:** {summary.get('intent', 'N/A')}")
                    
                    risk = conv.get("risk", {})
                    risk_text = str(risk.get("risk_level", "Low")) if isinstance(risk, dict) else str(risk)
                    st.write(f"**Risk:** {risk_text}")
                    st.write(f"**Emotion:** {conv.get('emotion', 'Neutral')}")
                
                # Action buttons
                save_col, del_col, spacer = st.columns([1, 1, 4])
                with save_col:
                    if st.button("Save Changes", key=f"save_{idx}"):
                        if doc_id:
                            payload = {
                                "_id": doc_id,
                                "transcript": edited_transcript,
                                "translated_transcript": edited_translation
                            }
                            try:
                                save_resp = requests.post(f"{API}/edit_conversation", json=payload)
                                if save_resp.status_code == 200 and save_resp.json().get("success"):
                                    st.success("Saved.")
                                else:
                                    st.error("Failed to save.")
                            except Exception as e:
                                st.error(f"Error: {e}")
                
                with del_col:
                    if st.button("Delete", key=f"del_{idx}"):
                        if doc_id:
                            try:
                                del_resp = requests.post(f"{API}/delete_conversation", json={"_id": doc_id})
                                if del_resp.status_code == 200 and del_resp.json().get("success"):
                                    st.session_state["history_data"].pop(idx)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete.")
                            except Exception as e:
                                st.error(f"Error: {e}")
            
            if "timeline" in conv:
                timeline_data.append(conv["timeline"])
        
        if timeline_data:
            st.subheader("Risk & Emotion Timeline")
            try:
                chart = create_timeline_chart(timeline_data)
                st.plotly_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Could not render timeline: {e}")
    elif st.session_state.get("history_data") is not None:
        st.info("No conversations recorded yet.")