import os
import time

import requests
import streamlit as st
import streamlit.components.v1 as components
from timeline_chart import create_timeline_chart

from backend.config import GROQ_API_KEY

API = os.getenv("API_URL", "http://127.0.0.1:8000")


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


st.set_page_config(page_title="FinSense - Financial Conversations", layout="wide")

st.title("FinSense – Financial Conversation Intelligence")
st.markdown(
    "Record or upload financial discussions to track decisions, extract insights, and assess risks."
)

if "result" not in st.session_state:
    st.session_state.result = None

tab1, tab2, tab3 = st.tabs(["Capture Conversation", "Conversation History", "Live Streaming"])

with tab1:
    if not GROQ_API_KEY:
        st.warning(
            "Capture Conversation requires a Groq API key. Live Streaming remains available without it."
        )

    col_upload, col_record = st.columns(2)

    with col_upload:
        st.subheader("Upload Audio")
        uploaded_file = st.file_uploader(
            "Upload an existing audio file (.wav, .mp3)", type=["wav", "mp3"]
        )

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
        "Hinglish (Hindi+English)": "hi",
    }
    selected_lang = st.selectbox(
        "🌐 Select spoken language (improves accuracy for regional languages)",
        options=list(lang_options.keys()),
        index=0,
    )
    lang_hint = lang_options[selected_lang]

    if audio_to_process and st.button(
        "Analyze Conversation", type="primary", disabled=not GROQ_API_KEY
    ):
        with st.spinner(
            "Transcribing and extracting insights (this may take a minute as AI models load)..."
        ):
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
                    files={"file": (filename, audio_to_process.getvalue()), **form_data},
                )
                if response.status_code == 200:
                    st.session_state.result = response.json()
                    st.success("Analysis complete!")
                else:
                    st.error(f"Error from backend: {response.text}")
            except Exception as e:
                st.error(f"Backend Server error: {e}")

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
                key=f"capture_native_{res.get('_id', 'temp')}",
                height=120,
                label_visibility="collapsed",
            )

            st.markdown("**English Translation:**")
            edited_english = st.text_area(
                "Edit English translation",
                value=res.get("translated_transcript", ""),
                key=f"capture_english_{res.get('_id', 'temp')}",
                height=120,
                label_visibility="collapsed",
            )

            # Save edits button
            doc_id = res.get("_id")
            if doc_id and st.button("💾 Save Transcript Edits", key=f"save_capture_{doc_id}"):
                try:
                    save_resp = requests.post(
                        f"{API}/edit_conversation",
                        json={
                            "_id": doc_id,
                            "transcript": edited_native,
                            "translated_transcript": edited_english,
                        },
                    )
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

                decisions = summary.get("decisions", [])
                if decisions:
                    st.write("**Decisions:**")
                    for d in decisions:
                        st.write(f"- {d}")

                risks = summary.get("risks", [])
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
                st.caption(
                    f"Conversation {idx + 1}  —  {' · '.join(meta_parts)}"
                    if meta_parts
                    else f"Conversation {idx + 1}"
                )

                # Two-column layout: transcripts on left, insights on right
                left, right = st.columns(2)

                with left:
                    edited_transcript = st.text_area(
                        "Native Transcript",
                        value=conv.get("transcript", ""),
                        key=f"transcript_{doc_id}",
                        height=90,
                    )
                    edited_translation = st.text_area(
                        "English Translation",
                        value=conv.get("translated_transcript", ""),
                        key=f"translation_{doc_id}",
                        height=90,
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
                    risk_text = (
                        str(risk.get("risk_level", "Low")) if isinstance(risk, dict) else str(risk)
                    )
                    st.write(f"**Risk:** {risk_text}")
                    st.write(f"**Emotion:** {conv.get('emotion', 'Neutral')}")

                # Action buttons
                save_col, del_col, spacer = st.columns([1, 1, 4])
                with save_col:
                    if st.button("Save Changes", key=f"save_{doc_id}"):
                        if doc_id:
                            payload = {
                                "_id": doc_id,
                                "transcript": edited_transcript,
                                "translated_transcript": edited_translation,
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
                    if st.button("Delete", key=f"del_{doc_id}"):
                        if doc_id:
                            try:
                                del_resp = requests.post(
                                    f"{API}/delete_conversation", json={"_id": doc_id}
                                )
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


with tab3:
    st.subheader("Live Streaming Session")
    st.caption(
        "Start a session, record from your browser, and watch transcript and insight updates arrive in real time."
    )

    live_html = f"""
        <style>
            :root {{
                --bg-color: #ffffff;
                --text-color: #31333F;
                --card-bg: #f0f2f6;
                --border-color: #e6e9ef;
                --primary: #ff4b4b;
            }}
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --bg-color: #0e1117;
                    --text-color: #fafafa;
                    --card-bg: #262730;
                    --border-color: #333333;
                }}
            }}
            body {{ margin: 0; background-color: transparent; color: var(--text-color); }}
            .fs-live {{ font-family: "Source Sans Pro", sans-serif; padding: 0px; }}
            .fs-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px; }}
            .fs-card {{ flex:1 1 180px; background: var(--card-bg); padding:16px; border-radius:8px; min-height:72px; border: 1px solid var(--border-color); }}
            .fs-label {{ font-size:14px; opacity:0.7; margin-bottom:4px; }}
            .fs-value {{ font-size:20px; font-weight:600; word-break:break-word; }}
            .fs-controls {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0; }}
            .fs-button {{ background: var(--primary); color: white; border:none; border-radius:8px; padding:10px 16px; font-weight:600; cursor:pointer; }}
            .fs-button.secondary {{ background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border-color); }}
            .fs-button:disabled {{ opacity:0.5; cursor:not-allowed; }}
            .fs-textbox {{ background: var(--bg-color); border:1px solid var(--border-color); border-radius:8px; padding:16px; min-height:120px; white-space:pre-wrap; }}
            .fs-status {{ font-size:14px; opacity:0.7; margin-top:8px; }}
            .fs-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-top:12px; }}
            input.fs-input {{ width:100%; padding:10px 12px; border-radius:8px; border:1px solid var(--border-color); background: var(--bg-color); color: var(--text-color); }}
        </style>
        <div class="fs-live">
            <div class="fs-row">
                <div class="fs-card"><div class="fs-label">Session</div><div class="fs-value" id="fs-session">Not started</div></div>
                <div class="fs-card"><div class="fs-label">Current Topic</div><div class="fs-value" id="fs-topic">-</div></div>
                <div class="fs-card"><div class="fs-label">Detected Intent</div><div class="fs-value" id="fs-intent">-</div></div>
                <div class="fs-card"><div class="fs-label">Risk Level</div><div class="fs-value" id="fs-risk">-</div></div>
            </div>
            <div class="fs-grid">
                <div class="fs-card"><div class="fs-label">Sentiment</div><div class="fs-value" id="fs-sentiment">-</div></div>
                <div class="fs-card"><div class="fs-label">Entities</div><div class="fs-value" id="fs-entities">0</div></div>
                <div class="fs-card"><div class="fs-label">Confidence</div><div class="fs-value" id="fs-confidence">0%</div></div>
                <div class="fs-card"><div class="fs-label">Duration</div><div class="fs-value" id="fs-duration">0s</div></div>
            </div>
            <div class="fs-controls">
                <input id="fs-language" class="fs-input" placeholder="Language hint e.g. en, hi, te (optional)" />
                <button class="fs-button" id="fs-start">Start Session</button>
                <button class="fs-button secondary" id="fs-stop" disabled>Stop</button>
            </div>
            <div class="fs-textbox" id="fs-transcript">Transcript will appear here...</div>
            <div class="fs-status" id="fs-status">Idle.</div>
        </div>
        <script>
            (function() {{
                const configuredApiBase = {API!r};
                let pageOrigin = window.location.origin;
                if (!pageOrigin || pageOrigin === "null" || pageOrigin === "about://srcdoc") {{
                    try {{
                        pageOrigin = window.parent.location.origin;
                    }} catch (e) {{
                        pageOrigin = "http://localhost:8501";
                    }}
                }}
                const pageMappedBackend = pageOrigin.includes('8501') ? pageOrigin.replace('8501', '8000') : pageOrigin;
                const apiBase = pageMappedBackend || configuredApiBase;
                let sessionId = null;
                let ws = null;
                let recorder = null;
                let stream = null;
                let chunkIndex = 0;
                let startTime = null;
                let chunkTimer = null;
                let pendingSessionId = null;
                let audioChunks = [];

                const el = (id) => document.getElementById(id);
                const setStatus = (text) => el('fs-status').textContent = text;
                const setValue = (id, text) => el(id).textContent = text;

                function updateFromState(state) {{
                    setValue('fs-session', state.session_id || sessionId || 'Unknown');
                    setValue('fs-topic', state.current_topic || '-');
                    setValue('fs-intent', state.current_intent || '-');
                    setValue('fs-risk', state.risk_score >= 50 ? 'High' : state.risk_score >= 20 ? 'Moderate' : 'Low');
                    const lastSentiment = state.sentiment_timeline && state.sentiment_timeline.length ? state.sentiment_timeline[state.sentiment_timeline.length - 1] : null;
                    setValue('fs-sentiment', lastSentiment ? `${{lastSentiment.label}} (${{lastSentiment.score}})` : '-');
                    const entityCount = state.entities ? Object.keys(state.entities).length : 0;
                    setValue('fs-entities', String(entityCount));
                    setValue('fs-confidence', `${{Math.round((state.confidence_score || 0) * 100)}}%`);
                    if (startTime) {{
                        const seconds = Math.max(0, Math.round((Date.now() - startTime) / 1000));
                        setValue('fs-duration', `${{seconds}}s`);
                    }}
                    const transcript = state.final_transcript || state.latest_partial_text || '';
                    el('fs-transcript').textContent = transcript || 'Transcript will appear here...';
                }}

                async function startSession() {{
                    sessionId = pendingSessionId || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : `session-${{Date.now()}}-${{Math.random().toString(16).slice(2)}}`);
                    startTime = Date.now();
                    chunkIndex = 0;
                    setValue('fs-session', sessionId);
                    setStatus('Session started locally. Connecting microphone...');
                                        const wsBase = apiBase.startsWith('https://') ? apiBase.replace('https://', 'wss://') : apiBase.replace('http://', 'ws://');
                                        ws = new WebSocket(wsBase + `/ws/live/${{sessionId}}`);
                    ws.onmessage = (event) => {{
                        try {{
                            const message = JSON.parse(event.data);
                            if (message.state) updateFromState(message.state);
                        }} catch (error) {{
                            console.error(error);
                        }}
                    }};
                    ws.onopen = () => setStatus('Live websocket connected.');
                    ws.onclose = () => setStatus('Live websocket closed.');
                    ws.onerror = () => setStatus('Live websocket error.');

                    audioChunks = [];
                    stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                    recorder = new MediaRecorder(stream, {{ mimeType: 'audio/webm' }});
                    recorder.ondataavailable = async (event) => {{
                        if (!event.data || event.data.size === 0 || !sessionId) return;
                        
                        audioChunks.push(event.data);
                        const blob = new Blob(audioChunks, {{ type: 'audio/webm' }});
                        
                        const form = new FormData();
                        form.append('file', blob, `chunk-${{chunkIndex}}.webm`);
                        form.append('sequence', '0');
                        const language = el('fs-language').value.trim();
                        if (language) form.append('language_hint', language);
                        form.append('is_final', 'true');
                        chunkIndex += 1;
                        
                        try {{
                            const upload = await fetch(`${{apiBase}}/stream/audio/${{sessionId}}`, {{ method: 'POST', body: form }});
                            if (!upload.ok) throw new Error('Chunk upload failed');
                            // WebSocket handles the state updates
                        }} catch (error) {{
                            console.error(error);
                            setStatus('Chunk upload failed.');
                        }}
                    }};
                    
                    recorder.start(3000);
                    el('fs-start').disabled = true;
                    el('fs-stop').disabled = false;
                    setStatus('Recording...');
                }}

                async function stopSession() {{
                    if (recorder && recorder.state !== 'inactive') recorder.stop();
                    if (stream) stream.getTracks().forEach((track) => track.stop());
                    if (sessionId) {{
                        try {{
                            const response = await fetch(`${{apiBase}}/stream/finalize/${{sessionId}}`, {{ method: 'POST' }});
                            if (response.ok) {{
                                const data = await response.json();
                                if (data) updateFromState(data);
                            }}
                        }} catch (error) {{
                            console.error(error);
                        }}
                    }}
                    if (ws) ws.close();
                    el('fs-start').disabled = false;
                    el('fs-stop').disabled = true;
                    setStatus('Session stopped.');
                }}

                el('fs-start').addEventListener('click', async () => {{
                    try {{
                        pendingSessionId = null;
                        await startSession();
                    }} catch (error) {{
                        console.error(error);
                        setStatus('Could not start live session. Check microphone permissions and backend URL.');
                    }}
                }});

                el('fs-stop').addEventListener('click', async () => {{
                    await stopSession();
                }});
            }})();
        </script>
        """

    components.html(live_html, height=760, scrolling=True)
