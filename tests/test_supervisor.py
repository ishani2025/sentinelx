"""Unit tests for the Supervisor node: LLM proposal validation and the
deterministic fallback when the LLM call fails.
"""
from __future__ import annotations

from graph.state import initial_state
from graph.supervisor import supervisor_node
from models.llm import LLMOutputError
from schemas.enums import GraphNode
from schemas.supervisor import SupervisorDecision


def test_supervisor_node_uses_llm_proposal_when_valid(mocker, sample_incident):
    mocker.patch(
        "graph.supervisor.invoke_structured",
        return_value=SupervisorDecision(
            next_node=GraphNode.BUSINESS_CONTEXT, reason="Nothing gathered yet.", workflow_complete=False
        ),
    )

    result = supervisor_node(initial_state(sample_incident))

    assert result["current_node"] == "business_context"
    assert result["workflow_complete"] is False
    assert result["reasoning_log"][0]["node"] == "supervisor"


def test_supervisor_node_corrects_invalid_llm_proposal(mocker, sample_incident):
    # LLM proposes response_planning before any prerequisite has run - must be corrected.
    mocker.patch(
        "graph.supervisor.invoke_structured",
        return_value=SupervisorDecision(
            next_node=GraphNode.RESPONSE_PLANNING, reason="Let's skip ahead.", workflow_complete=False
        ),
    )

    result = supervisor_node(initial_state(sample_incident))

    assert result["current_node"] == "business_context"


def test_supervisor_node_falls_back_deterministically_on_llm_failure(mocker, sample_incident):
    mocker.patch("graph.supervisor.invoke_structured", side_effect=LLMOutputError("ollama unreachable"))

    state = initial_state(sample_incident)
    state["completed_nodes"] = ["business_context", "policy", "knowledge"]

    result = supervisor_node(state)

    assert result["current_node"] == "risk_assessment"
    assert "fallback" in result["reasoning_log"][0]["reason"].lower()
