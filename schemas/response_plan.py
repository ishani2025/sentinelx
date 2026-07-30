"""Output of the Response Planning Node: an ordered, organization-aware
response plan. This node only plans — it never executes actions, calls the
AWS SDK, sends notifications, or verifies anything.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResponseAction(BaseModel):
    sequence: int = Field(..., ge=1)
    action: str
    reason: str
    priority: str = Field(..., description="e.g. IMMEDIATE, HIGH, MEDIUM, LOW")
    requires_human_approval: bool
    justification: str


class ResponsePlan(BaseModel):
    actions: list[ResponseAction] = Field(default_factory=list)
    plan_summary: str
    overall_requires_approval: bool
