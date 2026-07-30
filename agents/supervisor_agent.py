"""
SentinelX — Supervisor Node (single-file LangGraph orchestrator)
================================================================

The Supervisor is the ONLY component that decides workflow routing. It owns the
InvestigationState, updates it after each specialized node, and decides when the
workflow is complete. It performs NO cybersecurity analysis, context retrieval,
risk estimation, or remediation — orchestration only.

Everything is in this one file:
  1. Supervisor system prompt (+ loader)
  2. Shared LLM helper (Llama 3.2 via Ollama, single instance)
  3. InvestigationState schema
  4. Structured logging
  5. State validator
  6. JSON parser (with one retry in the node)
  7. Supervisor node
  8. Router function (pure lookup)
  9. Conditional edge mapping / graph builder

Run for real:  pip install langgraph langchain-ollama  &&  ollama pull llama3.2
"""
from __future__ import annotations

import json
import logging
import re
import time
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, TypedDict
import os
SUPERVISOR_SYSTEM_PROMPT = """\
You are the Supervisor of SentinelX.
You are an enterprise workflow orchestrator.

You NEVER solve incidents.
You NEVER retrieve business context.
You NEVER retrieve policies.
You NEVER retrieve knowledge.
You NEVER estimate risk.
You NEVER generate remediation.
You ONLY decide which specialized workflow node should execute next.

You receive the complete InvestigationState. Reason ONLY over that state.

Valid node names: "Business", "Policy", "Knowledge", "Risk", "Response".

Decide, based purely on the current InvestigationState:
  - which node should execute next
  - why
  - whether the whole investigation is complete

Selection guidance (decide dynamically from what is present/absent in the state):
  - business_context missing                          -> "Business"
  - business_context present, policy_context missing  -> "Policy"
  - business + policy present, knowledge missing       -> "Knowledge"
  - all context present, risk_assessment missing       -> "Risk"
  - risk_assessment present, response_plan missing      -> "Response"
  - response_plan present                               -> workflow_complete = true

You MUST return ONLY valid JSON, no prose, in exactly this shape:
{
  "next_node": "<Business|Policy|Knowledge|Risk|Response|END>",
  "workflow_complete": <true|false>,
  "reason": "<one or two sentence justification>"
}
"""


def load_supervisor_prompt() -> str:
    return SUPERVISOR_SYSTEM_PROMPT


# =========================================================================== #
# 2. SHARED LLM HELPER  (instantiate once; nodes never create their own client)
# =========================================================================== #
DEFAULT_MODEL = os.getenv("SENTINELX_LLM_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@lru_cache(maxsize=1)
def get_llm(model: str = DEFAULT_MODEL, temperature: float = 0.0):
    """Singleton ChatOllama configured for deterministic JSON output."""
    from langchain_ollama import ChatOllama  # lazy import so this file imports cleanly
    return ChatOllama(model=model, base_url=OLLAMA_BASE_URL,
                      temperature=temperature, format="json")


def chat(system_prompt: str, user_content: str) -> str:
    """Single-turn call. Returns raw model text (expected JSON)."""
    from langchain_core.messages import SystemMessage, HumanMessage
    resp = get_llm().invoke([SystemMessage(content=system_prompt),
                             HumanMessage(content=user_content)])
    return resp.content if hasattr(resp, "content") else str(resp)


# =========================================================================== #
# 3. INVESTIGATION STATE SCHEMA
# =========================================================================== #
class InvestigationState(TypedDict, total=False):
    incident: dict
    business_context: Optional[dict]
    policy_context: Optional[dict]
    knowledge_context: Optional[dict]
    risk_assessment: Optional[dict]
    response_plan: Optional[dict]
    completed_nodes: list
    current_node: str
    next_node: str
    workflow_complete: bool
    reasoning_log: list


VALID_NODES = ["Business", "Policy", "Knowledge", "Risk", "Response", "END"]


# =========================================================================== #
# 4. STRUCTURED LOGGING
# =========================================================================== #
logger = logging.getLogger("sentinelx.supervisor")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","component":"%(name)s","msg":"%(message)s"}'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


def _log(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, default=str))


# =========================================================================== #
# 5. STATE VALIDATOR  (never crash on a missing field)
# =========================================================================== #
def validate_state(state: InvestigationState) -> InvestigationState:
    if not isinstance(state, dict):
        raise TypeError("InvestigationState must be a dict-like object")
    defaults: Dict[str, Any] = {
        "incident": {}, "business_context": None, "policy_context": None,
        "knowledge_context": None, "risk_assessment": None, "response_plan": None,
        "completed_nodes": [], "current_node": "Supervisor", "next_node": "",
        "workflow_complete": False, "reasoning_log": [],
    }
    for k, v in defaults.items():
        state.setdefault(k, v)
    for k in ("completed_nodes", "reasoning_log"):
        if state.get(k) is None:
            state[k] = []
    return state


def _state_summary(state: InvestigationState) -> Dict[str, Any]:
    return {
        "incident_present": bool(state.get("incident")),
        "business_context": state.get("business_context") is not None,
        "policy_context": state.get("policy_context") is not None,
        "knowledge_context": state.get("knowledge_context") is not None,
        "risk_assessment": state.get("risk_assessment") is not None,
        "response_plan": state.get("response_plan") is not None,
        "completed_nodes": state.get("completed_nodes", []),
    }


