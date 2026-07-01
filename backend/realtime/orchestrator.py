from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from backend.realtime.analysis import (
    build_summary,
    detect_intent,
    estimate_risk,
    estimate_sentiment,
    extract_entities,
)
from backend.realtime.events import ConversationState, TranscriptSegment
from backend.realtime.transcript_buffer import TranscriptBuffer


class RealtimeOrchestrator:
    def __init__(self, state_store, window_size: int = 8):
        self.state_store = state_store
        self.window_size = window_size
        self._buffers: dict[str, TranscriptBuffer] = {}

    def _buffer_for(self, session_id: str):
        if session_id not in self._buffers:
            self._buffers[session_id] = TranscriptBuffer(window_size=self.window_size)
        return self._buffers[session_id]

    async def start_session(self, session_id: str | None = None):
        session_id = session_id or str(uuid4())
        state = ConversationState(session_id=session_id)
        await self.state_store.save_state(state)
        return state

    async def ingest_segment(self, segment: TranscriptSegment):
        buffer = self._buffer_for(segment.session_id)
        buffer.upsert(segment)

        state = await self.state_store.get_state(segment.session_id)
        if state is None:
            state = ConversationState(session_id=segment.session_id)

        state.latest_partial_text = buffer.latest_partial()

        if segment.is_final:
            context_text = buffer.rolling_context()
            state.final_transcript = buffer.final_text()
            state.transcript_segments = buffer.snapshot()
            state.current_intent = detect_intent(context_text, state.current_intent)
            summary = build_summary(context_text, state.current_intent)
            state.current_topic = summary["topic"]

            extracted_entities = extract_entities(context_text)
            entity_map = {
                entity["entity"]: entity for entity in extracted_entities if entity.get("entity")
            }
            state.entities.update(entity_map)

            sentiment = estimate_sentiment(context_text)
            state.sentiment_timeline.append({"time": datetime.utcnow().isoformat(), **sentiment})
            state.risk_score = estimate_risk(extracted_entities, sentiment)["score"]
            state.rolling_summary = summary
            state.intent_history.append(
                {
                    "time": datetime.utcnow().isoformat(),
                    "intent": state.current_intent,
                    "topic": state.current_topic,
                }
            )
            state.confidence_score = segment.confidence or 0.0

        state.updated_at = datetime.utcnow()
        await self.state_store.save_state(state)
        return state

    async def finalize_session(self, session_id: str):
        state = await self.state_store.get_state(session_id)
        if state is None:
            state = ConversationState(session_id=session_id)
        state.final_transcript = self._buffer_for(session_id).final_text() or state.final_transcript
        state.updated_at = datetime.utcnow()
        await self.state_store.save_state(state)
        return state
