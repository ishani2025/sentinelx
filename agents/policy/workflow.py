"""Internal LangGraph workflow for the Policy Node.
START -> extract_incident_information -> retrieve_policies -> retrieve_approval_rules
      -> retrieve_compliance -> retrieve_escalation_matrix -> llm_policy_reasoning
      -> generate_policy_context -> END"""
from __future__ import annotations
from typing import Callable, Optional, TypedDict
from .tools import PolicyRetrievalTool, PolicyReasoningTool
from .schemas import PolicyContext
from .logger import log
from .utils import normalize_asset_type, derive_action, severity_from_criticality

class PolicyGraphState(TypedDict, total=False):
    incident: dict; business_context: dict
    department: Optional[str]; asset_type: Optional[str]; criticality: Optional[str]
    environment: Optional[str]; action: Optional[str]; severity: Optional[str]
    policies: list; approval_rules: list; compliance: list; escalation: object
    policy_context: dict; reasoning_log: list

def extract_incident_information(state: PolicyGraphState) -> dict:
    bc = state.get("business_context") or {}; incident = state.get("incident") or {}
    department = bc.get("department"); criticality = bc.get("criticality"); environment = bc.get("environment")
    asset_type = normalize_asset_type(bc.get("asset_type") or bc.get("affected_asset") or bc.get("application"))
    action = derive_action(asset_type, incident); severity = severity_from_criticality(criticality, incident)
    log("policy_extract", department=department, asset_type=asset_type, criticality=criticality,
        environment=environment, action=action, severity=severity)
    return {"department":department,"asset_type":asset_type,"criticality":criticality,"environment":environment,
            "action":action,"severity":severity,"reasoning_log":["Incident information extracted from business context."]}

def make_retrieve_policies(tool):
    def _run(state):
        rows = tool.get_policies(state.get("department"),state.get("asset_type"),state.get("criticality"),state.get("action"))
        return {"policies":rows,"reasoning_log":state.get("reasoning_log",[])+[f"Retrieved {len(rows)} enterprise policy(ies)."]}
    return _run

def make_retrieve_approval_rules(tool):
    def _run(state):
        rows = tool.get_approval_rules(state.get("department"),state.get("criticality"),state.get("action"))
        return {"approval_rules":rows,"reasoning_log":state.get("reasoning_log",[])+[f"Retrieved {len(rows)} approval rule(s)."]}
    return _run

def make_retrieve_compliance(tool):
    def _run(state):
        ids = list({p.compliance_id for p in state.get("policies",[]) if p.compliance_id})
        rows = tool.get_compliance(ids)
        return {"compliance":rows,"reasoning_log":state.get("reasoning_log",[])+[f"Retrieved {len(rows)} compliance standard(s)."]}
    return _run

def make_retrieve_escalation(tool):
    def _run(state):
        row = tool.get_escalation(state.get("department"),state.get("severity"))
        return {"escalation":row,"reasoning_log":state.get("reasoning_log",[])+["Escalation path resolved." if row else "No escalation rule matched."]}
    return _run

def make_llm_reasoning(tool):
    def _run(state):
        ctx = tool.reason(state.get("policies",[]),state.get("approval_rules",[]),state.get("compliance",[]),state.get("escalation"))
        return {"policy_context":ctx.model_dump(),"reasoning_log":state.get("reasoning_log",[])+["Policies interpreted by LLM policy agent."]}
    return _run

def generate_policy_context(state):
    approval = (state.get("policy_context") or {}).get("approval_required", False)
    return {"reasoning_log":state.get("reasoning_log",[])+[f"Policy context generated (approval_required={approval})."]}

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
