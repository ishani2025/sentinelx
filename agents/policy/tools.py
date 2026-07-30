"""Policy Node tools:
  1. PolicyRetrievalTool — filtered PostgreSQL retrieval (never SELECT *).
  2. PolicyReasoningTool — LLM interpretation grounded strictly on retrieved records."""
from __future__ import annotations
import json
from typing import Callable, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import Policy, ApprovalRule, Compliance, EscalationMatrix
from .schemas import PolicyContext, ApplicablePolicy, ComplianceRequirement, EscalationInfo
from .prompts import load_policy_prompt
from .logger import log
from .utils import default_llm_call, parse_json

class PolicyRetrievalTool:
    """Retrieves only records matching the incident context (targeted queries)."""
    def __init__(self, session_factory: Callable[[], Session]):
        self._sf = session_factory

    def get_policies(self, department, asset_type, criticality, action) -> list[Policy]:
        if not any([asset_type, department, criticality, action]): return []
        stmt = select(Policy)
        if asset_type: stmt = stmt.where(Policy.asset_type == asset_type)
        if department: stmt = stmt.where(Policy.department == department)
        if criticality: stmt = stmt.where(Policy.criticality == criticality)
        if action: stmt = stmt.where(Policy.action == action)
        with self._sf() as s: rows = list(s.scalars(stmt).all())
        log("policy_sql", table="policies", filters={"department":department,"asset_type":asset_type,
            "criticality":criticality,"action":action}, count=len(rows))
        return rows

    def get_approval_rules(self, department, criticality, action) -> list[ApprovalRule]:
        if not any([department, criticality, action]): return []
        stmt = select(ApprovalRule)
        if department: stmt = stmt.where(ApprovalRule.department == department)
        if criticality: stmt = stmt.where(ApprovalRule.criticality == criticality)
        if action: stmt = stmt.where(ApprovalRule.action == action)
        with self._sf() as s: rows = list(s.scalars(stmt).all())
        log("policy_sql", table="approval_rules", count=len(rows)); return rows

    def get_compliance(self, compliance_ids: list[str]) -> list[Compliance]:
        ids = [c for c in compliance_ids if c]
        if not ids: return []
        with self._sf() as s:
            rows = list(s.scalars(select(Compliance).where(Compliance.compliance_id.in_(ids))).all())
        log("policy_sql", table="compliance", count=len(rows)); return rows

    def get_escalation(self, department, severity) -> Optional[EscalationMatrix]:
        if not department: return None
        stmt = select(EscalationMatrix).where(EscalationMatrix.department == department)
        if severity: stmt = stmt.where(EscalationMatrix.severity == severity)
        with self._sf() as s: row = s.scalars(stmt).first()
        log("policy_sql", table="escalation_matrix", found=bool(row)); return row


class PolicyReasoningTool:
    """Interprets retrieved records into a validated PolicyContext. LLM is injected (DI)
    and reasons ONLY over supplied records. A grounded deterministic assembly (from the
    same records) is used if the LLM is unavailable — it never invents policies."""
    def __init__(self, llm_call: Callable[[str, str], str] = default_llm_call):
        self._llm = llm_call

    @staticmethod
    def _payload(policies, approval_rules, compliance, escalation) -> dict:
        return {
            "policies": [{"policy_id":p.policy_id,"policy_name":p.policy_name,"description":p.description,
                "action":p.action,"approval_required":p.approval_required,"compliance_id":p.compliance_id} for p in policies],
            "approval_rules": [{"approver":r.approver,"approval_level":r.approval_level,"action":r.action,
                "criticality":r.criticality,"department":r.department} for r in approval_rules],
            "compliance": [{"compliance_id":c.compliance_id,"standard":c.standard,"description":c.description,
                "requirements":c.requirements} for c in compliance],
            "escalation": ({"department":escalation.department,"severity":escalation.severity,
                "escalation_level":escalation.escalation_level,"notify_role":escalation.notify_role} if escalation else None)}

    def _grounded_assembly(self, payload: dict) -> PolicyContext:
        pols = [ApplicablePolicy(**{k:p[k] for k in
            ("policy_id","policy_name","description","action","approval_required","compliance_id")})
            for p in payload["policies"]]
        if not pols:
            return PolicyContext(applicable_policies=[], approval_required=False,
                reasoning="No enterprise policy matched this incident.")
        rule = payload["approval_rules"][0] if payload["approval_rules"] else None
        approval_required = any(p.approval_required for p in pols)
        esc = payload["escalation"]
        return PolicyContext(applicable_policies=pols, approval_required=approval_required,
            approver=(rule["approver"] if rule else None), approval_level=(rule["approval_level"] if rule else None),
            compliance=[ComplianceRequirement(**c) for c in payload["compliance"]],
            escalation_level=(EscalationInfo(**esc) if esc else None),
            organizational_constraints=[f"{p.policy_name}: {'approval required' if p.approval_required else 'auto-remediation permitted'}" for p in pols],
            reasoning=f"Grounded assembly from retrieved enterprise records ({len(pols)} policy(ies), approval_required={approval_required}).")

    def reason(self, policies, approval_rules, compliance, escalation) -> PolicyContext:
        payload = self._payload(policies, approval_rules, compliance, escalation)
        if not payload["policies"]:
            log("policy_no_match")
            return PolicyContext(applicable_policies=[], approval_required=False,
                reasoning="No enterprise policy matched this incident.")
        system = load_policy_prompt()
        user = "Retrieved enterprise records (reason ONLY over these):\n" + json.dumps(payload, indent=2)
        log("policy_llm_started", policies=len(payload["policies"]))
        try:
            data = parse_json(self._llm(system, user))
            if data:
                data["applicable_policies"] = payload["policies"]
                data["compliance"] = payload["compliance"]
                if payload["escalation"]: data["escalation_level"] = payload["escalation"]
                ctx = PolicyContext.model_validate(data)
                log("policy_llm_finished", approval_required=ctx.approval_required); return ctx
            log("policy_llm_unparseable")
        except Exception as ex:
            log("policy_llm_error", error=str(ex))
        return self._grounded_assembly(payload)
