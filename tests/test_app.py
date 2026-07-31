"""FastAPI wiring test — uses LLM_PROVIDER=mock (set in conftest.py) so this
never needs a real API key."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_greeting_route():
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert "session_id" in body
    assert "contract or lease" in body["message"].lower()


def test_chat_reuses_session_id():
    first = client.post("/chat", json={"message": "hi"}).json()
    second = client.post(
        "/chat",
        json={
            "message": "what is usually in a lease?",
            "session_id": first["session_id"],
        },
    ).json()
    assert second["session_id"] == first["session_id"]
