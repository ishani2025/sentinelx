"""Seeds PostgreSQL with a realistic, internally-consistent enterprise for
"Acme Corp" — the same fictional org used by SentinelX's demo incident data
(see `demo/sample_logs/`, where user `jsmith` / Jane Smith's laptop is
credential-compromised and her Okta account then logs in from an anomalous
location).

Run as a script:
    python -m database.seed
"""
from __future__ import annotations

from database.models import (
    Application,
    ApprovalRule,
    Asset,
    ComplianceRequirement,
    Department,
    EscalationRule,
    Owner,
    Policy,
)
from database.postgres import reset_db, session_scope
from utils.logging import get_logger

logger = get_logger(__name__)


def seed_all() -> None:
    """Drops, recreates, and repopulates every table with mock enterprise data."""
    reset_db()

    with session_scope() as db:
        # --- Departments ---------------------------------------------------
        finance = Department(name="Finance", head_name="Sarah Chen", cost_center="CC-100")
        engineering = Department(name="Engineering", head_name="Marcus Alvarez", cost_center="CC-200")
        hr = Department(name="Human Resources", head_name="Priya Natarajan", cost_center="CC-300")
        security = Department(name="IT & Security", head_name="David Kim", cost_center="CC-400")
        db.add_all([finance, engineering, hr, security])
        db.flush()

        # --- Owners ----------------------------------------------------------
        sarah = Owner(name="Sarah Chen", email="sarah.chen@acme.com", role="CFO", department=finance)
        marcus = Owner(name="Marcus Alvarez", email="marcus.alvarez@acme.com", role="VP Engineering", department=engineering)
        priya = Owner(name="Priya Natarajan", email="priya.natarajan@acme.com", role="HR Director", department=hr)
        david = Owner(name="David Kim", email="david.kim@acme.com", role="CISO", department=security)
        db.add_all([sarah, marcus, priya, david])
        db.flush()

        # --- Applications ------------------------------------------------------
        payroll = Application(
            name="Payroll System",
            description="Processes employee payroll, tax withholding, and direct deposit for all Acme Corp staff.",
            department=finance,
            owner=sarah,
            business_criticality="CRITICAL",
            environment="production",
            data_sensitivity="restricted",
        )
        hris = Application(
            name="HR Information System",
            description="Stores employee PII, benefits enrollment, and performance records.",
            department=hr,
            owner=priya,
            business_criticality="HIGH",
            environment="production",
            data_sensitivity="restricted",
        )
        customer_portal = Application(
            name="Customer Portal",
            description="Customer-facing web application for account management and billing.",
            department=engineering,
            owner=marcus,
            business_criticality="HIGH",
            environment="production",
            data_sensitivity="confidential",
        )
        internal_wiki = Application(
            name="Internal Wiki",
            description="Internal engineering documentation and runbooks.",
            department=engineering,
            owner=marcus,
            business_criticality="LOW",
            environment="production",
            data_sensitivity="internal",
        )
        ci_pipeline = Application(
            name="CI/CD Pipeline",
            description="Build and deployment pipeline for engineering services.",
            department=engineering,
            owner=marcus,
            business_criticality="MEDIUM",
            environment="staging",
            data_sensitivity="internal",
        )
        db.add_all([payroll, hris, customer_portal, internal_wiki, ci_pipeline])
        db.flush()

        # --- Assets --------------------------------------------------------
        # Jane Smith (jsmith) is a Senior Financial Analyst in Finance with
        # payroll access from her corporate laptop — this is the asset
        # compromised in the demo incident story.
        db.add_all(
            [
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
                ),
                Asset(
                    asset_identifier="i-0a1b2c3d4payroll01",
                    hostname="payroll-app-01",
                    ip_address="10.0.1.20",
                    asset_type="AWS::EC2::Instance",
                    account_id="111111111111",
                    environment="production",
                    department=finance,
                    application=payroll,
                ),
                Asset(
                    asset_identifier="payroll-db-01",
                    hostname="payroll-db-01",
                    ip_address="10.0.1.10",
                    asset_type="AWS::RDS::DBInstance",
                    account_id="111111111111",
                    environment="production",
                    department=finance,
                    application=payroll,
                ),
                Asset(
                    asset_identifier="hris-db-01",
                    hostname="hris-db-01",
                    ip_address="10.0.2.10",
                    asset_type="AWS::RDS::DBInstance",
                    account_id="222222222222",
                    environment="production",
                    department=hr,
                    application=hris,
                ),
                Asset(
                    asset_identifier="i-0f1e2d3c4portal01",
                    hostname="portal-web-01",
                    ip_address="10.0.3.10",
                    asset_type="AWS::EC2::Instance",
                    account_id="333333333333",
                    environment="production",
                    department=engineering,
                    application=customer_portal,
                ),
                Asset(
                    asset_identifier="i-0f1e2d3c4portal02",
                    hostname="portal-web-02",
                    ip_address="10.0.3.11",
                    asset_type="AWS::EC2::Instance",
                    account_id="333333333333",
                    environment="production",
                    department=engineering,
                    application=customer_portal,
                ),
                Asset(
                    asset_identifier="wiki-01",
                    hostname="wiki-01",
                    ip_address="10.0.4.10",
                    asset_type="AWS::EC2::Instance",
                    account_id="333333333333",
                    environment="production",
                    department=engineering,
                    application=internal_wiki,
                ),
                Asset(
                    asset_identifier="ci-runner-01",
                    hostname="ci-runner-01",
                    ip_address="10.0.5.10",
                    asset_type="AWS::EC2::Instance",
                    account_id="333333333333",
                    environment="staging",
                    department=engineering,
                    application=ci_pipeline,
                ),
                Asset(
                    asset_identifier="DC02",
                    hostname="DC02",
                    ip_address="10.4.14.0",
                    asset_type="Domain Controller",
                    account_id="111111111111",
                    environment="production",
                    department=security,
                    business_criticality_override="CRITICAL",
                ),
            ]
        )

        # --- Policies -------------------------------------------------------
        credential_policy = Policy(
            policy_code="POL-001",
            name="Credential Compromise Response Policy",
            category="Identity & Access",
            description="Any confirmed or suspected credential compromise for an account with access to a "
            "CRITICAL or HIGH criticality application requires immediate session revocation and password reset.",
            applies_to_criticality="HIGH",
        )
        prod_change_policy = Policy(
            policy_code="POL-002",
            name="Production Change Control Policy",
            category="Change Management",
            description="Any containment or remediation action taken against a production asset must be "
            "logged and approved per the escalation matrix before execution.",
            applies_to_environment="production",
        )
        data_protection_policy = Policy(
            policy_code="POL-003",
            name="Restricted Data Protection Policy",
            category="Data Protection",
            description="Assets classified as 'restricted' data sensitivity (PII, payroll, financial records) "
            "require Finance or Legal sign-off before any action that could affect availability.",
            applies_to_criticality="CRITICAL",
        )
        endpoint_isolation_policy = Policy(
            policy_code="POL-004",
            name="Endpoint Isolation Policy",
            category="Incident Response",
            description="Endpoints showing indicators of credential theft or malware execution may be "
            "network-isolated by the on-call security engineer without prior approval.",
        )
        db.add_all([credential_policy, prod_change_policy, data_protection_policy, endpoint_isolation_policy])
        db.flush()

        # --- Approval rules ---------------------------------------------------
        db.add_all(
            [
                ApprovalRule(
                    policy=data_protection_policy,
                    action_type="Disable/restart production database or payroll processing",
                    required_approver_role="CFO",
                    criticality_threshold="CRITICAL",
                    environment="production",
                ),
                ApprovalRule(
                    policy=prod_change_policy,
                    action_type="Isolate or terminate a production server/instance",
                    required_approver_role="VP Engineering",
                    criticality_threshold="HIGH",
                    environment="production",
                ),
                ApprovalRule(
                    policy=credential_policy,
                    action_type="Force password reset / revoke sessions for an executive or finance account",
                    required_approver_role="CISO",
                    criticality_threshold="HIGH",
                    environment=None,
                ),
                ApprovalRule(
                    policy=endpoint_isolation_policy,
                    action_type="Isolate a single end-user workstation",
                    required_approver_role="Security On-Call Engineer",
                    criticality_threshold="LOW",
                    environment=None,
                ),
            ]
        )

        # --- Compliance requirements -----------------------------------------
        db.add_all(
            [
                ComplianceRequirement(
                    framework="SOX",
                    requirement="Any incident affecting financial reporting systems (Payroll, GL) must be "
                    "documented with a full audit trail and reported to the Audit Committee within 24 hours.",
                    applies_to_data_sensitivity="restricted",
                    department=finance,
                ),
                ComplianceRequirement(
                    framework="GDPR",
                    requirement="Any suspected exposure of employee PII (HR Information System) must be "
                    "assessed for breach-notification obligations within 72 hours.",
                    applies_to_data_sensitivity="restricted",
                    department=hr,
                ),
                ComplianceRequirement(
                    framework="SOC2",
                    requirement="Access control changes on production customer-facing systems must be logged "
                    "and available for the next SOC2 audit cycle.",
                    applies_to_data_sensitivity="confidential",
                    department=engineering,
                ),
                ComplianceRequirement(
                    framework="PCI-DSS",
                    requirement="If cardholder data environments are in scope, restrict and log all "
                    "administrative access during and after the incident.",
                    applies_to_data_sensitivity="restricted",
                    department=None,
                ),
            ]
        )

        # --- Escalation matrix -------------------------------------------------
        db.add_all(
            [
                EscalationRule(
                    severity="CRITICAL", criticality="CRITICAL",
                    escalate_to_role="CISO", escalate_to_contact="david.kim@acme.com", sla_minutes=15,
                ),
                EscalationRule(
                    severity="HIGH", criticality="CRITICAL",
                    escalate_to_role="CISO", escalate_to_contact="david.kim@acme.com", sla_minutes=30,
                ),
                EscalationRule(
                    severity="HIGH", criticality="HIGH",
                    escalate_to_role="Security Manager", escalate_to_contact="secops-lead@acme.com", sla_minutes=60,
                ),
                EscalationRule(
                    severity="MEDIUM", criticality="HIGH",
                    escalate_to_role="Security Manager", escalate_to_contact="secops-lead@acme.com", sla_minutes=120,
                ),
                EscalationRule(
                    severity="LOW", criticality="MEDIUM",
                    escalate_to_role="Security On-Call Engineer", escalate_to_contact="secops-oncall@acme.com", sla_minutes=240,
                ),
            ]
        )

    logger.info("database_seeded", departments=4, applications=5, assets=9, policies=4)


if __name__ == "__main__":
    seed_all()
    print("SentinelX enterprise mock data seeded successfully.")
