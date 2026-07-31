import json

import pytest

from agents.extractor import run_extraction


def test_run_extraction_parses_valid_json(scripted_llm_factory, sample_profile_dict):
    llm = scripted_llm_factory([json.dumps(sample_profile_dict)])
    profile = run_extraction("some contract text", llm=llm)
    assert profile.document_type == "residential lease"
    assert len(llm.calls) == 1


def test_run_extraction_strips_markdown_fences(scripted_llm_factory, sample_profile_dict):
    fenced = "```json\n" + json.dumps(sample_profile_dict) + "\n```"
    llm = scripted_llm_factory([fenced])
    profile = run_extraction("some contract text", llm=llm)
    assert profile.document_type == "residential lease"


def test_run_extraction_invalid_json_raises(scripted_llm_factory):
    llm = scripted_llm_factory(["not json at all"])
    with pytest.raises(ValueError):
        run_extraction("some contract text", llm=llm)
