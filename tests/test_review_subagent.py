import json

from shared.memory.conversation_store import InMemoryConversationStore
from subagents.review_subagent import run_review


def test_run_review_pipeline_end_to_end(
    scripted_llm_factory,
    sample_profile_dict,
    sample_risk_review_dict,
    sample_lease_text,
):
    llm = scripted_llm_factory(
        [
            json.dumps(sample_profile_dict),  # extraction step
            json.dumps(sample_risk_review_dict),  # risk review step
            "## Overview\nFinal report text.",  # summary step
        ]
    )
    store = InMemoryConversationStore()

    report = run_review(
        sample_lease_text, session_id="s1", store=store, llm=llm
    )

    assert report == "## Overview\nFinal report text."
    assert len(llm.calls) == 3  # extraction, risk review, summary — in that order
    assert store.get_contract("s1") == sample_lease_text
    assert store.get_profile("s1")["document_type"] == "residential lease"
    assert store.get_risk_review("s1")["overall_risk_level"] == "medium"

    history = store.history("s1")
    assert history[-1].role == "assistant"
    assert history[-1].text == "## Overview\nFinal report text."
