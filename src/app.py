"""FastAPI entry point. Flat REST contract, similar in spirit to the
original repo's API Gateway wrapper (POST /fp-agent/messages) but simpler —
no A2A protocol, just {message, session_id} in and out.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

load_dotenv()

from orchestrator import Orchestrator  # noqa: E402  (after load_dotenv)
from shared.schemas.contract_profile import (  # noqa: E402
    ContractProfile,
    FinancialSimulation,
    RiskReview,
)
from tools.contract_extract import (  # noqa: E402
    extract_text_from_bytes,
    load_contract_text,
)
from tools.report_pdf import generate_report_pdf  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"
SAMPLE_LEASE_PATH = Path(__file__).resolve().parent.parent / "samples" / "sample_lease.txt"

app = FastAPI(title="Contract & Lease Review Assistant")
_orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    contract_path: str | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    review: dict | None = None


class LoadContractResponse(BaseModel):
    session_id: str
    filename: str
    message: str


class LoadSampleRequest(BaseModel):
    session_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


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
    review = _orchestrator.get_review_snapshot(session_id)
    return ChatResponse(message=reply, session_id=session_id, review=review)


@app.post("/upload", response_model=LoadContractResponse)
async def upload(
    file: UploadFile = File(...),
    session_id: str | None = Form(None),
) -> LoadContractResponse:
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only .pdf or .txt files are supported.")

    data = await file.read()
    text = extract_text_from_bytes(file.filename, data)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Couldn't extract any text from that file.")

    session_id = session_id or str(uuid.uuid4())
    _orchestrator.load_contract(session_id, text)
    return LoadContractResponse(
        session_id=session_id,
        filename=file.filename,
        message=f"Loaded {file.filename} ({len(text):,} characters). Ask a question or say "
        '"review this contract" for a full risk report.',
    )


@app.post("/load-sample", response_model=LoadContractResponse)
def load_sample(req: LoadSampleRequest) -> LoadContractResponse:
    text = load_contract_text(str(SAMPLE_LEASE_PATH))
    session_id = req.session_id or str(uuid.uuid4())
    _orchestrator.load_contract(session_id, text)
    return LoadContractResponse(
        session_id=session_id,
        filename="sample_lease.txt",
        message='Loaded the sample lease. Ask a question or say "review this contract" '
        "for a full risk report.",
    )


@app.get("/report/pdf")
def report_pdf(session_id: str) -> Response:
    snapshot = _orchestrator.get_review_snapshot(session_id)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="No review found for this session yet — run a review first.",
        )

    profile = ContractProfile.model_validate(snapshot["profile"])
    risk_review = RiskReview.model_validate(snapshot["risk_review"] or {})
    financial_sim = FinancialSimulation.model_validate(snapshot["financial_sim"] or {})
    narrative_md = snapshot["narrative_md"] or ""

    pdf_bytes = generate_report_pdf(profile, risk_review, financial_sim, narrative_md)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=risk_report.pdf"},
    )
