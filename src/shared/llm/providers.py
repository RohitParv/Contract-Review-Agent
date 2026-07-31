"""Concrete LLMClient implementations, one per provider.

Each provider's SDK is imported lazily inside its class's ``__init__`` so
that ``pip install``-ing only the provider you actually use is enough —
you don't need anthropic+openai+google-generativeai all installed just to
run with one of them.
"""

from __future__ import annotations

import os


class GeminiClient:
    """Google AI Studio / Gemini API. Free tier, no credit card required.

    Get a key at https://aistudio.google.com/apikey and set GOOGLE_API_KEY.
    """

    def __init__(self, model: str | None = None) -> None:
        import google.generativeai as genai

        api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Get a free key at "
                "https://aistudio.google.com/apikey"
            )
        genai.configure(api_key=api_key)
        self._model_name = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        self._genai = genai

    def complete(self, system: str, user: str) -> str:
        model = self._genai.GenerativeModel(
            self._model_name, system_instruction=system
        )
        response = model.generate_content(user)
        return (response.text or "").strip()


class AnthropicClient:
    """Anthropic Claude API. Requires ANTHROPIC_API_KEY."""

    def __init__(self, model: str | None = None) -> None:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model or os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"
        )

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()


class OpenAIClient:
    """OpenAI API. Requires OPENAI_API_KEY."""

    def __init__(self, model: str | None = None) -> None:
        import openai

        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self._client = openai.OpenAI(api_key=api_key)
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip()


class MockClient:
    """Deterministic canned-response client. No API key, no network.

    Used by the test suite and available as LLM_PROVIDER=mock for trying out
    the pipeline wiring before you've set up a real API key.
    """

    def complete(self, system: str, user: str) -> str:
        return (
            "[mock response]\n"
            f"system_len={len(system)} user_len={len(user)}\n"
            "This is a placeholder reply from the mock LLM provider. "
            "Set LLM_PROVIDER to gemini/anthropic/openai for real answers."
        )
