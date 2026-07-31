import json

from agents.risk_match import run_risk_review


def test_run_risk_review_parses_valid_json(
    scripted_llm_factory, sample_risk_review_dict, sample_lease_text
):
    llm = scripted_llm_factory([json.dumps(sample_risk_review_dict)])
    review = run_risk_review(sample_lease_text, llm=llm)
    assert review.overall_risk_level == "medium"
    assert review.flags[0].category == "Auto-renewal"

    # The clause bank should have been included in the prompt sent to the LLM.
    system, user = llm.calls[0]
    assert "auto-renewal" in user
    assert "CONTRACT TEXT" in user
