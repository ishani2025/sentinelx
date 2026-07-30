"""
Knowledge Node — a single LangGraph node implemented as a LangChain tool-calling agent.
It retrieves enterprise knowledge (playbooks, TheHive cases, threat intel) from a single
FAISS store and COMPARES it against the AWS investigation to produce evidence-backed,
improved recommendations. Returns ONLY knowledge_context, completed_nodes, reasoning_log.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

from .vector_store import KnowledgeVectorStore
from .retriever import KnowledgeRetriever
from .tools import make_knowledge_tools
from .prompts import load_knowledge_prompt, load_synthesis_prompt
from .logger import log, log_error
from .utils import (KnowledgeContext, KnowledgeNodeError, SupportingEvidence,
                    parse_json, get_chat_llm, default_synthesis_call)

_MAX_ITERS = 6


# --------------------------------------------------------------------------- #
# Helpers: extract AWS recs + attack signal from the incident
# --------------------------------------------------------------------------- #
def _aws_recommendations(incident: dict) -> list[str]:
    for key in ("aws_recommendations", "generic_recommendations", "recommendations"):
        v = incident.get(key)
        if isinstance(v, list) and v:
            return [str(x) for x in v]
    report = incident.get("aws_investigation_report") or incident.get("guardduty_report") or {}
    if isinstance(report, dict):
        v = report.get("recommendations")
        if isinstance(v, list):
            return [str(x) for x in v]
    return []


def _attack_signal(incident: dict, business_context: dict) -> dict[str, Optional[str]]:
    mitre = incident.get("mitre_mapping") or incident.get("mitre") or []
    mt = mitre[0] if isinstance(mitre, list) and mitre else (mitre if isinstance(mitre, str) else None)
    return {"attack_type": incident.get("attack_type") or incident.get("attack"),
            "asset_type": (business_context or {}).get("asset_type"),
            "mitre_technique": mt,
            "query": incident.get("attack_summary") or incident.get("summary") or str(mitre)}


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch == " ").strip()


# --------------------------------------------------------------------------- #
# Grounded synthesis (used if the LLM synthesis is unavailable) — never invents
# --------------------------------------------------------------------------- #
def _grounded_synthesis(aws_recs: list[str], collector: dict) -> KnowledgeContext:
    playbooks, cases = collector.get("playbooks", []), collector.get("cases", [])
    ti = collector.get("threat_intel", [])

    pb_out, extra_steps, evidence = [], [], []
    _seen_pb, _seen_case = set(), set()
    playbooks = [d for d in playbooks if not (d["metadata"].get("path") in _seen_pb or _seen_pb.add(d["metadata"].get("path")))]
    for d in playbooks:
        steps = [ln.strip("- ").strip() for ln in d["content"].splitlines()
                 if ln.strip().startswith("-") and "remediat" not in ln.lower()]
        title = d["metadata"].get("title", d["metadata"].get("path", "playbook"))
        pb_out.append({"title": title, "remediation_steps": steps[:8]})
        extra_steps.extend(steps)
        evidence.append(SupportingEvidence(source_type="playbook", reference=title,
                        excerpt=d["content"][:160]))
    case_out = []
    for d in cases:
        try:
            obj = json.loads(d["content"])
        except Exception:
            obj = {}
        _cid = obj.get("case_id") or d["metadata"].get("path")
        if _cid in _seen_case:
            continue
        _seen_case.add(_cid)
        case_out.append({"case_id": obj.get("case_id", "?"),
                         "summary": obj.get("incident_summary", ""),
                         "actions_taken": obj.get("actions_taken", []),
                         "outcome": obj.get("outcome", ""),
                         "lessons_learned": obj.get("lessons_learned", "")})
        if obj.get("lessons_learned"):
            extra_steps.append(obj["lessons_learned"])
        evidence.append(SupportingEvidence(source_type="thehive_case",
                        reference=obj.get("case_id", d["metadata"].get("path", "case")),
                        excerpt=obj.get("lessons_learned", "")[:160]))
    for d in ti:
        evidence.append(SupportingEvidence(source_type=d["metadata"].get("source_type", "threat_intel"),
                        reference=d["metadata"].get("title", d["metadata"].get("path", "intel")),
                        excerpt=d["content"][:160]))

    # enterprise recs = AWS recs first, then non-duplicate enterprise additions
    seen = {_norm(r) for r in aws_recs}
    additions: list[str] = []
    for s in extra_steps:
        n = _norm(s)
        if n and n not in seen and len(s) > 4:
            additions.append(s); seen.add(n)
    enterprise = aws_recs + additions
    reasoning = ("Compared AWS generic recommendations against enterprise playbooks and "
                 f"{len(cases)} historical case(s). Enterprise knowledge adds {len(additions)} "
                 "step(s) AWS omitted (e.g., STS session revocation, host isolation, DPO notification).")
    return KnowledgeContext(similar_cases=case_out, retrieved_playbooks=pb_out,
                            enterprise_recommendations=enterprise,
                            missing_aws_recommendations=additions,
                            supporting_evidence=evidence, reasoning=reasoning)


def _llm_synthesis(synthesis_call: Callable[[str, str], str], aws_recs: list[str],
                   collector: dict) -> Optional[KnowledgeContext]:
    payload = {"aws_recommendations": aws_recs,
               "retrieved_playbooks": collector.get("playbooks", []),
               "historical_cases": collector.get("cases", []),
               "threat_intel": collector.get("threat_intel", [])}
    try:
        data = parse_json(synthesis_call(load_synthesis_prompt(),
                          "Evidence (use ONLY this):\n" + json.dumps(payload, indent=2)))
        if data:
            return KnowledgeContext.model_validate(data)
    except Exception as ex:
        log("knowledge_synthesis_llm_error", error=str(ex))
    return None


# --------------------------------------------------------------------------- #
# Node
# --------------------------------------------------------------------------- #
def knowledge_node(
    state: dict[str, Any],
    *,
    vector_store: Optional[KnowledgeVectorStore] = None,
    llm: Any = None,
    synthesis_call: Callable[[str, str], str] = default_synthesis_call,
    max_iters: int = _MAX_ITERS,
) -> dict[str, Any]:
    """LangGraph node. vector_store, llm, and synthesis_call are dependency-injectable."""
    start = time.perf_counter()
    incident = state.get("incident") or {}
    business_context = state.get("business_context") or {}
    log("node_started", node="Knowledge", incident=incident.get("incident_id"))
    if not incident:
        err = KnowledgeNodeError(error="missing_incident", detail="Knowledge Node requires 'incident'.")
        return {"knowledge_context": err.model_dump(), "completed_nodes": ["Knowledge"],
                "reasoning_log": [f"[Knowledge][ERROR] {err.detail}"]}

    try:
        store = vector_store or KnowledgeVectorStore()
        retriever = KnowledgeRetriever(store)
    except Exception as ex:
        err = KnowledgeNodeError(error="vector_store_unavailable", detail=str(ex))
        log_error("node_vs_error", ex, node="Knowledge")
        return {"knowledge_context": err.model_dump(), "completed_nodes": ["Knowledge"],
                "reasoning_log": [f"[Knowledge][ERROR] vector store unavailable: {ex}"]}

    collector: dict[str, Any] = {}
    reasoning_log: list[str] = ["Knowledge Node started."]
    sig = _attack_signal(incident, business_context)
    aws_recs = _aws_recommendations(incident)

    # ---- tool-calling (ReAct) loop; LLM chooses retrievers ----
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
        tools = make_knowledge_tools(retriever, collector)
        registry = {t.name: t for t in tools}
        chat = (llm or get_chat_llm()).bind_tools(tools)
        human = ("Enrich this AWS investigation with enterprise knowledge. Retrieve relevant "
                 "playbooks, similar historical cases, and threat intel, then compare against the "
                 "AWS recommendations.\n"
                 f"attack_signal: {json.dumps(sig)}\naws_recommendations: {json.dumps(aws_recs)}")
        messages: list[Any] = [SystemMessage(content=load_knowledge_prompt()), HumanMessage(content=human)]
        for _ in range(max_iters):
            ai = chat.invoke(messages); messages.append(ai)
            tcs = getattr(ai, "tool_calls", None) or []
            if not tcs:
                break
            for tc in tcs:
                tl = registry.get(tc["name"])
                out = tl.invoke(tc.get("args", {})) if tl else f"unknown tool {tc['name']}"
                reasoning_log.append(f"Retriever '{tc['name']}' invoked by LLM.")
                messages.append(ToolMessage(content=str(out), tool_call_id=tc.get("id", tc["name"])))
    except Exception as ex:
        log("knowledge_toolloop_degraded", error=str(ex))
        reasoning_log.append(f"[Knowledge] tool-calling loop degraded: {ex}")

    # ---- grounded fallback retrieval if the LLM retrieved nothing ----
    if not any(collector.get(k) for k in ("playbooks", "cases", "threat_intel")):
        collector["playbooks"] = retriever.playbooks(sig["query"] or "", sig["attack_type"], sig["asset_type"])
        collector["cases"] = retriever.cases(sig["query"] or "", sig["attack_type"], sig["asset_type"])
        collector["threat_intel"] = (retriever.threat_intel(sig["query"] or "", sig["mitre_technique"]) +
                                     retriever.mitre(sig["query"] or "", sig["mitre_technique"]))
        reasoning_log.append("Grounded retrieval executed (LLM tool loop unavailable).")

    log("documents_retrieved", playbooks=len(collector.get("playbooks", [])),
        cases=len(collector.get("cases", [])), threat_intel=len(collector.get("threat_intel", [])))

    # ---- synthesis: compare AWS vs enterprise (LLM, else grounded) ----
    log("llm_started", stage="synthesis")
    context = _llm_synthesis(synthesis_call, aws_recs, collector) or _grounded_synthesis(aws_recs, collector)
    log("llm_finished", stage="synthesis")

    if not context.retrieved_playbooks and not context.similar_cases:
        context.reasoning = (context.reasoning or "") + " No enterprise knowledge matched; AWS recommendations retained."

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    log("knowledge_generated", additions=len(context.missing_aws_recommendations), execution_ms=elapsed_ms)
    return {"knowledge_context": context.model_dump(),
            "completed_nodes": ["Knowledge"],
            "reasoning_log": reasoning_log + [
                f"Knowledge context generated: {len(context.missing_aws_recommendations)} "
                f"enterprise addition(s) to AWS recommendations.",
                f"Knowledge Node completed in {elapsed_ms} ms."]}


__all__ = ["knowledge_node"]
