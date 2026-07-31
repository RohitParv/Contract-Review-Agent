from shared.schemas.contract_profile import ContractProfile, RiskFlag, RiskReview


def test_contract_profile_defaults():
    profile = ContractProfile()
    assert profile.document_type == "unknown"
    assert profile.parties == []
    assert profile.key_dates == []


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
