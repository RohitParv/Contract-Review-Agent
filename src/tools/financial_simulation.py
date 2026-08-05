"""Deterministic cost projection from a contract's extracted financial
terms — plain arithmetic, no LLM call. The extractor agent already pulled
the raw numbers out of the text; this just does the math on them.
"""

from __future__ import annotations

from shared.schemas.contract_profile import ContractProfile, FinancialSimulation

_DEFAULT_LATE_DAYS = 15
_DEFAULT_TERM_MONTHS = 12


def simulate_costs(profile: ContractProfile) -> FinancialSimulation:
    ft = profile.financial_terms
    notes: list[str] = []

    base_total_cost = None
    if ft.monthly_rent is not None and ft.term_months is not None:
        base_total_cost = round(ft.monthly_rent * ft.term_months, 2)
    else:
        notes.append(
            "Total cost over the term not computed — monthly rent or term "
            "length wasn't clearly stated in the document."
        )

    worst_case_late_fees = None
    if ft.late_fee_flat is not None or ft.late_fee_daily is not None:
        days_late = ft.late_fee_daily_cap if ft.late_fee_daily_cap is not None else _DEFAULT_LATE_DAYS
        months = ft.term_months or _DEFAULT_TERM_MONTHS
        monthly_worst = (ft.late_fee_flat or 0.0) + (ft.late_fee_daily or 0.0) * days_late
        worst_case_late_fees = round(monthly_worst * months, 2)
        cap_note = (
            f"capped at {days_late} late days/month as stated"
            if ft.late_fee_daily_cap is not None
            else f"assuming up to {days_late} late days/month (no cap was stated)"
        )
        notes.append(
            f"Worst-case late fees assume paying late every month for {months} "
            f"months, {cap_note} — a stress scenario, not a prediction."
        )
    else:
        notes.append("No late fee terms found in this document.")

    deposit_at_stake = ft.security_deposit
    if deposit_at_stake is None:
        notes.append("Security deposit amount not clearly stated.")

    return FinancialSimulation(
        base_total_cost=base_total_cost,
        worst_case_late_fees=worst_case_late_fees,
        deposit_at_stake=deposit_at_stake,
        notes=notes,
    )
