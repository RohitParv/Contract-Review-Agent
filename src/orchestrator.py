"""Central dispatcher: classify intent, run the matching route, return text.

Equivalent to the original repo's orchestrator.py, trimmed to this project's
three routes. Structured events are printed (not persisted to a real event
store) — swap `_log_event` for a real sink later if useful.
"""

from __future__ import annotations

import json
import sys
import time

from router import IntentRouter
from shared.llm.client import LLMClient
from shared.llm.factory import llm_client_factory
from shared.memory.conversation_store import InMemoryConversationStore, build_conversation_store
from subagents.base import RouteDecision
from subagents.qna_subagent import run_qna
from subagents.review_subagent import run_review

CAPABILITY_TEXT = (
    "I can help you with a contract or lease. I can:\n"
    "- Review an uploaded contract/lease and flag risky clauses "
    "(provide a file path to a .pdf or .txt file)\n"
    "- Answer general questions about contract/lease terms\n"
    "- Answer questions about a contract you've already loaded in this "
    "conversation\n\n"
    "To get started, either ask a question or tell me the path to a "
    "contract file you'd like reviewed."
)


def _log_event(event: str, **fields: object) -> None:
    payload = {"event": event, "ts": time.time(), **fields}
    print(json.dumps(payload), file=sys.stderr)


class Orchestrator:
    def __init__(
        self,
        *,
        store: InMemoryConversationStore | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self._router = IntentRouter()
        self._store = store or build_conversation_store()
        self._llm = llm or llm_client_factory()

    def load_contract(self, session_id: str, text: str) -> None:
        """Store contract text on a session ahead of the next chat turn (used
        by the /upload route, where the file comes from the browser instead
        of a server-side path)."""
        self._store.set_contract(session_id, text)

    def get_review_snapshot(self, session_id: str) -> dict | None:
        """Structured profile/risk/financial data for a session, if a review
        has run — lets the API layer enrich its response without changing
        what .run() returns."""
        profile = self._store.get_profile(session_id)
        if profile is None:
            return None
        return {
            "profile": profile,
            "risk_review": self._store.get_risk_review(session_id),
            "financial_sim": self._store.get_financial_sim(session_id),
            "narrative_md": self._store.get_report_markdown(session_id),
        }

    def run(
        self,
        query: str,
        *,
        session_id: str,
        contract_path_text: str | None = None,
    ) -> str:
        """Run one turn. ``contract_path_text`` is the already-loaded raw
        text of a contract, if the caller supplied a file this turn."""
        route = self._router.classify(
            query,
            session_id=session_id,
            has_contract_upload=contract_path_text is not None,
        )
        _log_event("route_decided", route=route.value, session_id=session_id)

        if route == RouteDecision.GREETING:
            return CAPABILITY_TEXT

        if route == RouteDecision.REVIEW:
            text = contract_path_text or self._store.get_contract(session_id)
            if not text:
                return (
                    "I don't have a contract loaded yet for this conversation. "
                    "Tell me the file path to a .pdf or .txt contract to review."
                )
            report = run_review(
                text, session_id=session_id, store=self._store, llm=self._llm
            )
            _log_event("review_generated", session_id=session_id)
            return report

        answer = run_qna(
            query, session_id=session_id, store=self._store, llm=self._llm
        )
        _log_event("qa_answered", session_id=session_id)
        return answer