# =========================================================================== #
# 6. JSON PARSER  (tolerant)
# =========================================================================== #
def parse_decision(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _valid_decision(d: Any) -> bool:
    return (isinstance(d, dict) and d.get("next_node") in VALID_NODES
            and isinstance(d.get("workflow_complete", False), bool))


# =========================================================================== #
# 7. SUPERVISOR NODE
# =========================================================================== #
def supervisor_node(state: InvestigationState) -> InvestigationState:
    start = time.perf_counter()
    state = validate_state(state)
    _log("supervisor_started",
         incident=state.get("incident", {}).get("incident_id"),
         state=_state_summary(state))

    system = load_supervisor_prompt()
    user = "Current InvestigationState (presence flags):\n" + json.dumps(_state_summary(state), indent=2)

    decision, last_error = None, ""
    for attempt in (1, 2):  # call + one retry
        try:
            raw = chat(system, user)
            decision = parse_decision(raw)
            if _valid_decision(decision):
                break
            last_error = f"invalid decision on attempt {attempt}: {str(raw)[:200]!r}"
            _log("supervisor_parse_retry", attempt=attempt, error=last_error)
            decision = None
        except Exception as ex:
            last_error = f"llm_error attempt {attempt}: {ex}"
            _log("supervisor_llm_error", attempt=attempt, error=str(ex))
            decision = None

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    if decision is None:  # structured error; end cleanly, do not crash the graph
        state["next_node"] = "END"
        state["workflow_complete"] = True
        state["reasoning_log"].append(f"[Supervisor][ERROR] {last_error}")
        _log("supervisor_error", elapsed_ms=elapsed_ms, error=last_error)
        return state

    next_node = "END" if decision.get("workflow_complete") else decision["next_node"]
    state["current_node"] = "Supervisor"
    state["next_node"] = next_node
    state["workflow_complete"] = bool(decision.get("workflow_complete", False)) or next_node == "END"
    reason = decision.get("reason", "")
    state["reasoning_log"].append(f"[Supervisor] -> {next_node}: {reason}")

    _log("supervisor_decision", next_node=next_node,
         workflow_complete=state["workflow_complete"], reason=reason, elapsed_ms=elapsed_ms)
    if state["workflow_complete"]:
        _log("workflow_complete", completed_nodes=state.get("completed_nodes", []), elapsed_ms=elapsed_ms)
    return state


def mark_node_complete(state: InvestigationState, node_name: str) -> InvestigationState:
    """Specialized nodes call this at the end of their run to record completion."""
    state = validate_state(state)
    if node_name not in state["completed_nodes"]:
        state["completed_nodes"].append(node_name)
    state["current_node"] = node_name
    return state


# =========================================================================== #
# 8. ROUTER  (pure lookup — no reasoning, no business logic)
# =========================================================================== #
def router(state: InvestigationState) -> str:
    return state.get("next_node") or "END"


# =========================================================================== #
# 9. CONDITIONAL EDGE MAPPING / GRAPH BUILDER
# =========================================================================== #
def build_graph(nodes: Dict[str, Callable[[InvestigationState], InvestigationState]]):
    """
    Wire the StateGraph. `nodes` maps the five specialized node names to callables.
    START -> Supervisor -> (conditional) specialized node -> Supervisor -> ... -> END.
    Specialized nodes never call each other; only the Supervisor routes.
    """
    from langgraph.graph import StateGraph, START, END

    g = StateGraph(InvestigationState)
    g.add_node("Supervisor", supervisor_node)
    for name in ("Business", "Policy", "Knowledge", "Risk", "Response"):
        if name not in nodes:
            raise ValueError(f"missing specialized node implementation: {name}")
        g.add_node(name, nodes[name])

    g.add_edge(START, "Supervisor")
    g.add_conditional_edges(
        "Supervisor", router,
        {"Business": "Business", "Policy": "Policy", "Knowledge": "Knowledge",
         "Risk": "Risk", "Response": "Response", "END": END})
    for name in ("Business", "Policy", "Knowledge", "Risk", "Response"):
        g.add_edge(name, "Supervisor")
    return g.compile()


__all__ = ["InvestigationState", "SUPERVISOR_SYSTEM_PROMPT", "load_supervisor_prompt",
           "get_llm", "chat", "validate_state", "parse_decision", "supervisor_node",
           "mark_node_complete", "router", "build_graph", "VALID_NODES"]


# =========================================================================== #
# Offline self-test (stubs the LLM; no Ollama needed)
# =========================================================================== #
if __name__ == "__main__":
    import sys
    this = sys.modules[__name__]
    def _fake_chat(system, user):
        s = json.loads(user.split("\n", 1)[1])
        if not s["business_context"]:    d = {"next_node": "Business", "workflow_complete": False, "reason": "need business"}
        elif not s["policy_context"]:    d = {"next_node": "Policy", "workflow_complete": False, "reason": "need policy"}
        elif not s["knowledge_context"]: d = {"next_node": "Knowledge", "workflow_complete": False, "reason": "need history"}
        elif not s["risk_assessment"]:   d = {"next_node": "Risk", "workflow_complete": False, "reason": "assess risk"}
        elif not s["response_plan"]:      d = {"next_node": "Response", "workflow_complete": False, "reason": "plan"}
        else:                             d = {"next_node": "END", "workflow_complete": True, "reason": "done"}
        return "```json\n" + json.dumps(d) + "\n```"
    this.chat = _fake_chat  # patch the shared helper

    state: InvestigationState = {"incident": {"incident_id": "inc_demo"}}
    producer = {"Business": "business_context", "Policy": "policy_context",
                "Knowledge": "knowledge_context", "Risk": "risk_assessment", "Response": "response_plan"}
    for _ in range(10):
        state = supervisor_node(state)
        nxt = router(state)
        print("Supervisor ->", nxt)
        if state["workflow_complete"]:
            break
        state[producer[nxt]] = {"ok": True}
        state = mark_node_complete(state, nxt)
    print("completed_nodes:", state["completed_nodes"], "| complete:", state["workflow_complete"])
