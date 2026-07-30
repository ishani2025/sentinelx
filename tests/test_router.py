"""Unit tests for the deterministic routing rules the Supervisor's proposals
are validated against.
"""
from __future__ import annotations

from graph.router import next_deterministic_node, validate_next_node
from schemas.enums import GraphNode


def test_next_deterministic_node_starts_with_business_context():
    assert next_deterministic_node([]) == GraphNode.BUSINESS_CONTEXT


def test_next_deterministic_node_skips_completed():
    assert next_deterministic_node(["business_context"]) == GraphNode.POLICY


def test_next_deterministic_node_waits_for_all_prerequisites_before_risk():
    # Only business_context and policy done - risk_assessment still needs knowledge.
    assert next_deterministic_node(["business_context", "policy"]) == GraphNode.KNOWLEDGE


def test_next_deterministic_node_reaches_risk_after_all_three_prereqs():
    completed = ["business_context", "policy", "knowledge"]
    assert next_deterministic_node(completed) == GraphNode.RISK_ASSESSMENT


def test_next_deterministic_node_reaches_response_after_risk():
    completed = ["business_context", "policy", "knowledge", "risk_assessment"]
    assert next_deterministic_node(completed) == GraphNode.RESPONSE_PLANNING


def test_next_deterministic_node_ends_when_all_complete():
    completed = ["business_context", "policy", "knowledge", "risk_assessment", "response_planning"]
    assert next_deterministic_node(completed) == GraphNode.END


def test_validate_next_node_accepts_valid_proposal():
    assert validate_next_node(GraphNode.BUSINESS_CONTEXT, []) == GraphNode.BUSINESS_CONTEXT


def test_validate_next_node_rejects_premature_risk_assessment():
    # risk_assessment proposed before its prerequisites are done -> falls back.
    result = validate_next_node(GraphNode.RISK_ASSESSMENT, ["business_context"])
    assert result == GraphNode.POLICY


def test_validate_next_node_rejects_already_completed_node():
    result = validate_next_node(GraphNode.BUSINESS_CONTEXT, ["business_context"])
    assert result == GraphNode.POLICY


def test_validate_next_node_rejects_premature_end():
    result = validate_next_node(GraphNode.END, ["business_context"])
    assert result == GraphNode.POLICY


def test_validate_next_node_accepts_end_when_everything_done():
    completed = ["business_context", "policy", "knowledge", "risk_assessment", "response_planning"]
    assert validate_next_node(GraphNode.END, completed) == GraphNode.END
