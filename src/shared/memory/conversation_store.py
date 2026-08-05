"""Conversation memory, abstracted like the original's conversation_store.py.

v1 is in-memory only (fine for a personal/local project). Swap this for a
SQLite-backed implementation later without touching orchestrator code — keep
the same three methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    text: str


@dataclass
class _SessionState:
    turns: list[Turn] = field(default_factory=list)
    contract_text: str | None = None
    contract_profile: dict | None = None
    risk_review: dict | None = None
    financial_sim: dict | None = None
    report_markdown: str | None = None


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._sessions: dict[str, _SessionState] = {}

    def _get_or_create(self, session_id: str) -> _SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = _SessionState()
        return self._sessions[session_id]

    def append_turn(self, session_id: str, role: str, text: str) -> None:
        self._get_or_create(session_id).turns.append(Turn(role=role, text=text))

    def history(self, session_id: str) -> list[Turn]:
        return list(self._get_or_create(session_id).turns)

    def set_contract(self, session_id: str, text: str) -> None:
        self._get_or_create(session_id).contract_text = text

    def get_contract(self, session_id: str) -> str | None:
        return self._get_or_create(session_id).contract_text

    def set_profile(self, session_id: str, profile: dict) -> None:
        self._get_or_create(session_id).contract_profile = profile

    def get_profile(self, session_id: str) -> dict | None:
        return self._get_or_create(session_id).contract_profile

    def set_risk_review(self, session_id: str, review: dict) -> None:
        self._get_or_create(session_id).risk_review = review

    def get_risk_review(self, session_id: str) -> dict | None:
        return self._get_or_create(session_id).risk_review

    def set_financial_sim(self, session_id: str, sim: dict) -> None:
        self._get_or_create(session_id).financial_sim = sim

    def get_financial_sim(self, session_id: str) -> dict | None:
        return self._get_or_create(session_id).financial_sim

    def set_report_markdown(self, session_id: str, report: str) -> None:
        self._get_or_create(session_id).report_markdown = report

    def get_report_markdown(self, session_id: str) -> str | None:
        return self._get_or_create(session_id).report_markdown


_store_singleton: InMemoryConversationStore | None = None


def build_conversation_store() -> InMemoryConversationStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = InMemoryConversationStore()
    return _store_singleton
