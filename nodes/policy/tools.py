"""SQL retrieval tool for the Policy Node.

Given the business context already gathered, deterministically filters
Policy / ApprovalRule / ComplianceRequirement / EscalationRule rows down to
the ones that actually apply, so the LLM only ever summarizes/formats
records it was handed rather than deciding applicability itself.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import ApprovalRule, ComplianceRequirement, Department, EscalationRule, Policy
from schemas.business_context import BusinessContext
from schemas.enums import severity_rank
from schemas.incident import Incident


def fetch_policy_records(db: Session, incident: Incident, business_context: BusinessContext) -> dict:
    asset_environments = {asset.environment.value for asset in business_context.affected_assets}
    asset_sensitivities = {asset.data_sensitivity.value for asset in business_context.affected_assets}
    max_criticality_rank = severity_rank(business_context.overall_business_criticality.value)

    policies: list[Policy] = list(db.execute(select(Policy)).scalars())
    applicable_policies = [
        policy
        for policy in policies
        if (policy.applies_to_environment is None or policy.applies_to_environment in asset_environments)
        and (policy.applies_to_criticality is None or max_criticality_rank >= severity_rank(policy.applies_to_criticality))
    ]
    applicable_policy_ids = {policy.id for policy in applicable_policies}

    approval_rules: list[ApprovalRule] = list(db.execute(select(ApprovalRule)).scalars())
    applicable_approval_rules = [
        rule
        for rule in approval_rules
        if rule.policy_id in applicable_policy_ids
        and max_criticality_rank >= severity_rank(rule.criticality_threshold)
        and (rule.environment is None or rule.environment in asset_environments)
    ]

    department_ids = {
        db.execute(select(Department.id).where(Department.name == asset.department_name)).scalar()
        for asset in business_context.affected_assets
        if asset.department_name
    }
    compliance_requirements: list[ComplianceRequirement] = list(db.execute(select(ComplianceRequirement)).scalars())
    applicable_compliance = [
        req
        for req in compliance_requirements
        if (req.applies_to_data_sensitivity is None or req.applies_to_data_sensitivity in asset_sensitivities)
        or (req.applies_to_department_id is not None and req.applies_to_department_id in department_ids)
    ]

    escalation_rules: list[EscalationRule] = list(db.execute(select(EscalationRule)).scalars())
    matching_escalations = [
        rule
        for rule in escalation_rules
        if rule.severity == incident.severity.value
        and severity_rank(rule.criticality) <= max_criticality_rank
    ]
    # Prefer the rule whose criticality most closely matches the asset criticality
    # (tightest applicable SLA), falling back to the shortest SLA available.
    best_escalation = min(matching_escalations, key=lambda r: r.sla_minutes, default=None)

    return {
        "applicable_policies": [
            {"policy_id": p.policy_code, "name": p.name, "category": p.category, "description": p.description}
            for p in applicable_policies
        ],
        "approval_rules": [
            {
                "action_type": r.action_type,
                "required_approver_role": r.required_approver_role,
                "criticality_threshold": r.criticality_threshold,
            }
            for r in applicable_approval_rules
        ],
        "compliance_requirements": [
            {"framework": c.framework, "requirement": c.requirement} for c in applicable_compliance
        ],
        "escalation": (
            {
                "escalate_to_role": best_escalation.escalate_to_role,
                "escalate_to_contact": best_escalation.escalate_to_contact,
                "sla_minutes": best_escalation.sla_minutes,
            }
            if best_escalation
            else None
        ),
    }
