"""API contract tests for `POST /investigate`, with the graph itself mocked
out so these run without a live Postgres/Ollama/FAISS stack.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from graph.state import initial_state
from models.llm import LLMOutputError
from schemas.business_context import AssetBusinessContext, BusinessContext
from schemas.knowledge_context import KnowledgeContext
from schemas.policy_context import PolicyContext
from schemas.response_plan import ResponseAction, ResponsePlan
from schemas.risk_assessment import RiskAssessment

client = TestClient(app)


def _completed_state(sample_incident):
    state = initial_state(sample_incident)
    state["business_context"] = BusinessContext(
        affected_assets=[
            AssetBusinessContext(
                asset_id="LAPTOP-JSMITH01",
                asset_type="Workstation",
                business_criticality="HIGH",
                environment="production",
                data_sensitivity="restricted",
            )
        ],
        overall_business_criticality="HIGH",
        business_summary="summary",
    )
    state["policy_context"] = PolicyContext(policy_summary="summary")
    state["knowledge_context"] = KnowledgeContext(knowledge_summary="summary")
    state["risk_assessment"] = RiskAssessment(
        business_impact="HIGH", priority="P1", severity="HIGH", confidence=90, reasoning="summary"
    )
    state["response_plan"] = ResponsePlan(
        actions=[
            ResponseAction(
                sequence=1,
                action="Isolate LAPTOP-JSMITH01",
                reason="Active credential theft",
                priority="IMMEDIATE",
                requires_human_approval=False,
                justification="POL-004",
            )
        ],
        plan_summary="Contain and rotate credentials.",
        overall_requires_approval=True,
    )
    state["completed_nodes"] = ["business_context", "policy", "knowledge", "risk_assessment", "response_planning"]
    state["current_node"] = "END"
    state["workflow_complete"] = True
    return state


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_investigate_returns_completed_state(mocker, sample_incident):
    mocker.patch("api.main.run_investigation", return_value=_completed_state(sample_incident))

    response = client.post("/investigate", json=sample_incident.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["workflow_complete"] is True
    assert body["response_plan"]["actions"][0]["action"] == "Isolate LAPTOP-JSMITH01"


def test_investigate_returns_502_on_llm_failure(mocker, sample_incident):
    mocker.patch("api.main.run_investigation", side_effect=LLMOutputError("ollama unreachable"))

    response = client.post("/investigate", json=sample_incident.model_dump(mode="json"))

    assert response.status_code == 502


def test_investigate_rejects_malformed_incident():
    response = client.post("/investigate", json={"title": "missing required fields"})
    assert response.status_code == 422
