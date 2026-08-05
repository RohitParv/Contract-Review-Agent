"""Structured representation of an extracted contract/lease.

Mirrors the role ``ClientProfile`` played in the original fp-domain-agent
project: a validated Pydantic model that downstream steps (risk matching,
summary generation) can rely on instead of re-parsing raw text.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class KeyDate(BaseModel):
    label: str = Field(description="What this date represents, e.g. 'Lease start'")
    date: str = Field(description="ISO date string if known, else best-effort text")


class FinancialTerms(BaseModel):
    """Structured numeric terms, extracted only when clearly stated in the
    text. Left null rather than guessed — downstream cost simulation treats
    a null as 'can't compute this', never as zero."""

    monthly_rent: float | None = None
    security_deposit: float | None = None
    term_months: int | None = None
    late_fee_flat: float | None = Field(
        default=None, description="One-time flat late fee, if any"
    )
    late_fee_daily: float | None = Field(
        default=None, description="Additional per-day late fee, if any"
    )
    late_fee_daily_cap: int | None = Field(
        default=None, description="Max number of days the daily late fee applies, if stated"
    )
    renewal_increase_pct: float | None = Field(
        default=None, description="Rent increase percentage allowed on renewal, if stated"
    )


class ContractProfile(BaseModel):
    """Structured facts extracted from a contract/lease document."""

    document_type: str = Field(
        default="unknown",
        description="e.g. 'residential lease', 'freelance services agreement'",
    )
    parties: list[str] = Field(default_factory=list)
    effective_date: str | None = None
    term_length: str | None = Field(
        default=None, description="e.g. '12 months', 'month-to-month'"
    )
    payment_terms: str | None = Field(
        default=None, description="Rent/fee amount and schedule, in plain text"
    )
    key_dates: list[KeyDate] = Field(default_factory=list)
    termination_terms: str | None = None
    key_obligations: list[str] = Field(
        default_factory=list, description="Notable obligations for each party"
    )
    notes: str | None = Field(
        default=None, description="Anything else the extractor flagged as notable"
    )
    financial_terms: FinancialTerms = Field(default_factory=FinancialTerms)


class RiskFlag(BaseModel):
    """A single flagged clause, evidence-grounded in the source text."""

    clause_excerpt: str = Field(description="The actual clause text (short excerpt)")
    category: str = Field(description="e.g. 'auto-renewal', 'indemnification'")
    severity: str = Field(description="low | medium | high")
    explanation: str = Field(description="Why this is worth the reader's attention")
    clause_bank_id: str | None = Field(
        default=None, description="Matched entry id from clause_bank.json, if any"
    )
    confidence: float | None = Field(
        default=None, description="0.0-1.0, how clearly the excerpt matches the pattern"
    )
    suggested_language: str | None = Field(
        default=None, description="Concrete counter-clause language the reader could propose"
    )


class RiskReview(BaseModel):
    """Full risk-matching result for a contract."""

    flags: list[RiskFlag] = Field(default_factory=list)
    overall_risk_level: str = Field(default="unknown", description="low | medium | high")
    summary_note: str | None = None


class FinancialSimulation(BaseModel):
    """Deterministic cost projection computed from FinancialTerms — no LLM
    involved, so the numbers are exactly what the arithmetic says."""

    base_total_cost: float | None = Field(
        default=None, description="monthly_rent * term_months, if both are known"
    )
    worst_case_late_fees: float | None = Field(
        default=None, description="Stress-scenario total late fees over the term"
    )
    deposit_at_stake: float | None = None
    notes: list[str] = Field(
        default_factory=list, description="Caveats for any figure that couldn't be computed"
    )
