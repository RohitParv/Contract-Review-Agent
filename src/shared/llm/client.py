"""Minimal synchronous LLM client interface.

Deliberately not LangChain-based. The original fp-domain-agent project used
two separate LLM seams: a synchronous ``LLMClient`` for structured
agents (extraction, strategy/risk matching) and a LangChain chat-model seam
for its LangGraph ReAct tool-calling pipeline. This project only needs the
first seam for v1 — there's no multi-tool ReAct loop yet, so pulling in
LangChain/LangGraph would be dead weight. Add a LangChain adapter later if
you outgrow this and want a tool-calling pipeline (see README "Next steps").
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Anything that can turn (system prompt, user text) into a text reply."""

    def complete(self, system: str, user: str) -> str:
        ...
