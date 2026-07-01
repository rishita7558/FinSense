from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_endpoint_reports_ready():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_stream_start_returns_session_metadata():
    response = client.post("/stream/start")
    assert response.status_code == 200

    payload = response.json()
    assert payload["session_id"]
    assert payload["websocket_url"].startswith("/ws/live/")


def test_stream_segment_updates_live_state():
    start_response = client.post("/stream/start")
    session_id = start_response.json()["session_id"]

    response = client.post(
        f"/stream/segment/{session_id}",
        json={
            "sequence": 1,
            "text": "I want to invest in a mutual fund SIP.",
            "is_final": True,
            "confidence": 0.98,
        },
    )

    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["current_intent"] in {"Investment Discussion", "Mutual Fund Discussion"}
    assert payload["current_topic"] in {"Investments", "Mutual Funds"}
