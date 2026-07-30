"""Unit test for the Business Context Node's orchestration (DB lookup wired
into the LLM call), with the DB session pointed at the in-memory SQLite
fixture and the LLM call mocked.
"""
from __future__ import annotations

from contextlib import contextmanager

from graph.state import initial_state
from nodes.business.node import business_context_node
from schemas.business_context import AssetBusinessContext, BusinessContext


def test_business_context_node_returns_partial_state_update(mocker, sqlite_session, sample_incident):
    @contextmanager
    def fake_session_scope():
        yield sqlite_session

    mocker.patch("nodes.business.node.session_scope", fake_session_scope)

    expected = BusinessContext(
        affected_assets=[
            AssetBusinessContext(
                asset_id="LAPTOP-JSMITH01",
                hostname="LAPTOP-JSMITH01",
                asset_type="Workstation",
                application_name="Payroll System",
                department_name="Finance",
                owner_name="Sarah Chen",
                owner_email="sarah.chen@acme.com",
                business_criticality="HIGH",
                environment="production",
                data_sensitivity="restricted",
            )
        ],
        primary_department="Finance",
        primary_application="Payroll System",
        overall_business_criticality="HIGH",
        business_summary="jsmith's compromised laptop has access to the Payroll System.",
    )
    mocker.patch("nodes.business.node.invoke_structured", return_value=expected)

    result = business_context_node(initial_state(sample_incident))

    assert result["business_context"] == expected
    assert result["completed_nodes"] == ["business_context"]
    assert result["reasoning_log"][0]["node"] == "business_context"
