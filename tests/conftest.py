"""Shared test fixtures.

No test in this suite makes a real network/LLM call — everything runs
against ScriptedLLMClient or MockClient, mirroring the original repo's
convention of mocking AI Hub/AWS in unit tests and keeping live-call smoke
scripts separate under local/.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Force the mock provider for the whole test session so importing app.py (which
# builds an Orchestrator, and therefore an LLM client, at module load time)
# never needs a real API key or network access.
os.environ.setdefault("LLM_PROVIDER", "mock")

import pytest  # noqa: E402


class ScriptedLLMClient:
    """Returns pre-set responses in order, one per .complete() call.

    Raises if called more times than scripted, or if no responses were
    provided at all — makes it obvious in a failing test whether a route
    short-circuited (e.g. GREETING shouldn't call the LLM) or called the LLM
    more times than expected.
    """

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self._responses:
            raise AssertionError("ScriptedLLMClient called with no responses left")
        return self._responses.pop(0)


class RaisingLLMClient:
    """Fails the test loudly if the LLM is called at all."""

    def complete(self, system: str, user: str) -> str:
        raise AssertionError("LLM should not have been called for this route")


@pytest.fixture
def sample_profile_dict() -> dict:
    return {
        "document_type": "residential lease",
        "parties": ["Example Properties LLC", "Jordan A. Sample"],
        "effective_date": "2026-01-01",
        "term_length": "12 months",
        "payment_terms": "$1,800.00 per month, due on the 1st",
        "key_dates": [{"label": "Lease start", "date": "2026-01-01"}],
        "termination_terms": "Full remaining rent owed if terminated early",
        "key_obligations": ["Tenant responsible for all repairs and maintenance"],
        "notes": None,
    }


@pytest.fixture
def sample_risk_review_dict() -> dict:
    return {
        "flags": [
            {
                "clause_excerpt": "automatically renew for successive twelve (12) month terms",
                "category": "Auto-renewal",
                "severity": "medium",
                "explanation": "Locks the tenant in unless they give 90 days notice.",
                "clause_bank_id": "auto-renewal",
            }
        ],
        "overall_risk_level": "medium",
        "summary_note": "Several tenant-unfavorable clauses present.",
    }


@pytest.fixture
def scripted_llm_factory():
    def _make(responses: list[str]) -> ScriptedLLMClient:
        return ScriptedLLMClient(responses)

    return _make


@pytest.fixture
def raising_llm() -> RaisingLLMClient:
    return RaisingLLMClient()


@pytest.fixture
def sample_lease_text() -> str:
    path = Path(__file__).resolve().parent.parent / "samples" / "sample_lease.txt"
    return path.read_text(encoding="utf-8")


def as_json(data: dict) -> str:
    return json.dumps(data)
