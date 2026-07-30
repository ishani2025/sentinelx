"""Pydantic view of the InvestigationState, used to validate/serialize the
`POST /investigate` API response. The graph itself runs on the TypedDict in
`graph.state` (LangGraph's native state representation); this model is a
strict mirror of it for the API boundary.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.business_context import BusinessContext
from schemas.incident import Incident
from schemas.knowledge_context import KnowledgeContext
from schemas.policy_context import PolicyContext
from schemas.response_plan import ResponsePlan
from schemas.risk_assessment import RiskAssessment


class ReasoningLogEntry(BaseModel):
    node: str
    reason: str


class InvestigationStateModel(BaseModel):
    incident: Incident
    business_context: BusinessContext | None = None
    policy_context: PolicyContext | None = None
    knowledge_context: KnowledgeContext | None = None
    risk_assessment: RiskAssessment | None = None
    response_plan: ResponsePlan | None = None
    completed_nodes: list[str] = Field(default_factory=list)
    current_node: str
    workflow_complete: bool
    reasoning_log: list[ReasoningLogEntry] = Field(default_factory=list)
