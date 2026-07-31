from agents.summary import run_summary
from shared.schemas.contract_profile import ContractProfile, RiskReview


def test_run_summary_returns_llm_text(
    scripted_llm_factory, sample_profile_dict, sample_risk_review_dict
):
    llm = scripted_llm_factory(["## Overview\nSome markdown report."])
    profile = ContractProfile.model_validate(sample_profile_dict)
    review = RiskReview.model_validate(sample_risk_review_dict)

    report = run_summary(profile, review, llm=llm)
    assert "Overview" in report

    # Profile and review data should both be in the prompt sent to the LLM.
    system, user = llm.calls[0]
    assert "residential lease" in user
    assert "Auto-renewal" in user
