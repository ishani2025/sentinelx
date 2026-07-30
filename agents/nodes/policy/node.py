"""
Policy Node — public entrypoint for the SentinelX LangGraph workflow.

Receives the InvestigationState, runs the internal Policy workflow, and returns ONLY:
    policy_context, completed_nodes, reasoning_log
No other state fields are modified.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from .database import make_session_factory, seed_if_empty
from .tools import PolicyRetrievalTool, PolicyReasoningTool
from .workflow import build_policy_graph
from .schemas import PolicyNodeError
from .logger import log, log_error
from .utils import Timer, default_llm_call


def policy_node(
    state: dict[str, Any],
    *,
    session_factory: Optional[Callable[[], Session]] = None,
    llm_call: Callable[[str, str], str] = default_llm_call,
    seed: bool = True,
) -> dict[str, Any]:
    """
    LangGraph node. Dependency-injectable session_factory and llm_call for testing.
    Returns a partial InvestigationState update.
    """
    with Timer() as t:
        incident_id = (state.get("incident") or {}).get("incident_id")
        log("node_started", node="Policy", incident=incident_id)

        # ---- guard: business_context must be present (produced upstream) ----
        if not state.get("business_context"):
            err = PolicyNodeError(error="missing_business_context",
                                  detail="Policy Node requires business_context from the Business Context Node.")
            log_error("node_precondition_failed", err.detail, node="Policy")
            return {"policy_context": err.model_dump(),
                    "completed_nodes": ["Policy"],
                    "reasoning_log": [f"[Policy][ERROR] {err.detail}"]}

        # ---- database (dependency injection with safe default) --------------
        try:
            sf = session_factory or make_session_factory()
            if seed:
                seed_if_empty(sf)
        except Exception as ex:  # PostgreSQL failure -> structured error
            err = PolicyNodeError(error="database_unavailable", detail=str(ex))
            log_error("node_db_error", ex, node="Policy")
            return {"policy_context": err.model_dump(),
                    "completed_nodes": ["Policy"],
                    "reasoning_log": [f"[Policy][ERROR] database unavailable: {ex}"]}

        # ---- run the internal LangGraph workflow ----------------------------
        try:
            retrieval = PolicyRetrievalTool(sf)
            reasoning = PolicyReasoningTool(llm_call)
            graph = build_policy_graph(retrieval, reasoning)
            result = graph.invoke({"incident": state.get("incident", {}),
                                   "business_context": state.get("business_context", {})})
        except Exception as ex:
            err = PolicyNodeError(error="policy_workflow_failed", detail=str(ex))
            log_error("node_workflow_error", ex, node="Policy")
            return {"policy_context": err.model_dump(),
                    "completed_nodes": ["Policy"],
                    "reasoning_log": [f"[Policy][ERROR] workflow failed: {ex}"]}

        policy_context = result.get("policy_context", {})
        reasoning_log = result.get("reasoning_log", [])
        log("node_finished", node="Policy",
            approval_required=policy_context.get("approval_required"), execution_ms=t.ms
            if hasattr(t, "ms") else None)

    return {"policy_context": policy_context,
            "completed_nodes": ["Policy"],
            "reasoning_log": reasoning_log + [f"Policy Node completed in {t.ms} ms."]}


__all__ = ["policy_node"]
