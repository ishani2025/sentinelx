"""Robust extraction of a single JSON object from raw LLM text output.

Local models occasionally wrap JSON in markdown fences or prose despite being
asked for JSON-only output. This module isolates that defensive parsing so
node code can just ask for a dict back.
"""
from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class JSONExtractionError(ValueError):
    """Raised when no valid JSON object could be extracted from LLM output."""


def extract_json_object(raw_text: str) -> dict:
    """Extracts and parses the first JSON object found in `raw_text`.

    Tries, in order: the whole string, the contents of a markdown code
    fence, and the first `{...}` balanced-brace span in the text.
    """
    candidates: list[str] = [raw_text.strip()]

    fence_match = _FENCE_RE.search(raw_text)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    brace_span = _first_balanced_braces(raw_text)
    if brace_span:
        candidates.append(brace_span)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue

    raise JSONExtractionError(f"Could not extract a JSON object from LLM output: {raw_text[:500]!r}")


def _first_balanced_braces(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None
