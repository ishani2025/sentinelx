"""Assembles the single Sentinelx LangGraph workflow.

START -> Supervisor -> (Business Context | Policy | Knowledge | Risk
Assessment | Response Planning | END) -> back to Supervisor -> ... -> END.

Every specialist node has an unconditional edge back to the Supervisor;
only the Supervisor's outgoing edge is conditional, driven by
`graph.router.route_from_supervisor` reading the `current_node` the
Supervisor just validated and wrote to state.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from graph.router import route_from_supervisor
from graph.state import InvestigationState, initial_state
from graph.supervisor import supervisor_node
from nodes.business.node import business_context_node
from nodes.knowledge.node import knowledge_node
from nodes.policy.node import policy_node
from nodes.response.node import response_planning_node
from nodes.risk.node import risk_assessment_node
from schemas.enums import GraphNode
from schemas.incident import Incident
from utils.logging import get_logger

logger = get_logger(__name__)

_SPECIALIST_NODES: dict[GraphNode, callable] = {
    GraphNode.BUSINESS_CONTEXT: business_context_node,
    GraphNode.POLICY: policy_node,
    GraphNode.KNOWLEDGE: knowledge_node,
    GraphNode.RISK_ASSESSMENT: risk_assessment_node,
    GraphNode.RESPONSE_PLANNING: response_planning_node,
}

_ROUTE_MAP = {node.value: node.value for node in _SPECIALIST_NODES} | {GraphNode.END.value: END}


def build_graph() -> CompiledStateGraph:
    """Builds and compiles the SentinelX investigation graph."""
    graph = StateGraph(InvestigationState)

    graph.add_node(GraphNode.SUPERVISOR.value, supervisor_node)
    for node, fn in _SPECIALIST_NODES.items():
        graph.add_node(node.value, fn)

    graph.add_edge(START, GraphNode.SUPERVISOR.value)
    graph.add_conditional_edges(
        GraphNode.SUPERVISOR.value,
        lambda state: route_from_supervisor(state["current_node"]),
        _ROUTE_MAP,
    )
    for node in _SPECIALIST_NODES:
        graph.add_edge(node.value, GraphNode.SUPERVISOR.value)

    return graph.compile()


_compiled_graph: CompiledStateGraph | None = None


def get_compiled_graph() -> CompiledStateGraph:
    """Returns a process-wide cached compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_investigation(incident: Incident) -> InvestigationState:
    """Runs the full investigation graph for `incident` to completion and
    returns the final InvestigationState.
    """
    logger.info("investigation_start", incident_id=incident.incident_id)
    graph = get_compiled_graph()
    # +2 headroom over the 6 supervisor round-trips (5 specialists + END) the
    # canonical path takes, so a couple of invalid-proposal recoveries don't
    # trip LangGraph's recursion guard.
    final_state = graph.invoke(initial_state(incident), config={"recursion_limit": 25})
    logger.info(
        "investigation_complete",
        incident_id=incident.incident_id,
        completed_nodes=final_state.get("completed_nodes"),
    )
    return final_state
