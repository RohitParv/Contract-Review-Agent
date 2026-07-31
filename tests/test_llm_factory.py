import pytest

from shared.llm.factory import llm_client_factory, reset_client_cache
from shared.llm.providers import MockClient


def test_mock_provider_returns_mock_client():
    reset_client_cache()
    client = llm_client_factory("mock")
    assert isinstance(client, MockClient)
    reply = client.complete("system", "user")
    assert "mock response" in reply


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        llm_client_factory("not-a-real-provider")
