from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TranscriptSegment:
    session_id: str
    segment_id: str
    sequence: int
    text: str
    is_final: bool = False
    confidence: float = 0.0
    speaker: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        return payload


@dataclass
class ConversationState:
    session_id: str
    transcript_segments: list[TranscriptSegment] = field(default_factory=list)
    rolling_summary: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    intent_history: list[dict[str, Any]] = field(default_factory=list)
    sentiment_timeline: list[dict[str, Any]] = field(default_factory=list)
    current_intent: str = "Financial Conversation"
    current_topic: str = "General Financial Planning"
    risk_score: int = 0
    speaking_time_ms: int = 0
    confidence_score: float = 0.0
    latest_partial_text: str = ""
    final_transcript: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "transcript_segments": [segment.to_dict() for segment in self.transcript_segments],
            "rolling_summary": self.rolling_summary,
            "entities": self.entities,
            "intent_history": self.intent_history,
            "sentiment_timeline": self.sentiment_timeline,
            "current_intent": self.current_intent,
            "current_topic": self.current_topic,
            "risk_score": self.risk_score,
            "speaking_time_ms": self.speaking_time_ms,
            "confidence_score": self.confidence_score,
            "latest_partial_text": self.latest_partial_text,
            "final_transcript": self.final_transcript,
            "updated_at": self.updated_at.isoformat(),
        }
