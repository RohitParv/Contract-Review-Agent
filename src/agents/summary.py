"""Reusable summary agent: ContractProfile + RiskReview -> Markdown report."""

from __future__ import annotations

import json

from shared.llm.client import LLMClient
from shared.prompts.loader import load_prompt
from shared.schemas.contract_profile import ContractProfile, RiskReview


def run_summary(
    profile: ContractProfile, risk_review: RiskReview, *, llm: LLMClient
) -> str:
    system = load_prompt("summary_system")
    user = (
        f"CONTRACT PROFILE:\n{json.dumps(profile.model_dump(), indent=2)}\n\n"
        f"RISK REVIEW:\n{json.dumps(risk_review.model_dump(), indent=2)}"
    )
    return llm.complete(system=system, user=user)
