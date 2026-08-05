"""FastAPI wiring test — uses LLM_PROVIDER=mock (set in conftest.py) so this
never needs a real API key."""

import json

from fastapi.testclient import TestClient

import app as app_module
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


def test_index_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Contract" in response.text


def test_upload_txt_file():
    response = client.post(
        "/upload",
        files={"file": ("lease.txt", b"This is a test lease document.", "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "lease.txt"
    assert "session_id" in body


def test_upload_rejects_unsupported_extension():
    response = client.post(
        "/upload",
        files={"file": ("lease.docx", b"irrelevant", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_text():
    response = client.post(
        "/upload",
        files={"file": ("empty.txt", b"   \n  ", "text/plain")},
    )
    assert response.status_code == 400


def test_load_sample_then_ask_question():
    loaded = client.post("/load-sample", json={}).json()
    assert loaded["filename"] == "sample_lease.txt"

    reply = client.post(
        "/chat",
        json={"message": "what is the term length?", "session_id": loaded["session_id"]},
    )
    assert reply.status_code == 200


def test_upload_then_qa_reuses_session():
    uploaded = client.post(
        "/upload",
        files={"file": ("lease.txt", b"Sample lease text for review.", "text/plain")},
    ).json()
    reply = client.post(
        "/chat",
        json={
            "message": "what does this say about the security deposit?",
            "session_id": uploaded["session_id"],
        },
    )
    assert reply.status_code == 200
    assert reply.json()["session_id"] == uploaded["session_id"]


def test_chat_review_field_is_null_before_any_review():
    response = client.post("/chat", json={"message": "hi"})
    assert response.json()["review"] is None


def test_report_pdf_404_without_review():
    response = client.get("/report/pdf", params={"session_id": "no-such-session"})
    assert response.status_code == 404


def test_report_pdf_after_review(monkeypatch, scripted_llm_factory, sample_profile_dict, sample_risk_review_dict):
    llm = scripted_llm_factory(
        [
            json.dumps(sample_profile_dict),
            json.dumps(sample_risk_review_dict),
            "## Overview\nTest overview.\n\n## Questions Worth Asking Before You Sign\n1. Test?\n",
        ]
    )
    monkeypatch.setattr(app_module._orchestrator, "_llm", llm)

    uploaded = client.post(
        "/upload",
        files={"file": ("lease.txt", b"Sample lease text for review.", "text/plain")},
    ).json()
    reply = client.post(
        "/chat",
        json={"message": "please review this contract", "session_id": uploaded["session_id"]},
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["review"] is not None
    assert body["review"]["financial_sim"] is not None

    pdf_response = client.get("/report/pdf", params={"session_id": uploaded["session_id"]})
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content[:4] == b"%PDF"
