"""The shared InvestigationState that flows through the entire graph.

Every node reads whatever sections it needs and writes back a partial
update covering ONLY its own section, plus an entry appended to
`completed_nodes` and `reasoning_log`. LangGraph merges partial updates
into the running state; `completed_nodes` and `reasoning_log` use the
`operator.add` reducer so successive partial updates accumulate instead of
overwriting each other.
"""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from schemas.business_context import BusinessContext
from schemas.incident import Incident
from schemas.knowledge_context import KnowledgeContext
from schemas.policy_context import PolicyContext
from schemas.response_plan import ResponsePlan
from schemas.risk_assessment import RiskAssessment


class ReasoningLogEntry(TypedDict):
    node: str
    reason: str


class InvestigationState(TypedDict, total=False):
    incident: Incident
    business_context: BusinessContext | None
    policy_context: PolicyContext | None
    knowledge_context: KnowledgeContext | None
    risk_assessment: RiskAssessment | None
    response_plan: ResponsePlan | None
    completed_nodes: Annotated[list[str], operator.add]
    current_node: str
    workflow_complete: bool
    reasoning_log: Annotated[list[ReasoningLogEntry], operator.add]


def initial_state(incident: Incident) -> InvestigationState:
    """Builds the starting state for a fresh investigation."""
    return InvestigationState(
        incident=incident,
        business_context=None,
        policy_context=None,
        knowledge_context=None,
        risk_assessment=None,
        response_plan=None,
        completed_nodes=[],
        current_node="supervisor",
        workflow_complete=False,
        reasoning_log=[],
    )
