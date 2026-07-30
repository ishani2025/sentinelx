"""Unit tests for robust JSON extraction from raw LLM text output."""
from __future__ import annotations

import pytest

from utils.json_utils import JSONExtractionError, extract_json_object


def test_extracts_plain_json():
    assert extract_json_object('{"a": 1, "b": "two"}') == {"a": 1, "b": "two"}


def test_extracts_json_from_markdown_fence():
    raw = "Here is the result:\n```json\n{\"a\": 1}\n```\nLet me know if you need anything else."
    assert extract_json_object(raw) == {"a": 1}


def test_extracts_json_from_surrounding_prose():
    raw = "Sure! {\"next_node\": \"policy\", \"workflow_complete\": false} is my answer."
    assert extract_json_object(raw) == {"next_node": "policy", "workflow_complete": False}


def test_extracts_first_balanced_object_with_nested_braces():
    raw = 'prefix {"outer": {"inner": 1}} suffix'
    assert extract_json_object(raw) == {"outer": {"inner": 1}}


def test_raises_on_no_json_present():
    with pytest.raises(JSONExtractionError):
        extract_json_object("this response has no json in it at all")
