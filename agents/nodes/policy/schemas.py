"""Pydantic v2 output models for the Policy Node."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class ApplicablePolicy(BaseModel):
    policy_id: str
    policy_name: str
    description: str
    action: str
    approval_required: bool
    compliance_id: Optional[str] = None


class ComplianceRequirement(BaseModel):
    compliance_id: str
    standard: str
    description: str
    requirements: str


class EscalationInfo(BaseModel):
    department: str
    severity: str
    escalation_level: str
    notify_role: str


class PolicyContext(BaseModel):
    """Validated output written to InvestigationState.policy_context."""
    applicable_policies: list[ApplicablePolicy] = Field(default_factory=list)
    approval_required: bool = False
    approver: Optional[str] = None
    approval_level: Optional[int] = None
    compliance: list[ComplianceRequirement] = Field(default_factory=list)
    escalation_level: Optional[EscalationInfo] = None
    organizational_constraints: list[str] = Field(default_factory=list)
    reasoning: str = ""


class PolicyNodeError(BaseModel):
    """Structured error returned when the node cannot complete (e.g. DB failure)."""
    error: str
    detail: str
