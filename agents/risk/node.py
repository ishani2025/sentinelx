"""
Risk Assessment Node — a single LangGraph node that performs pure LLM reasoning
(no tools, no retrieval, no SQL/FAISS/APIs). It combines the AWS investigation,
business context, policy context, and knowledge context into an enterprise risk
assessment. Returns ONLY risk_assessment, completed_nodes, reasoning_log.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

from .prompts import load_risk_assessment_prompt
from .logger import log, log_error
from .utils import (RiskAssessment, RiskNodeError, parse_json,
                    default_llm_call, grounded_assessment)


def _build_user_content(incident: dict, business: dict, policy: dict, knowledge: dict) -> str:
    """Serialize all upstream context for the LLM (this node never retrieves anything)."""
    return ("Estimate the enterprise risk for this incident using ALL supplied context.\n\n"
            f"AWS_INVESTIGATION:\n{json.dumps(incident, indent=2, default=str)}\n\n"
            f"BUSINESS_CONTEXT:\n{json.dumps(business, indent=2, default=str)}\n\n"
            f"POLICY_CONTEXT:\n{json.dumps(policy, indent=2, default=str)}\n\n"
            f"KNOWLEDGE_CONTEXT:\n{json.dumps(knowledge, indent=2, default=str)}")


def risk_assessment_node(
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

    log("node_started", node="Risk Assessment", incident=incident.get("incident_id"))
    if not incident:
        err = RiskNodeError(error="missing_incident", detail="Risk Assessment Node requires 'incident'.")
        return {"risk_assessment": err.model_dump(), "completed_nodes": ["Risk Assessment"],
                "reasoning_log": [f"[Risk Assessment][ERROR] {err.detail}"]}

    log("state_received", has_business=bool(business), has_policy=bool(policy), has_knowledge=bool(knowledge))

    assessment: Optional[RiskAssessment] = None
    system = load_risk_assessment_prompt()
    user = _build_user_content(incident, business, policy, knowledge)

    # ---- primary path: Llama 3.2 reasoning (JSON), grounded strictly in supplied state ----
    log("llm_started", node="Risk Assessment")
    try:
        data = parse_json(llm_call(system, user))
        if data:
            assessment = RiskAssessment.model_validate(data)
    except Exception as ex:
        log("risk_llm_error", error=str(ex))
    log("llm_finished", node="Risk Assessment")

    # ---- deterministic grounded fallback (never invents; uses only supplied state) ----
    if assessment is None:
        assessment = grounded_assessment(incident, business, policy, knowledge)
        source = "grounded_fallback"
    else:
        source = "llm"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    log("risk_assessment_generated", overall_risk=assessment.overall_risk,
        priority=assessment.priority, source=source, execution_ms=elapsed_ms)

    return {"risk_assessment": assessment.model_dump(),
            "completed_nodes": ["Risk Assessment"],
            "reasoning_log": [
                "Risk Assessment Node started.",
                f"Combined AWS investigation + business + policy + knowledge context ({source}).",
                f"Overall risk {assessment.overall_risk}, priority {assessment.priority}, "
                f"urgency {assessment.urgency}, confidence {assessment.confidence}.",
                f"Risk Assessment Node completed in {elapsed_ms} ms."]}


__all__ = ["risk_assessment_node"]
