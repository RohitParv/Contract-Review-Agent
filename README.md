# Contract & Lease Review Assistant

A personal AI agent that reviews contracts and leases: extracts key terms,
flags risky clauses against a known-pattern bank (each with a confidence
score and suggested counter-clause language), runs a deterministic financial
cost simulation, answers questions about a loaded document, and generates a
plain-English summary report — viewable in the web UI or downloadable as a
PDF.

Built as a scaled-down version of the **router → orchestrator → subagents/tools**
architecture from a production financial-planning agent — same pattern, much
smaller footprint. See `PROJECT_NOTES.md`-style reasoning inline in the code
comments if you're curious why things are split the way they are.

**This is not legal advice.** It's a reading aid — always have anything
important reviewed by an actual lawyer before you sign it.

## How It Works

```
User message → Router (classify intent) → Orchestrator
                                              ├─ GREETING → capability list
                                              ├─ QA       → Q&A subagent (grounded in loaded contract, if any)
                                              └─ REVIEW   → extract → risk-flag → summarize pipeline
```

- **`src/router.py`** — cheap keyword-based intent classifier (no LLM call
  needed just to route).
- **`src/orchestrator.py`** — dispatches to the right handler, persists
  conversation turns.
- **`src/agents/`** — reusable, typed LLM logic (extraction, risk matching,
  summary generation). Take text in, return validated Pydantic models out.
- **`src/subagents/`** — thin route handlers that call `agents/` and manage
  conversation state.
- **`src/tools/contract_extract.py`** — reads a `.pdf` or `.txt` contract
  into plain text (PyMuPDF for PDFs).
- **`src/tools/financial_simulation.py`** — deterministic, no-LLM cost
  projection (total cost over term, worst-case late fees, deposit at stake)
  computed from the numeric `financial_terms` the extractor pulls out.
- **`src/tools/report_pdf.py`** — renders the same structured review data as
  a styled PDF via `reportlab`, served from `GET /report/pdf?session_id=...`.
- **`src/clause_bank.json`** — 12 common risky lease/contract clause
  patterns (auto-renewal, mandatory arbitration, one-sided indemnification,
  etc.) that the risk-matching agent checks the document against.
- **`src/shared/llm/`** — swappable LLM client. Default is Gemini (free
  tier); Anthropic, OpenAI, and a no-network `mock` provider are also
  supported behind the same interface.

## Setup

1. **Get a free LLM API key.** The default provider is Google Gemini via AI
   Studio — no credit card required:
   https://aistudio.google.com/apikey

   (Want Claude or GPT instead? See "Switching providers" below.)

2. **Install dependencies:**

   ```bash
   cd contract-review-agent
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure your API key:**

   ```bash
   cp .env.example .env
   # edit .env and paste your key into GOOGLE_API_KEY=
   ```

## Running It

**Option A — CLI (fastest way to try it):**

```bash
python local/run_local.py --contract samples/sample_lease.txt
```

This loads the included synthetic sample lease, runs the full review
pipeline, prints the report, then drops you into an interactive prompt to
ask follow-up questions about it.

Or start with just a question, no document:

```bash
python local/run_local.py --message "What can you help me with?"
```

**Option B — HTTP server + web UI:**

```bash
python main.py
# or: uvicorn main:app --reload
```

Then open **http://127.0.0.1:8000** in a browser for a small chat UI —
upload a `.pdf`/`.txt` contract (or click "Try the sample lease"), then ask
questions or click "Review this contract" for the full risk report: a
financial snapshot, per-clause risk cards (severity, confidence, quoted
excerpt, suggested counter-language), and a "Download PDF Report" button.

Or drive the API directly:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "please review this", "contract_path": "samples/sample_lease.txt"}'
```

Reuse the returned `session_id` on your next request to continue the same
conversation (ask follow-up questions, the contract stays loaded for that
session). To load a contract from a browser upload instead of a server-side
path, `POST /upload` as `multipart/form-data` with a `file` field (and
optional `session_id` to attach it to an existing conversation).

## Testing

47 tests, all offline (mocked/scripted LLM responses — no API key or network
needed to run them):

```bash
pytest
```

## Switching LLM Providers

Edit `LLM_PROVIDER` in `.env`:

| Value | Needs | Install |
|---|---|---|
| `gemini` (default) | `GOOGLE_API_KEY` | `google-generativeai` (already in requirements.txt) |
| `anthropic` | `ANTHROPIC_API_KEY` | `pip install anthropic` |
| `openai` | `OPENAI_API_KEY` | `pip install openai` |
| `mock` | nothing | nothing — canned responses, for testing wiring only |

The rest of the app never changes — everything goes through
`shared/llm/factory.py`.

## Project Layout

```
contract-review-agent/
├── main.py                    # uvicorn entry point
├── src/
│   ├── app.py                 # FastAPI app (POST /chat, /upload, /load-sample, GET /, /health)
│   ├── static/index.html       # self-contained web chat UI served at GET /
│   ├── orchestrator.py        # route dispatcher
│   ├── router.py               # intent classifier
│   ├── clause_bank.json        # known risky clause patterns
│   ├── agents/                 # reusable structured LLM agents
│   │   ├── extractor.py        # contract text -> ContractProfile
│   │   ├── risk_match.py       # contract text + clause bank -> RiskReview
│   │   └── summary.py          # ContractProfile + RiskReview -> Markdown report
│   ├── subagents/               # route handlers (qna, review)
│   ├── tools/
│   │   ├── contract_extract.py     # PDF/text file -> raw text
│   │   ├── financial_simulation.py # ContractProfile -> FinancialSimulation (pure Python)
│   │   └── report_pdf.py           # structured review data -> PDF bytes (reportlab)
│   ├── shared/
│   │   ├── llm/                # client interface, providers, factory
│   │   ├── memory/              # in-memory conversation store
│   │   ├── prompts/loader.py
│   │   └── schemas/             # ContractProfile, RiskFlag, RiskReview, FinancialSimulation
│   └── prompts/                # *.md system prompts
├── samples/sample_lease.txt    # synthetic test lease (packed with flaggable clauses)
├── local/run_local.py          # CLI smoke test / chat loop
└── tests/                      # 47 pytest tests (mocked LLM)
```

## Next Steps (Ideas, Not Done Yet)

- **Persistent memory**: swap `InMemoryConversationStore` for SQLite so
  conversations survive a restart (this would also fix PDF/session data
  being lost on server restart).
- **Jurisdiction-aware flagging**: deliberately deferred — doing this
  honestly needs either curated per-state legal rules or hedged LLM guesses,
  either of which sits uneasily next to the app's explicit "not legal
  advice" stance. Worth its own focused pass rather than a quick add.
- **LangGraph tool-calling pipeline**: if you want the agent to autonomously
  decide when to extract/re-extract/re-flag mid-conversation instead of a
  fixed pipeline, port in LangGraph the way the original project used it for
  its multi-tool ReAct agent.
- **Expand the clause bank**: 12 patterns is a starting set — freelance
  contracts, NDAs, and ToS documents would each want their own bank entries.
