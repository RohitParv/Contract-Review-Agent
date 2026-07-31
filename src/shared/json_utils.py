"""Small helper for parsing JSON out of an LLM text response.

Models occasionally wrap JSON in markdown code fences even when told not to;
this strips that before parsing so callers don't all need the same guard.
"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_response(text: str) -> dict:
    cleaned = _FENCE_RE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model response was not valid JSON after cleanup: {cleaned[:200]!r}"
        ) from exc
