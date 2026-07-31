"""FastAPI entry point. Flat REST contract, similar in spirit to the
original repo's API Gateway wrapper (POST /fp-agent/messages) but simpler —
no A2A protocol, just {message, session_id} in and out.
"""

from __future__ import annotations

import uuid

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

from orchestrator import Orchestrator  # noqa: E402  (after load_dotenv)
from tools.contract_extract import load_contract_text  # noqa: E402

app = FastAPI(title="Contract & Lease Review Assistant")
_orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    contract_path: str | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())

    contract_text = None
    if req.contract_path:
        contract_text = load_contract_text(req.contract_path)

    reply = _orchestrator.run(
        req.message,
        session_id=session_id,
        contract_path_text=contract_text,
    )
    return ChatResponse(message=reply, session_id=session_id)
