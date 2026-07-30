"""Response Planning utilities: Pydantic models, LLM helper (single instance), JSON parsing,
and a deterministic grounded planner (combines all contexts; never invents)."""
from __future__ import annotations
import json, os, re
from functools import lru_cache
from typing import Any, Optional
from pydantic import BaseModel, Field

_LLM_MODEL = os.getenv("SENTINELX_LLM_MODEL", "llama3.2")
_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@lru_cache(maxsize=1)
def _get_json_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature, format="json")


def default_llm_call(system_prompt: str, user_content: str) -> str:
    from langchain_core.messages import SystemMessage, HumanMessage
    resp = _get_json_llm().invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
    return resp.content if hasattr(resp, "content") else str(resp)


def parse_json(raw: str) -> Optional[dict[str, Any]]:
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


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class ResponseAction(BaseModel):
    step: int
    title: str
    description: str
    target: str
    priority: str
    requires_human_approval: bool
    dependency: Optional[str] = None
    expected_outcome: str
    justification: str


class ResponsePlan(BaseModel):
    overall_strategy: str
    priority: str
    estimated_urgency: str
    actions: list[ResponseAction] = Field(default_factory=list)
    reasoning: str = ""


class ResponseNodeError(BaseModel):
    error: str
    detail: str


# --------------------------------------------------------------------------- #
# Deterministic grounded planner (fallback; uses ONLY supplied state)
# --------------------------------------------------------------------------- #
_DESTRUCTIVE = ("terminate", "delete", "re-enable", "reenable", "restore", "wipe", "destroy")


def _classify(title: str) -> tuple[str, bool]:
    """Return (target_system, requires_human_approval) from the action title."""
    t = title.lower()
    if any(k in t for k in _DESTRUCTIVE):
        approval = True
    elif "approval" in t:
        approval = True
    else:
        approval = False
    if any(k in t for k in ("sts", "session", "token")):
        target = "AWS STS"
    elif any(k in t for k in ("access key", "iam", "credential", "disable")) and "sts" not in t:
        target = "IAM"
    elif any(k in t for k in ("ip", "block", "waf", "firewall")):
        target = "Network / WAF"
    elif any(k in t for k in ("ec2", "instance", "isolate", "host")):
        target = "EC2"
    elif "s3" in t or "bucket" in t:
        target = "S3"
    elif any(k in t for k in ("notify", "slack", "email", "team")):
        target = "Notification"
    elif any(k in t for k in ("ticket", "incident", "jira", "servicenow")):
        target = "Ticketing"
    elif "approval" in t:
        target = "Approval Workflow"
    else:
        target = "Enterprise"
    return target, approval


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def grounded_plan(incident: dict, business: dict, policy: dict,
                  knowledge: dict, risk: dict) -> ResponsePlan:
    business, policy, knowledge, risk = business or {}, policy or {}, knowledge or {}, risk or {}
    priority = risk.get("priority") or risk.get("recommended_priority") or "P2"
    urgency = risk.get("urgency") or ("Immediate" if priority == "P1" else "High")
    overall_risk = risk.get("overall_risk", "High")
    asset = business.get("asset_name", incident.get("resource_arn", "the affected resource"))
    crit = business.get("criticality", "unknown")
    attack = str(incident.get("attack_type", incident.get("attack", ""))).lower()
    approver = policy.get("approver", "Security Manager")
    approval_required = bool(policy.get("approval_required"))
    esc = (policy.get("escalation_level") or {})
    notify_role = esc.get("notify_role", "Security / Identity Team")
    aws_recs = (incident.get("aws_recommendations") or incident.get("recommendations") or [])
    additions = knowledge.get("missing_aws_recommendations", []) or []

    # ---- build ordered candidate steps (title, justification) ----
    candidates: list[tuple[str, str]] = []
    if "credential" in attack or "iam" in attack:
        candidates.append(("Disable compromised IAM user",
            f"{overall_risk} risk on {asset} ({crit}); immediately stop unauthorized access."))
    elif any(k in attack for k in ("ransom", "malware", "c2", "lateral")):
        candidates.append(("Isolate affected host",
            f"{overall_risk} risk; contain active threat on {asset} to prevent spread."))
    else:
        candidates.append(("Contain affected resource",
            f"{overall_risk} risk on {asset}; limit blast radius."))

    for step in additions:  # enterprise knowledge additions (grounded)
        candidates.append((step, "Enterprise knowledge / historical cases show this step is required."))
    for rec in aws_recs:    # AWS generic recs
        candidates.append((rec, "AWS investigation recommendation, retained in the enterprise plan."))

    candidates.append((f"Notify {notify_role}",
        f"Escalation policy requires notifying {notify_role} for a {priority} incident."))
    candidates.append(("Open security incident ticket",
        "Establish an auditable incident record and coordinate the response."))
    if approval_required:
        candidates.append((f"Request {approver} approval before re-enabling the account",
            f"Enterprise policy requires {approver} approval before restoring access."))

    # ---- de-duplicate, assemble actions ----
    actions: list[ResponseAction] = []
    seen: set[str] = set()
    for title, justification in candidates:
        n = _norm(title)
        if not n or n in seen:
            continue
        seen.add(n)
        target, approval = _classify(title)
        step_no = len(actions) + 1
        is_notify_or_ticket = target in ("Notification", "Ticketing")
        pr = ("Medium" if is_notify_or_ticket else
              ("High" if target == "Approval Workflow" else
               ("Critical" if overall_risk in ("Critical", "High") else "High")))
        dep = None if step_no == 1 else ("Step 1" if is_notify_or_ticket else f"Step {step_no - 1}")
        actions.append(ResponseAction(
            step=step_no, title=title,
            description=f"{title} on {target} as part of the enterprise response.",
            target=target, priority=pr, requires_human_approval=approval, dependency=dep,
            expected_outcome=("Restores access safely after review." if approval and "approval" in title.lower()
                              else "Reduces risk and progresses containment/eradication."),
            justification=justification))

    reasoning = (f"Plan derived by combining AWS recommendations ({len(aws_recs)}), enterprise knowledge "
                 f"additions ({len(additions)}), business criticality ({crit}), and the {overall_risk} risk "
                 f"assessment. Containment is prioritized; high-impact/irreversible actions and account "
                 f"re-enablement are gated on {approver} approval per policy.")
    return ResponsePlan(overall_strategy="Contain -> Eradicate -> Recover",
                        priority=priority, estimated_urgency=urgency, actions=actions, reasoning=reasoning)
