from shared.schemas.contract_profile import (
    ContractProfile,
    FinancialSimulation,
    RiskFlag,
    RiskReview,
)


def test_contract_profile_defaults():
    profile = ContractProfile()
    assert profile.document_type == "unknown"
    assert profile.parties == []
    assert profile.key_dates == []
    assert profile.financial_terms.monthly_rent is None


def test_risk_flag_new_fields_default_to_none():
    flag = RiskFlag(clause_excerpt="x", category="y", severity="low", explanation="z")
    assert flag.confidence is None
    assert flag.suggested_language is None


def test_financial_simulation_defaults():
    sim = FinancialSimulation()
    assert sim.base_total_cost is None
    assert sim.notes == []


def test_contract_profile_from_dict(sample_profile_dict):
    profile = ContractProfile.model_validate(sample_profile_dict)
    assert profile.document_type == "residential lease"
    assert "Jordan A. Sample" in profile.parties
    assert profile.key_dates[0].label == "Lease start"


def test_risk_review_from_dict(sample_risk_review_dict):
    review = RiskReview.model_validate(sample_risk_review_dict)
    assert review.overall_risk_level == "medium"
    assert len(review.flags) == 1
    assert isinstance(review.flags[0], RiskFlag)
    assert review.flags[0].clause_bank_id == "auto-renewal"
