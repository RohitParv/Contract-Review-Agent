"""Central place that decides which LLMClient implementation to build.

Mirrors the role of the original repo's ``shared/llm/factory.py`` — one
seam that the rest of the codebase depends on, so swapping providers never
means touching business logic.
"""

from __future__ import annotations

import os

from shared.llm.client import LLMClient
from shared.llm.providers import (
    AnthropicClient,
    GeminiClient,
    MockClient,
    OpenAIClient,
)

_PROVIDERS = {
    "gemini": GeminiClient,
    "anthropic": AnthropicClient,
    "openai": OpenAIClient,
    "mock": MockClient,
}

_client_singleton: LLMClient | None = None


def llm_client_factory(provider: str | None = None) -> LLMClient:
    """Build (and cache) the configured LLMClient.

    Provider is read from LLM_PROVIDER if not passed explicitly. Defaults to
    "gemini" since Google AI Studio's free tier needs no billing setup.
    """
    global _client_singleton
    if _client_singleton is not None and provider is None:
        return _client_singleton

    name = (provider or os.environ.get("LLM_PROVIDER", "gemini")).strip().lower()
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{name}'. Choose one of: {sorted(_PROVIDERS)}"
        )
    client = _PROVIDERS[name]()
    if provider is None:
        _client_singleton = client
    return client


def reset_client_cache() -> None:
    """Test helper: clear the cached singleton between tests."""
    global _client_singleton
    _client_singleton = None
