"""
Internal LangGraph workflow for the Policy Node.

START -> extract_incident_information -> retrieve_policies -> retrieve_approval_rules
      -> retrieve_compliance -> retrieve_escalation_matrix -> llm_policy_reasoning
      -> generate_policy_context -> END

Each stage is a small, modular function operating on PolicyGraphState. The compiled
graph is dependency-injected with the retrieval + reasoning tools.
"""
from __future__ import annotations

from typing import Callable, Optional, TypedDict

from .tools import PolicyRetrievalTool, PolicyReasoningTool
from .schemas import PolicyContext
from .logger import log
from .utils import (normalize_asset_type, derive_action, severity_from_criticality)


class PolicyGraphState(TypedDict, total=False):
    incident: dict
    business_context: dict
    # extracted query params
    department: Optional[str]
    asset_type: Optional[str]
    criticality: Optional[str]
    environment: Optional[str]
    action: Optional[str]
    severity: Optional[str]
    # retrieved records
    policies: list
    approval_rules: list
    compliance: list
    escalation: object
    # output
    policy_context: dict
    reasoning_log: list


# --------------------------------------------------------------------------- #
# Stage functions (each returns a partial state update)
# --------------------------------------------------------------------------- #
def extract_incident_information(state: PolicyGraphState) -> dict:
    bc = state.get("business_context") or {}
    incident = state.get("incident") or {}
    department = bc.get("department")
    criticality = bc.get("criticality")
    environment = bc.get("environment")
    asset_type = normalize_asset_type(
        bc.get("asset_type") or bc.get("affected_asset") or bc.get("application"))
    action = derive_action(asset_type, incident)
    severity = severity_from_criticality(criticality, incident)
    log("policy_extract", department=department, asset_type=asset_type,
        criticality=criticality, environment=environment, action=action, severity=severity)
    return {"department": department, "asset_type": asset_type, "criticality": criticality,
            "environment": environment, "action": action, "severity": severity,
            "reasoning_log": ["Incident information extracted from business context."]}


def make_retrieve_policies(tool: PolicyRetrievalTool) -> Callable[[PolicyGraphState], dict]:
    def _run(state: PolicyGraphState) -> dict:
        rows = tool.get_policies(state.get("department"), state.get("asset_type"),
                                 state.get("criticality"), state.get("action"))
        return {"policies": rows,
                "reasoning_log": state.get("reasoning_log", []) + [f"Retrieved {len(rows)} enterprise policy(ies)."]}
    return _run


def make_retrieve_approval_rules(tool: PolicyRetrievalTool) -> Callable[[PolicyGraphState], dict]:
    def _run(state: PolicyGraphState) -> dict:
        rows = tool.get_approval_rules(state.get("department"), state.get("criticality"), state.get("action"))
        return {"approval_rules": rows,
                "reasoning_log": state.get("reasoning_log", []) + [f"Retrieved {len(rows)} approval rule(s)."]}
    return _run


def make_retrieve_compliance(tool: PolicyRetrievalTool) -> Callable[[PolicyGraphState], dict]:
    def _run(state: PolicyGraphState) -> dict:
        ids = list({p.compliance_id for p in state.get("policies", []) if p.compliance_id})
        rows = tool.get_compliance(ids)
        return {"compliance": rows,
                "reasoning_log": state.get("reasoning_log", []) + [f"Retrieved {len(rows)} compliance standard(s)."]}
    return _run


def make_retrieve_escalation(tool: PolicyRetrievalTool) -> Callable[[PolicyGraphState], dict]:
    def _run(state: PolicyGraphState) -> dict:
        row = tool.get_escalation(state.get("department"), state.get("severity"))
        return {"escalation": row,
                "reasoning_log": state.get("reasoning_log", []) + ["Escalation path resolved." if row else "No escalation rule matched."]}
    return _run


def make_llm_reasoning(tool: PolicyReasoningTool) -> Callable[[PolicyGraphState], dict]:
    def _run(state: PolicyGraphState) -> dict:
        ctx: PolicyContext = tool.reason(state.get("policies", []), state.get("approval_rules", []),
                                         state.get("compliance", []), state.get("escalation"))
        return {"policy_context": ctx.model_dump(),
                "reasoning_log": state.get("reasoning_log", []) + ["Policies interpreted by LLM policy agent."]}
    return _run


def generate_policy_context(state: PolicyGraphState) -> dict:
    ctx = state.get("policy_context") or {}
    approval = ctx.get("approval_required", False)
    return {"reasoning_log": state.get("reasoning_log", []) +
            [f"Policy context generated (approval_required={approval})."]}


# --------------------------------------------------------------------------- #
# Graph builder (dependency injection of tools)
# --------------------------------------------------------------------------- #
def build_policy_graph(retrieval: PolicyRetrievalTool, reasoning: PolicyReasoningTool):
    from langgraph.graph import StateGraph, START, END
    g = StateGraph(PolicyGraphState)
    g.add_node("extract_incident_information", extract_incident_information)
    g.add_node("retrieve_policies", make_retrieve_policies(retrieval))
    g.add_node("retrieve_approval_rules", make_retrieve_approval_rules(retrieval))
    g.add_node("retrieve_compliance", make_retrieve_compliance(retrieval))
    g.add_node("retrieve_escalation_matrix", make_retrieve_escalation(retrieval))
    g.add_node("llm_policy_reasoning", make_llm_reasoning(reasoning))
    g.add_node("generate_policy_context", generate_policy_context)

    g.add_edge(START, "extract_incident_information")
    g.add_edge("extract_incident_information", "retrieve_policies")
    g.add_edge("retrieve_policies", "retrieve_approval_rules")
    g.add_edge("retrieve_approval_rules", "retrieve_compliance")
    g.add_edge("retrieve_compliance", "retrieve_escalation_matrix")
    g.add_edge("retrieve_escalation_matrix", "llm_policy_reasoning")
    g.add_edge("llm_policy_reasoning", "generate_policy_context")
    g.add_edge("generate_policy_context", END)
    return g.compile()
