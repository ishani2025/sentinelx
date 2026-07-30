"""The investigation report handed to SentinelX by AWS Security Hub /
GuardDuty Investigation Agent. This is SentinelX's entry point: detection,
MITRE mapping, attack timeline, and confidence scoring have already been
done upstream by AWS. SentinelX never re-derives these fields.
"""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from schemas.enums import Severity


class MitreTechnique(BaseModel):
    technique_id: str = Field(..., description="e.g. T1078")
    tactic: str = Field(..., description="e.g. Initial Access")
    name: str


class TimelineEvent(BaseModel):
    timestamp: datetime
    description: str
    event_type: str


class AffectedResource(BaseModel):
    resource_id: str
    resource_type: str = Field(..., description="e.g. AWS::EC2::Instance, Okta::User")
    resource_arn: str | None = None
    hostname: str | None = None
    ip_address: str | None = None
    account_id: str | None = None


class Incident(BaseModel):
    """AWS investigation report — the sole input to the graph."""

    incident_id: str
    title: str
    description: str
    source: str = Field(default="AWS Security Hub", description="e.g. AWS Security Hub, GuardDuty Investigation")
    severity: Severity
    confidence_score: float = Field(..., ge=0, le=100, description="AWS-provided confidence, 0-100")
    account_id: str
    region: str
    mitre_techniques: list[MitreTechnique] = Field(default_factory=list)
    attack_timeline: list[TimelineEvent] = Field(default_factory=list)
    affected_resources: list[AffectedResource] = Field(default_factory=list)
    aws_recommended_remediation: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
