"""Integration tests for the Business Context Node's SQL retrieval tool,
run against an in-memory SQLite database (see `tests/conftest.py`).
"""
from __future__ import annotations

from nodes.business.tools import fetch_business_records
from schemas.incident import AffectedResource


def test_fetch_business_records_matches_by_hostname(sqlite_session, sample_incident):
    records = fetch_business_records(sqlite_session, sample_incident.affected_resources)

    assert len(records) == 1
    record = records[0]
    assert record["found"] is True
    assert record["asset_id"] == "LAPTOP-JSMITH01"
    assert record["application_name"] == "Payroll System"
    assert record["department_name"] == "Finance"
    assert record["owner_name"] == "Sarah Chen"
    # Override on the asset (HIGH) takes precedence over the application's CRITICAL rating.
    assert record["business_criticality"] == "HIGH"


def test_fetch_business_records_reports_unmatched_resource(sqlite_session):
    unknown = [AffectedResource(resource_id="i-doesnotexist", resource_type="AWS::EC2::Instance")]
    records = fetch_business_records(sqlite_session, unknown)

    assert len(records) == 1
    assert records[0]["found"] is False
    assert records[0]["queried_resource_id"] == "i-doesnotexist"
