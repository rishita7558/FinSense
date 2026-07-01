from backend.realtime.events import TranscriptSegment
from backend.realtime.transcript_buffer import TranscriptBuffer


def test_transcript_buffer_merges_partial_and_final_segments():
    buffer = TranscriptBuffer(window_size=2)

    buffer.upsert(TranscriptSegment(session_id="s1", segment_id="1", sequence=1, text="I think we should", is_final=False))
    buffer.upsert(TranscriptSegment(session_id="s1", segment_id="1", sequence=1, text="I think we should", is_final=True))
    buffer.upsert(TranscriptSegment(session_id="s1", segment_id="2", sequence=2, text="start a SIP", is_final=True))

    assert buffer.latest_partial() == ""
    assert buffer.final_text() == "I think we should start a SIP"
    assert buffer.rolling_context() == "I think we should start a SIP"
    assert len(buffer.snapshot()) == 2
