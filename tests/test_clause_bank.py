from agents.risk_match import load_clause_bank


def test_clause_bank_loads_and_has_expected_shape():
    bank = load_clause_bank()
    assert len(bank) > 0
    for entry in bank:
        assert {"id", "category", "description", "why_it_matters"} <= entry.keys()


def test_clause_bank_has_common_categories():
    ids = {entry["id"] for entry in load_clause_bank()}
    assert "auto-renewal" in ids
    assert "mandatory-arbitration" in ids
    assert "excessive-late-fees" in ids
