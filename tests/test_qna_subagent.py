from shared.memory.conversation_store import InMemoryConversationStore
from subagents.qna_subagent import run_qna


def test_run_qna_returns_answer_and_persists_turns(scripted_llm_factory):
    llm = scripted_llm_factory(["Here's the answer."])
    store = InMemoryConversationStore()

    answer = run_qna(
        "What is a security deposit?", session_id="s1", store=store, llm=llm
    )

    assert answer == "Here's the answer."
    history = store.history("s1")
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


def test_run_qna_includes_loaded_contract_in_context(scripted_llm_factory):
    llm = scripted_llm_factory(["Answer grounded in contract."])
    store = InMemoryConversationStore()
    store.set_contract("s2", "This lease has an auto-renewal clause.")

    run_qna("What's the renewal term?", session_id="s2", store=store, llm=llm)

    system, user = llm.calls[0]
    assert "auto-renewal clause" in user
