from __future__ import annotations

import json

from backend.config import REDIS_URL
from backend.realtime.events import ConversationState

try:
    import redis
except Exception:
    redis = None


class ConversationStateStore:
    def __init__(self):
        self._memory: dict[str, ConversationState] = {}
        self._redis = None
        if REDIS_URL and redis is not None:
            self._redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def get_state(self, session_id: str):
        if self._redis:
            raw = self._redis.get(self._key(session_id))
            if raw:
                return self._deserialize(raw)
        return self._memory.get(session_id)

    async def save_state(self, state: ConversationState):
        if self._redis:
            self._redis.set(self._key(state.session_id), self._serialize(state), ex=60 * 60 * 24)
        self._memory[state.session_id] = state

    async def delete_state(self, session_id: str):
        self._memory.pop(session_id, None)
        if self._redis:
            self._redis.delete(self._key(session_id))

    def _key(self, session_id: str):
        return f"finsen:{session_id}"

    def _serialize(self, state: ConversationState):
        return json.dumps(state.to_dict())

    def _deserialize(self, payload: str):
        data = json.loads(payload)
        state = ConversationState(session_id=data["session_id"])
        state.rolling_summary = data.get("rolling_summary", {})
        state.entities = data.get("entities", {})
        state.intent_history = data.get("intent_history", [])
        state.sentiment_timeline = data.get("sentiment_timeline", [])
        state.current_intent = data.get("current_intent", "Financial Conversation")
        state.current_topic = data.get("current_topic", "General Financial Planning")
        state.risk_score = data.get("risk_score", 0)
        state.speaking_time_ms = data.get("speaking_time_ms", 0)
        state.confidence_score = data.get("confidence_score", 0.0)
        state.latest_partial_text = data.get("latest_partial_text", "")
        state.final_transcript = data.get("final_transcript", "")
        return state
