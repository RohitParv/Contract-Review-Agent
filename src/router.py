"""Intent router. Cheap keyword/pattern classification, no LLM call needed
just to route — same principle as the original repo's router.py.
"""

from __future__ import annotations

import re

from subagents.base import RouteDecision

_GREETING_PATTERNS = (
    "what can you do",
    "what can you help",
    "how can you help",
    "what do you do",
    "get started",
    "where do i start",
)
_GREETING_WORDS = {"hi", "hello", "hey", "help", "start", "menu", "options"}

_REVIEW_SIGNALS = (
    "review this",
    "review my",
    "review the",
    "look over this",
    "check this contract",
    "check this lease",
    "flag any risks",
    "flag risky",
    "any red flags",
    "risky clauses",
)

_REVIEW_INTENT = re.compile(r"\b(review|analyz\w*|check)\b", re.IGNORECASE)
_DOCUMENT_NOUN = re.compile(r"\b(contract|lease|agreement)\b", re.IGNORECASE)


def _is_vague_greeting(query: str) -> bool:
    q = query.lower().strip()
    if not q:
        return True
    if any(pattern in q for pattern in _GREETING_PATTERNS):
        return True
    tokens = re.findall(r"[a-z']+", q)
    return len(tokens) <= 3 and any(t in _GREETING_WORDS for t in tokens)


def _wants_review(query: str, has_contract: bool) -> bool:
    q = query.lower()
    if any(signal in q for signal in _REVIEW_SIGNALS):
        return True
    return bool(has_contract and _REVIEW_INTENT.search(q) and _DOCUMENT_NOUN.search(q))


class IntentRouter:
    """Routes inbound requests; tracks which conversations have been seen."""

    def __init__(self) -> None:
        self._seen_conversations: set[str] = set()

    def classify(
        self,
        query: str,
        *,
        session_id: str = "",
        has_contract_upload: bool = False,
    ) -> RouteDecision:
        query = (query or "").strip()
        first_turn = self._mark_first_turn(session_id)

        if first_turn and _is_vague_greeting(query):
            return RouteDecision.GREETING

        if has_contract_upload:
            return RouteDecision.REVIEW

        if _wants_review(query, has_contract=False):
            return RouteDecision.REVIEW

        return RouteDecision.QA

    def _mark_first_turn(self, session_id: str) -> bool:
        key = session_id or ""
        first = key not in self._seen_conversations
        self._seen_conversations.add(key)
        return first
