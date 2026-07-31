"""Reusable risk-matching agent: raw contract text + clause bank -> RiskReview.

Evidence-first by design, matching the original project's strategy-matching
principle: every flag must be grounded in an actual excerpt from the
supplied text, not fabricated from category names alone.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from shared.json_utils import parse_json_response
from shared.llm.client import LLMClient
from shared.prompts.loader import load_prompt
from shared.schemas.contract_profile import RiskReview

_CLAUSE_BANK_PATH = Path(__file__).resolve().parent.parent / "clause_bank.json"


@lru_cache(maxsize=1)
def load_clause_bank() -> list[dict]:
    return json.loads(_CLAUSE_BANK_PATH.read_text(encoding="utf-8"))


def run_risk_review(contract_text: str, *, llm: LLMClient) -> RiskReview:
    system = load_prompt("risk_review_system")
    clause_bank = load_clause_bank()
    user = (
        f"CLAUSE BANK:\n{json.dumps(clause_bank, indent=2)}\n\n"
        f"CONTRACT TEXT:\n{contract_text}"
    )
    raw = llm.complete(system=system, user=user)
    data = parse_json_response(raw)
    return RiskReview.model_validate(data)
