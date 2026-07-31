import json

from orchestrator import Orchestrator
from shared.memory.conversation_store import InMemoryConversationStore


def test_greeting_route_does_not_call_llm(raising_llm):
    orchestrator = Orchestrator(store=InMemoryConversationStore(), llm=raising_llm)
    reply = orchestrator.run("hi", session_id="s1")
    assert "contract or lease" in reply.lower()


def test_qa_route_delegates_to_llm(scripted_llm_factory):
    llm = scripted_llm_factory(["General answer."])
    orchestrator = Orchestrator(store=InMemoryConversationStore(), llm=llm)

    # First turn with a substantive question shouldn't be treated as a greeting.
    reply = orchestrator.run(
        "What does a security deposit clause usually cover?", session_id="s2"
    )
    assert reply == "General answer."


def test_review_route_runs_full_pipeline(
    scripted_llm_factory,
    sample_profile_dict,
    sample_risk_review_dict,
    sample_lease_text,
):
    llm = scripted_llm_factory(
        [
            json.dumps(sample_profile_dict),
            json.dumps(sample_risk_review_dict),
            "Final report.",
        ]
    )
    orchestrator = Orchestrator(store=InMemoryConversationStore(), llm=llm)

    reply = orchestrator.run(
        "please review this",
        session_id="s3",
        contract_path_text=sample_lease_text,
    )
    assert reply == "Final report."


def test_review_route_without_contract_asks_for_one(raising_llm):
    orchestrator = Orchestrator(store=InMemoryConversationStore(), llm=raising_llm)
    reply = orchestrator.run("review this lease", session_id="s4")
    assert "don't have a contract loaded" in reply.lower()
