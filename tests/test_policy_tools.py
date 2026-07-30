"""Integration tests for the Policy Node's SQL retrieval tool, run against
an in-memory SQLite database (see `tests/conftest.py`).
"""
from __future__ import annotations

from nodes.policy.tools import fetch_policy_records
from schemas.business_context import AssetBusinessContext, BusinessContext


def _business_context() -> BusinessContext:
    return BusinessContext(
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
        business_summary="jsmith's laptop has access to the Payroll System.",
    )


def test_fetch_policy_records_matches_credential_policy(sqlite_session, sample_incident):
    records = fetch_policy_records(sqlite_session, sample_incident, _business_context())

    policy_codes = {p["policy_id"] for p in records["applicable_policies"]}
    assert "POL-001" in policy_codes

    approver_roles = {r["required_approver_role"] for r in records["approval_rules"]}
    assert "CISO" in approver_roles


def test_fetch_policy_records_excludes_policies_below_criticality_threshold(sqlite_session, sample_incident):
    low_criticality_context = _business_context().model_copy(
        update={"overall_business_criticality": "LOW"},
        deep=True,
    )
    low_criticality_context.affected_assets[0].business_criticality = "LOW"

    records = fetch_policy_records(sqlite_session, sample_incident, low_criticality_context)

    policy_codes = {p["policy_id"] for p in records["applicable_policies"]}
    assert "POL-001" not in policy_codes
