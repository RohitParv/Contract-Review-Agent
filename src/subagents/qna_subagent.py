"""Q&A route handler. Thin — delegates the actual LLM call, just assembles
context (conversation history + loaded contract text if any) and persists
the turn.
"""

from __future__ import annotations

from shared.llm.client import LLMClient
from shared.memory.conversation_store import InMemoryConversationStore
from shared.prompts.loader import load_prompt


def run_qna(
    query: str,
    *,
    session_id: str,
    store: InMemoryConversationStore,
    llm: LLMClient,
) -> str:
    system = load_prompt("qa_system")

    contract_text = store.get_contract(session_id)
    history = store.history(session_id)

    context_parts = []
    if contract_text:
        context_parts.append(f"LOADED CONTRACT TEXT:\n{contract_text}")
    if history:
        transcript = "\n".join(f"{t.role}: {t.text}" for t in history[-10:])
        context_parts.append(f"CONVERSATION SO FAR:\n{transcript}")
    context_parts.append(f"USER QUESTION:\n{query}")

    user = "\n\n".join(context_parts)
    answer = llm.complete(system=system, user=user)

    store.append_turn(session_id, "user", query)
    store.append_turn(session_id, "assistant", answer)
    return answer
