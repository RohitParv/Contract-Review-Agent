"""Reusable structured extraction agent: raw contract text -> ContractProfile.

Same layering idea as the original repo's agents/ directory: typed input in,
validated Pydantic result out, LLM call through the synchronous LLMClient
seam. Callable from a subagent today, and from a future tool-calling
pipeline later without duplicating logic.
"""

from __future__ import annotations

from shared.json_utils import parse_json_response
from shared.llm.client import LLMClient
from shared.prompts.loader import load_prompt
from shared.schemas.contract_profile import ContractProfile


def run_extraction(contract_text: str, *, llm: LLMClient) -> ContractProfile:
    system = load_prompt("extractor_system")
    raw = llm.complete(system=system, user=contract_text)
    data = parse_json_response(raw)
    return ContractProfile.model_validate(data)
