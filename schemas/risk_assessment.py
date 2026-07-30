"""Output of the Risk Assessment Node: enterprise risk estimated purely from
already-collected state (incident + business + policy + knowledge). This
node never retrieves new data and never proposes remediation.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.enums import Priority, Severity


class RiskAssessment(BaseModel):
    business_impact: Severity
    priority: Priority
    severity: Severity
    confidence: float = Field(..., ge=0, le=100)
    affected_business_units: list[str] = Field(default_factory=list)
    reasoning: str
