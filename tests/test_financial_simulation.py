from shared.schemas.contract_profile import ContractProfile, FinancialTerms
from tools.financial_simulation import simulate_costs


def test_simulate_costs_full_data():
    profile = ContractProfile(
        financial_terms=FinancialTerms(
            monthly_rent=1800,
            term_months=12,
            security_deposit=1800,
            late_fee_flat=150,
            late_fee_daily=25,
            late_fee_daily_cap=10,
        )
    )
    sim = simulate_costs(profile)
    assert sim.base_total_cost == 21600.0
    assert sim.worst_case_late_fees == 4800.0  # (150 + 25*10) * 12
    assert sim.deposit_at_stake == 1800.0
    # Late-fee assumption is always explained, even when the figures are fully known.
    assert len(sim.notes) == 1
    assert "stress scenario" in sim.notes[0]


def test_simulate_costs_missing_data_adds_caveat_notes():
    profile = ContractProfile()
    sim = simulate_costs(profile)
    assert sim.base_total_cost is None
    assert sim.worst_case_late_fees is None
    assert sim.deposit_at_stake is None
    assert len(sim.notes) == 3


def test_simulate_costs_late_fee_without_cap_uses_default_days():
    profile = ContractProfile(financial_terms=FinancialTerms(late_fee_daily=10, term_months=6))
    sim = simulate_costs(profile)
    assert sim.worst_case_late_fees == 10 * 15 * 6
    assert sim.base_total_cost is None
