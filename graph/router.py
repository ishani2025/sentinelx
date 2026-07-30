"""Deterministic routing rules the Supervisor's LLM decision is validated
against.

The Supervisor node is an LLM, and local models occasionally propose an
invalid or premature transition. To keep the platform deterministic and
prevent invalid loops, every LLM-proposed `next_node` is checked here
against a fixed prerequisite graph before it is trusted; an invalid
proposal falls back to the next node in the canonical order whose
prerequisites are already satisfied.
"""
from __future__ import annotations

from schemas.enums import GraphNode

# Canonical order specialist nodes normally run in.
DEFAULT_ORDER: list[GraphNode] = [
    GraphNode.BUSINESS_CONTEXT,
    GraphNode.POLICY,
    GraphNode.KNOWLEDGE,
    GraphNode.RISK_ASSESSMENT,
    GraphNode.RESPONSE_PLANNING,
]

# Node -> set of nodes that must already be in completed_nodes before it can run.
PREREQUISITES: dict[GraphNode, set[GraphNode]] = {
    GraphNode.BUSINESS_CONTEXT: set(),
    GraphNode.POLICY: set(),
    GraphNode.KNOWLEDGE: set(),
    GraphNode.RISK_ASSESSMENT: {GraphNode.BUSINESS_CONTEXT, GraphNode.POLICY, GraphNode.KNOWLEDGE},
    GraphNode.RESPONSE_PLANNING: {GraphNode.RISK_ASSESSMENT},
}


def _is_valid(node: GraphNode, completed: set[GraphNode]) -> bool:
    if node in completed:
        return False
    return PREREQUISITES.get(node, set()).issubset(completed)


def next_deterministic_node(completed_nodes: list[str]) -> GraphNode:
    """Returns the next node per the canonical order/prerequisites, or END
    if every specialist node has completed.
    """
    completed = {GraphNode(name) for name in completed_nodes}
    for node in DEFAULT_ORDER:
        if _is_valid(node, completed):
            return node
    return GraphNode.END


def validate_next_node(proposed: GraphNode, completed_nodes: list[str]) -> GraphNode:
    """Validates the Supervisor's proposed next node against the
    prerequisite graph, falling back to the deterministic default order if
    the proposal is invalid (already completed, or prerequisites unmet).
    """
    completed = {GraphNode(name) for name in completed_nodes}

    if proposed == GraphNode.END:
        return GraphNode.END if not DEFAULT_ORDER or completed.issuperset(DEFAULT_ORDER) else next_deterministic_node(completed_nodes)

    if proposed in PREREQUISITES and _is_valid(proposed, completed):
        return proposed

    return next_deterministic_node(completed_nodes)


def route_from_supervisor(current_node: str) -> str:
    """Conditional-edge selector: maps the validated `current_node` on state
    to the LangGraph node name to execute next (or `END`).
    """
    return current_node
