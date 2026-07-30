"""Validation tests for the core Pydantic schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.incident import Incident
from schemas.response_plan import ResponseAction, ResponsePlan
from schemas.risk_assessment import RiskAssessment


def test_sample_incident_is_valid(sample_incident):
    assert sample_incident.severity.value == "HIGH"
    assert sample_incident.mitre_techniques[0].technique_id == "T1555.003"


def test_incident_rejects_invalid_severity(sample_incident):
    payload = sample_incident.model_dump()
    payload["severity"] = "SUPER_CRITICAL"
    with pytest.raises(ValidationError):
        Incident.model_validate(payload)


def test_incident_rejects_out_of_range_confidence(sample_incident):
    payload = sample_incident.model_dump()
    payload["confidence_score"] = 150
    with pytest.raises(ValidationError):
        Incident.model_validate(payload)


def test_risk_assessment_confidence_bounds():
    with pytest.raises(ValidationError):
        RiskAssessment(
            business_impact="HIGH",
            priority="P1",
            severity="HIGH",
            confidence=101,
            affected_business_units=["Finance"],
            reasoning="test",
        )


def test_response_plan_action_sequence_must_be_positive():
    with pytest.raises(ValidationError):
        ResponseAction(
            sequence=0,
            action="Isolate host",
            reason="Contain threat",
            priority="IMMEDIATE",
            requires_human_approval=True,
            justification="POL-004",
        )


def test_response_plan_roundtrip():
    plan = ResponsePlan(
        actions=[
            ResponseAction(
                sequence=1,
                action="Isolate LAPTOP-JSMITH01",
                reason="Active credential theft",
                priority="IMMEDIATE",
                requires_human_approval=False,
                justification="POL-004 allows on-call isolation without approval",
            )
        ],
        plan_summary="Contain and rotate credentials.",
        overall_requires_approval=True,
    )
    dumped = plan.model_dump_json()
    assert ResponsePlan.model_validate_json(dumped) == plan
