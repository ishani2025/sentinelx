"""Output of the Policy Node: applicable organizational policies, required
approvals, compliance constraints, and escalation routing, retrieved from
PostgreSQL and interpreted (never invented) by the LLM.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ApplicablePolicy(BaseModel):
    policy_id: str
    name: str
    category: str
    description: str
    why_applicable: str


class RequiredApproval(BaseModel):
    action_type: str
    approver_role: str
    reason: str


class ComplianceConstraint(BaseModel):
    framework: str = Field(..., description="e.g. PCI-DSS, HIPAA, SOC2, GDPR")
    requirement: str
    why_applicable: str


class EscalationRoute(BaseModel):
    escalate_to_role: str
    escalate_to_contact: str
    sla_minutes: int


class PolicyContext(BaseModel):
    applicable_policies: list[ApplicablePolicy] = Field(default_factory=list)
    required_approvals: list[RequiredApproval] = Field(default_factory=list)
    compliance_constraints: list[ComplianceConstraint] = Field(default_factory=list)
    escalation: EscalationRoute | None = None
    policy_summary: str
