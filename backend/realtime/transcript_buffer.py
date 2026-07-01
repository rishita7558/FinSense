from __future__ import annotations

from dataclasses import replace

from backend.realtime.events import TranscriptSegment


class TranscriptBuffer:
    def __init__(self, window_size: int = 8):
        self.window_size = window_size
        self._segments: dict[str, TranscriptSegment] = {}
        self._ordered_ids: list[str] = []

    def upsert(self, segment: TranscriptSegment):
        if segment.segment_id not in self._segments:
            self._ordered_ids.append(segment.segment_id)
        self._segments[segment.segment_id] = segment

    def final_segments(self):
        final_items = [self._segments[segment_id] for segment_id in self._ordered_ids if self._segments[segment_id].is_final]
        return sorted(final_items, key=lambda item: item.sequence)

    def final_text(self):
        return " ".join(segment.text.strip() for segment in self.final_segments() if segment.text.strip()).strip()

    def rolling_context(self):
        final_items = self.final_segments()[-self.window_size :]
        return " ".join(segment.text.strip() for segment in final_items if segment.text.strip()).strip()

    def latest_partial(self):
        for segment_id in reversed(self._ordered_ids):
            segment = self._segments[segment_id]
            if not segment.is_final:
                return segment.text
        return ""

    def snapshot(self):
        return [replace(self._segments[segment_id]) for segment_id in self._ordered_ids]
