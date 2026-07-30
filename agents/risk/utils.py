"""Risk Node utilities: Pydantic models, LLM helper (single instance), JSON parsing,
and a deterministic grounded fallback assessment (never invents facts)."""
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
    """Default reasoning call (no tool calling; JSON mode)."""
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
class ImpactDimension(BaseModel):
    level: str
    reason: str


class RiskFactor(BaseModel):
    factor: str
    impact: str  # High | Medium | Low


class RiskAssessment(BaseModel):
    overall_risk: str
    priority: str
    urgency: str
    confidence: float
    risk_summary: str
    business_impact: ImpactDimension
    operational_impact: ImpactDimension
    data_exposure: ImpactDimension
    financial_impact: ImpactDimension
    compliance_impact: ImpactDimension
    reputation_impact: ImpactDimension
    lateral_movement: ImpactDimension
    recovery_complexity: ImpactDimension
    incident_severity: ImpactDimension
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    recommended_priority: str
    reasoning: list[str] = Field(default_factory=list)


class RiskNodeError(BaseModel):
    error: str
    detail: str


# --------------------------------------------------------------------------- #
# Deterministic grounded fallback (used only if the LLM is unavailable)
# --------------------------------------------------------------------------- #
_LEVEL = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
_PRIORITY = {"Critical": "P1", "High": "P2", "Medium": "P3", "Low": "P4"}
_URGENCY = {"Critical": "Immediate", "High": "High", "medium": "Medium", "Medium": "Medium", "Low": "Low"}
_ORDER = ["Low", "Medium", "High", "Critical"]


def _bump(level: str, by: int = 1) -> str:
    i = min(len(_ORDER) - 1, _ORDER.index(level) + by)
    return _ORDER[i]


def grounded_assessment(incident: dict, business: dict, policy: dict, knowledge: dict) -> RiskAssessment:
    business, policy, knowledge = business or {}, policy or {}, knowledge or {}
    crit = _LEVEL.get(str(business.get("criticality", "medium")).lower(), "Medium")
    sensitive = bool(business.get("contains_sensitive_data"))
    production = str(business.get("environment", "")).lower() == "production"
    approval = bool(policy.get("approval_required"))
    compliance = policy.get("compliance", []) or []
    standards = ", ".join(c.get("standard", c.get("compliance_id", "")) for c in compliance) if compliance else ""
    additions = knowledge.get("missing_aws_recommendations", []) or []
    dept = business.get("department", "the organization")
    asset = business.get("asset_name", incident.get("resource_arn", "the affected resource"))
    app = business.get("application_name", "the affected application")

    overall = crit
    if sensitive and production:
        overall = _bump(overall)  # sensitive prod data raises overall risk
    priority = _PRIORITY[overall]
    urgency = "Immediate" if overall == "Critical" else _URGENCY.get(overall, "Medium")

    present = sum(1 for x in (incident, business, policy, knowledge) if x)
    confidence = round(min(0.97, 0.6 + 0.09 * present), 2)

    data_level = "High" if sensitive else "Low"
    compliance_level = "High" if (sensitive or standards) else "Low"
    recovery_level = "High" if additions else ("Medium" if production else "Low")

    dims = {
        "business_impact": ImpactDimension(level=crit,
            reason=f"{asset} supports {app} for {dept} (criticality {crit})."),
        "operational_impact": ImpactDimension(level=("High" if production else "Medium"),
            reason=f"Incident affects a {business.get('environment','unknown')} environment; disruption to {app} is possible."),
        "data_exposure": ImpactDimension(level=data_level,
            reason=("Asset contains sensitive data." if sensitive else "No sensitive data recorded for this asset.")),
        "financial_impact": ImpactDimension(level=("High" if crit in ("Critical", "High") else "Medium"),
            reason=f"Disruption or breach of {app} carries financial exposure proportional to its {crit} criticality."),
        "compliance_impact": ImpactDimension(level=compliance_level,
            reason=(f"Regulated data / applicable standards: {standards or 'sensitive data present'}." if compliance_level == "High"
                    else "No specific compliance exposure identified.")),
        "reputation_impact": ImpactDimension(level=("High" if sensitive and production else "Medium"),
            reason="Compromise of sensitive production data could become externally reportable."),
        "lateral_movement": ImpactDimension(level=("High" if str(incident.get("attack_type","")).find("credential") >= 0 else "Medium"),
            reason="Credential-based compromise enables lateral movement across the estate." ),
        "recovery_complexity": ImpactDimension(level=recovery_level,
            reason=("Enterprise knowledge shows prior similar incidents required extra remediation steps."
                    if additions else "Standard remediation is expected to restore service.")),
        "incident_severity": ImpactDimension(level=_LEVEL.get(str(incident.get("severity","medium")).lower(), crit),
            reason=f"AWS-reported severity is {incident.get('severity','unknown')}."),
    }

    factors: list[RiskFactor] = []
    if crit in ("Critical", "High"):
        factors.append(RiskFactor(factor=f"{crit} {'production ' if production else ''}asset ({asset}) for {app}", impact="High"))
    if sensitive:
        factors.append(RiskFactor(factor="Asset stores sensitive data", impact="High"))
    if approval:
        factors.append(RiskFactor(factor=f"Policy requires {policy.get('approver','manager')} approval for containment", impact="Medium"))
    if standards:
        factors.append(RiskFactor(factor=f"{standards} compliance exposure", impact="High"))
    if additions:
        factors.append(RiskFactor(factor="Prior similar incident required additional remediation (per enterprise knowledge)", impact="Medium"))

    summary = (f"{overall} enterprise risk: {asset} ({app}, {dept}) is a {crit} "
               f"{business.get('environment','')} asset"
               f"{' holding sensitive data' if sensitive else ''}. "
               f"AWS severity {incident.get('severity','unknown')}"
               f"{'; regulated under ' + standards if standards else ''}"
               f"{'; enterprise history indicates elevated recovery complexity' if additions else ''}.")

    reasoning = [
        f"Business context: {asset} is {crit} for {dept} ({app}).",
        ("Sensitive data present -> elevated data-exposure and compliance impact."
         if sensitive else "No sensitive-data flag on this asset."),
        (f"Policy: containment requires {policy.get('approver','manager')} approval"
         + (f"; standards {standards}." if standards else ".") if approval or standards else "No blocking policy constraints identified."),
        ("Enterprise knowledge: similar past incident needed extra steps -> higher recovery complexity."
         if additions else "No prior-incident escalation signal from knowledge context."),
        f"Overall risk {overall} -> priority {priority}, urgency {urgency}, confidence {confidence}.",
    ]

    return RiskAssessment(overall_risk=overall, priority=priority, urgency=urgency, confidence=confidence,
                          risk_summary=summary, risk_factors=factors, recommended_priority=priority,
                          reasoning=reasoning, **dims)
