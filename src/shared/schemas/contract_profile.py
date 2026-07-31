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


class RiskFlag(BaseModel):
    """A single flagged clause, evidence-grounded in the source text."""

    clause_excerpt: str = Field(description="The actual clause text (short excerpt)")
    category: str = Field(description="e.g. 'auto-renewal', 'indemnification'")
    severity: str = Field(description="low | medium | high")
    explanation: str = Field(description="Why this is worth the reader's attention")
    clause_bank_id: str | None = Field(
        default=None, description="Matched entry id from clause_bank.json, if any"
    )


class RiskReview(BaseModel):
    """Full risk-matching result for a contract."""

    flags: list[RiskFlag] = Field(default_factory=list)
    overall_risk_level: str = Field(default="unknown", description="low | medium | high")
    summary_note: str | None = None
