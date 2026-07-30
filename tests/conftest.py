"""Shared pytest fixtures.

Node-level tests avoid requiring a live Postgres/Ollama/FAISS by (a) running
the SQLAlchemy models against an in-memory SQLite database seeded with a
small, internally-consistent dataset mirroring `database/seed.py`, and (b)
mocking `models.llm.invoke_structured` where LLM output is needed.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Application, ApprovalRule, Asset, Base, Department, Owner, Policy
from schemas.incident import AffectedResource, Incident, MitreTechnique, TimelineEvent


@pytest.fixture()
def sample_incident() -> Incident:
    """The jsmith credential-compromise + impossible-travel story used
    throughout `demo/sample_logs/`.
    """
    return Incident(
        incident_id="INC-2026-0730-001",
        title="Credential compromise and anomalous login for jsmith@acme.com",
        description=(
            "GuardDuty Investigation correlated an EDR-detected infostealer on "
            "LAPTOP-JSMITH01 with a high-risk Okta login for jsmith@acme.com "
            "from an anonymizing hosting provider in an implausible location "
            "shortly after."
        ),
        source="AWS Security Hub",
        severity="HIGH",
        confidence_score=87.5,
        account_id="111111111111",
        region="us-east-1",
        mitre_techniques=[
            MitreTechnique(technique_id="T1555.003", tactic="Credential Access", name="Credentials from Web Browsers"),
            MitreTechnique(technique_id="T1078", tactic="Initial Access", name="Valid Accounts"),
        ],
        attack_timeline=[
            TimelineEvent(
                timestamp=datetime(2026, 7, 30, 9, 0, 12, tzinfo=timezone.utc),
                description="Infostealer accessed browser credential store on LAPTOP-JSMITH01",
                event_type="credential_theft",
            ),
            TimelineEvent(
                timestamp=datetime(2026, 7, 30, 9, 12, 44, tzinfo=timezone.utc),
                description="High-risk Okta login for jsmith@acme.com from Moscow, Russia",
                event_type="anomalous_login",
            ),
        ],
        affected_resources=[
            AffectedResource(
                resource_id="LAPTOP-JSMITH01",
                resource_type="Workstation",
                hostname="LAPTOP-JSMITH01",
                ip_address="10.4.12.55",
                account_id="111111111111",
            )
        ],
        aws_recommended_remediation=[
            "Revoke active sessions for jsmith@acme.com",
            "Isolate host LAPTOP-JSMITH01",
        ],
        detected_at=datetime(2026, 7, 30, 9, 12, 44, tzinfo=timezone.utc),
    )


@pytest.fixture()
def sqlite_session() -> Session:
    """An in-memory SQLite session with the SentinelX schema and a small,
    internally-consistent seed (Finance dept -> Payroll app -> Sarah Chen ->
    LAPTOP-JSMITH01, mirroring `database/seed.py`).
    """
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    finance = Department(name="Finance", head_name="Sarah Chen", cost_center="CC-100")
    session.add(finance)
    session.flush()

    sarah = Owner(name="Sarah Chen", email="sarah.chen@acme.com", role="CFO", department=finance)
    session.add(sarah)
    session.flush()

    payroll = Application(
        name="Payroll System",
        description="Processes employee payroll.",
        department=finance,
        owner=sarah,
        business_criticality="CRITICAL",
        environment="production",
        data_sensitivity="restricted",
    )
    session.add(payroll)
    session.flush()

    session.add(
        Asset(
            asset_identifier="LAPTOP-JSMITH01",
            hostname="LAPTOP-JSMITH01",
            ip_address="10.4.12.55",
            asset_type="Workstation",
            account_id="111111111111",
            environment="production",
            department=finance,
            application=payroll,
            business_criticality_override="HIGH",
        )
    )

    credential_policy = Policy(
        policy_code="POL-001",
        name="Credential Compromise Response Policy",
        category="Identity & Access",
        description="Confirmed credential compromise for HIGH+ criticality assets requires immediate containment.",
        applies_to_criticality="HIGH",
    )
    session.add(credential_policy)
    session.flush()
    session.add(
        ApprovalRule(
            policy=credential_policy,
            action_type="Force password reset / revoke sessions for a finance account",
            required_approver_role="CISO",
            criticality_threshold="HIGH",
            environment=None,
        )
    )

    session.commit()
    yield session
    session.close()
    engine.dispose()
