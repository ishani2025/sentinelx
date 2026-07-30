"""
Business Context Node

Enterprise reference: departments, owners, criticality tiers and data
classifications used here are consistent with docs/governance/SentinelX_Security_Policy.md
(roles, data-classification scheme, and severity/criticality definitions). — a single LangGraph node implemented as a LangChain
tool-calling (ReAct-style) agent. The LLM decides which tools to invoke; the node
does not hardcode a fixed sequence. Returns ONLY business_context, completed_nodes,
reasoning_log.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from .database import make_session_factory, seed_if_empty
from .tools import (make_business_tools, resolve_asset_impl, normalize_impl, summary_impl)
from .schemas import BusinessContext, BusinessNodeError
from .prompts import load_business_context_prompt
from .logger import log, log_error
from .utils import Timer, get_chat_llm, default_summary_call, extract_aws_resource_ids

_MAX_ITERS = 8


def _assemble_context(normalized: dict[str, Any], summary: dict[str, Any]) -> BusinessContext:
    return BusinessContext(**normalized, summary=summary["summary"], reasoning=summary["reasoning"])


def _grounded_complete(session_factory, summary_call, incident: dict, collector: dict) -> Optional[BusinessContext]:
    """Safety net (grounded in PostgreSQL) if the LLM loop did not populate the collector."""
    normalized = collector.get("normalized")
    if not normalized:
        for rid in extract_aws_resource_ids(incident):
            res = resolve_asset_impl(session_factory, rid)
            if res:
                normalized = normalize_impl(session_factory, res.asset_id)
                collector["normalized"] = normalized
                break
    if not normalized:
        return None
    summary = collector.get("summary") or summary_impl(summary_call, normalized).model_dump()
    return _assemble_context(normalized, summary)


def business_context_node(
    state: dict[str, Any],
    *,
    session_factory: Optional[Callable[[], Session]] = None,
    llm: Any = None,
    summary_call: Callable[[str, str], str] = default_summary_call,
    seed: bool = True,
    max_iters: int = _MAX_ITERS,
) -> dict[str, Any]:
    """LangGraph node. `session_factory`, `llm`, and `summary_call` are dependency-injectable."""
    with Timer() as t:
        incident = state.get("incident") or {}
        log("node_started", node="Business Context", incident=incident.get("incident_id"))
        if not incident:
            err = BusinessNodeError(error="missing_incident", detail="Business Context Node requires 'incident'.")
            log_error("node_precondition_failed", err.detail, node="Business Context")
            return {"business_context": err.model_dump(), "completed_nodes": ["Business Context"],
                    "reasoning_log": [f"[Business Context][ERROR] {err.detail}"]}

        try:
            sf = session_factory or make_session_factory()
            if seed:
                seed_if_empty(sf)
        except Exception as ex:
            err = BusinessNodeError(error="database_unavailable", detail=str(ex))
            log_error("node_db_error", ex, node="Business Context")
            return {"business_context": err.model_dump(), "completed_nodes": ["Business Context"],
                    "reasoning_log": [f"[Business Context][ERROR] database unavailable: {ex}"]}

        collector: dict[str, Any] = {}
        reasoning_log: list[str] = ["Business Context Node started."]

        # ---- LangChain tool-calling (ReAct) loop; the LLM controls invocation ----
        try:
            from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
            tools = make_business_tools(sf, summary_call, collector)
            registry = {tl.name: tl for tl in tools}
            chat = (llm or get_chat_llm()).bind_tools(tools)

            resource_ids = extract_aws_resource_ids(incident)
            human = ("Enrich this AWS incident with enterprise business context. "
                     "Resolve the resource, retrieve its metadata, normalize it, then summarize.\n"
                     f"incident: {json.dumps({k: incident.get(k) for k in incident}, default=str)}\n"
                     f"candidate_aws_resource_ids: {resource_ids}")
            messages: list[Any] = [SystemMessage(content=load_business_context_prompt()),
                                   HumanMessage(content=human)]

            for _ in range(max_iters):
                ai = chat.invoke(messages)
                messages.append(ai)
                tool_calls = getattr(ai, "tool_calls", None) or []
                if not tool_calls:
                    break
                for tc in tool_calls:
                    tl = registry.get(tc["name"])
                    out = tl.invoke(tc.get("args", {})) if tl else f"unknown tool {tc['name']}"
                    reasoning_log.append(f"Tool '{tc['name']}' invoked by LLM.")
                    messages.append(ToolMessage(content=str(out), tool_call_id=tc.get("id", tc["name"])))
        except Exception as ex:
            # LLM/LangChain unavailable -> fall through to grounded completion
            log("business_toolloop_degraded", error=str(ex))
            reasoning_log.append(f"[Business Context] tool-calling loop degraded: {ex}")

        # ---- finalize (grounded in PostgreSQL; never invents) ----
        context = _grounded_complete(sf, summary_call, incident, collector)
        if context is None:
            err = BusinessNodeError(error="asset_not_found",
                detail="No enterprise asset matched the incident's AWS resources.")
            log_error("business_context_not_found", err.detail, node="Business Context")
            return {"business_context": err.model_dump(), "completed_nodes": ["Business Context"],
                    "reasoning_log": reasoning_log + [f"[Business Context][ERROR] {err.detail}"]}

        log("business_context_generated", asset=context.asset_name, department=context.department)
    return {"business_context": context.model_dump(),
            "completed_nodes": ["Business Context"],
            "reasoning_log": reasoning_log + [
                f"Business context generated for '{context.asset_name}' "
                f"({context.department}, {context.criticality}).",
                f"Business Context Node completed in {t.ms} ms."]}


__all__ = ["business_context_node"]
