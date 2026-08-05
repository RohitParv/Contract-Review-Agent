"""Review route handler: the extract -> risk-flag -> summarize pipeline.

Equivalent to the original repo's DATA_EXTRACTION route, which chained
several subagents directly in the orchestrator rather than through a
LangGraph tool loop. Same idea here: each step is a plain function call,
each step's structured result is cached on the session so re-asking
questions later can reuse it instead of re-running the whole pipeline.
"""

from __future__ import annotations

from agents.extractor import run_extraction
from agents.risk_match import run_risk_review
from agents.summary import run_summary
from shared.llm.client import LLMClient
from shared.memory.conversation_store import InMemoryConversationStore
from tools.financial_simulation import simulate_costs


def run_review(
    contract_text: str,
    *,
    session_id: str,
    store: InMemoryConversationStore,
    llm: LLMClient,
) -> str:
    store.set_contract(session_id, contract_text)

    profile = run_extraction(contract_text, llm=llm)
    store.set_profile(session_id, profile.model_dump())

    risk_review = run_risk_review(contract_text, llm=llm)
    store.set_risk_review(session_id, risk_review.model_dump())

    financial_sim = simulate_costs(profile)
    store.set_financial_sim(session_id, financial_sim.model_dump())

    report = run_summary(profile, risk_review, llm=llm)
    store.set_report_markdown(session_id, report)

    store.append_turn(session_id, "user", "[uploaded a contract for review]")
    store.append_turn(session_id, "assistant", report)
    return report
