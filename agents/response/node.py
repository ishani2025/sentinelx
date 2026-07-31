"""
Response Planning Node — a single LangGraph node that performs pure LLM reasoning
(no SQL / FAISS / APIs / AWS SDK / execution). It transforms all upstream context
(incident, business, policy, knowledge, risk) into a structured, policy-aware,
explainable enterprise response plan. Returns ONLY response_plan, completed_nodes,
reasoning_log. It NEVER executes any action.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

from .prompts import load_response_planning_prompt
from .logger import log, log_error
from .utils import (ResponsePlan, ResponseNodeError, parse_json,
                    default_llm_call, grounded_plan)


def _build_user_content(incident: dict, business: dict, policy: dict,
                        knowledge: dict, risk: dict) -> str:
    return ("Generate the enterprise incident response plan using ALL supplied context. "
            "Do not execute anything; only plan.\n\n"
            f"AWS_INVESTIGATION:\n{json.dumps(incident, indent=2, default=str)}\n\n"
            f"BUSINESS_CONTEXT:\n{json.dumps(business, indent=2, default=str)}\n\n"
            f"POLICY_CONTEXT:\n{json.dumps(policy, indent=2, default=str)}\n\n"
            f"KNOWLEDGE_CONTEXT:\n{json.dumps(knowledge, indent=2, default=str)}\n\n"
            f"RISK_ASSESSMENT:\n{json.dumps(risk, indent=2, default=str)}")


def response_planning_node(
    state: dict[str, Any],
    *,
    llm_call: Callable[[str, str], str] = default_llm_call,
) -> dict[str, Any]:
    """LangGraph node. `llm_call` (system, user) -> str is dependency-injectable for testing."""
    start = time.perf_counter()
    incident = state.get("incident") or {}
    business = state.get("business_context") or {}
    policy = state.get("policy_context") or {}
    knowledge = state.get("knowledge_context") or {}
    risk = state.get("risk_assessment") or {}
    prior_completed = list(state.get("completed_nodes") or [])
    prior_log = list(state.get("reasoning_log") or [])

    log("node_started", node="Response Planning", incident=incident.get("incident_id"))
    if not incident:
        err = ResponseNodeError(error="missing_incident", detail="Response Planning Node requires 'incident'.")
        return {"response_plan": err.model_dump(), "completed_nodes": prior_completed + ["Response"],
                "reasoning_log": prior_log + [f"[Response Planning][ERROR] {err.detail}"]}

    log("state_received", has_business=bool(business), has_policy=bool(policy),
        has_knowledge=bool(knowledge), has_risk=bool(risk))

    plan: Optional[ResponsePlan] = None
    system = load_response_planning_prompt()
    user = _build_user_content(incident, business, policy, knowledge, risk)

    log("llm_started", node="Response Planning")
    try:
        data = parse_json(llm_call(system, user))
        if data:
            plan = ResponsePlan.model_validate(data)
    except Exception as ex:
        log("response_llm_error", error=str(ex))
    log("llm_finished", node="Response Planning")

    if plan is None:  # deterministic grounded fallback (uses only supplied state)
        plan = grounded_plan(incident, business, policy, knowledge, risk)
        source = "grounded_fallback"
    else:
        source = "llm"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    approvals = sum(1 for a in plan.actions if a.requires_human_approval)
    log("response_plan_generated", steps=len(plan.actions), approvals=approvals,
        priority=plan.priority, source=source, execution_ms=elapsed_ms)

    return {"response_plan": plan.model_dump(),
            "completed_nodes": prior_completed + ["Response"],
            "reasoning_log": prior_log + [
                "Response Planning Node started.",
                f"Combined AWS + business + policy + knowledge + risk context ({source}).",
                f"Generated {len(plan.actions)}-step plan; {approvals} action(s) require human approval; "
                f"priority {plan.priority}, urgency {plan.estimated_urgency}.",
                f"Response Planning Node completed in {elapsed_ms} ms."]}


__all__ = ["response_planning_node"]
