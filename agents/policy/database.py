"""PostgreSQL layer — SQLAlchemy 2.0 models, session factory, realistic seed data.
DATABASE_URL controls the backend (default PostgreSQL). Overridable for DI/testing."""
from __future__ import annotations
import os
from typing import Callable
from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql+psycopg://sentinelx:sentinelx@localhost:5432/sentinelx")

class Base(DeclarativeBase): pass

class Compliance(Base):
    __tablename__ = "compliance"
    compliance_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    standard: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text)

class Policy(Base):
    __tablename__ = "policies"
    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text)
    asset_type: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(64), index=True)
    criticality: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("compliance.compliance_id"), nullable=True)

class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    rule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department: Mapped[str] = mapped_column(String(64), index=True)
    criticality: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    approver: Mapped[str] = mapped_column(String(128))
    approval_level: Mapped[int] = mapped_column(Integer)

class EscalationMatrix(Base):
    __tablename__ = "escalation_matrix"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    escalation_level: Mapped[str] = mapped_column(String(32))
    notify_role: Mapped[str] = mapped_column(String(128))

def make_engine(url: str | None = None):
    return create_engine(url or DATABASE_URL, future=True, pool_pre_ping=True)

def make_session_factory(url: str | None = None) -> Callable[[], Session]:
    engine = make_engine(url); Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)

_COMPLIANCE = [
    Compliance(compliance_id="PCI-DSS", standard="PCI-DSS v4.0",
        description="Payment Card Industry Data Security Standard",
        requirements="Protect cardholder data; restrict access; MFA; log & monitor; rotate credentials."),
    Compliance(compliance_id="ISO-27001", standard="ISO/IEC 27001:2022",
        description="Information Security Management System",
        requirements="A.5.15 access control; A.5.17 authentication; A.8.15 logging; A.5.24 incident mgmt."),
    Compliance(compliance_id="GDPR", standard="EU GDPR", description="General Data Protection Regulation",
        requirements="Protect personal data; breach notification within 72 hours; DPO engagement."),
    Compliance(compliance_id="CIS-8", standard="CIS Controls v8", description="Center for Internet Security Controls",
        requirements="Control 3 data protection; Control 5/6 access & identity; Control 8 audit logs."),
    Compliance(compliance_id="SOC2", standard="SOC 2 Type II", description="Service Organization Control 2",
        requirements="CC6 logical access; CC7 detection & response; evidence retention."),
    Compliance(compliance_id="NIST-CSF", standard="NIST CSF 2.0", description="NIST Cybersecurity Framework",
        requirements="PR.AA access control; DE.CM monitoring; RS.MI mitigation; RC.RP recovery."),
]
_POLICIES = [
    Policy(policy_id="POL-FIN-IAM-001", policy_name="Finance IAM Credential Compromise",
        description="Compromised Finance IAM identities must be contained with mandatory approval.",
        asset_type="iam_user", department="Finance", criticality="critical",
        action="disable_access_key", approval_required=True, compliance_id="PCI-DSS"),
    Policy(policy_id="POL-FIN-IAM-002", policy_name="Finance Credential Rotation",
        description="Rotate credentials for compromised Finance identities under Security Manager approval.",
        asset_type="iam_user", department="Finance", criticality="critical",
        action="rotate_credentials", approval_required=True, compliance_id="SOC2"),
    Policy(policy_id="POL-DATA-S3-001", policy_name="PII S3 Bucket Protection",
        description="Buckets holding PII must be locked down; access revocation requires DPO approval.",
        asset_type="s3", department="Data", criticality="critical",
        action="revoke_access", approval_required=True, compliance_id="GDPR"),
    Policy(policy_id="POL-CLOUD-S3-002", policy_name="Public S3 Bucket Remediation",
        description="Non-sensitive public buckets are auto-remediated; notify Cloud team, no approval.",
        asset_type="s3", department="Cloud", criticality="medium",
        action="restrict_access", approval_required=False, compliance_id="CIS-8"),
    Policy(policy_id="POL-IT-EC2-001", policy_name="Production EC2 Containment",
        description="Terminating/isolating production EC2 requires CISO approval.",
        asset_type="ec2", department="IT", criticality="critical",
        action="terminate_instance", approval_required=True, compliance_id="ISO-27001"),
    Policy(policy_id="POL-IT-EC2-002", policy_name="EC2 Isolation",
        description="Network isolation of a suspected EC2 host requires Security Manager approval.",
        asset_type="ec2", department="IT", criticality="high",
        action="isolate_instance", approval_required=True, compliance_id="NIST-CSF"),
    Policy(policy_id="POL-IAM-ROOT-001", policy_name="Root Account Compromise",
        description="Root account compromise triggers org-wide lockdown with CISO+Exec approval.",
        asset_type="root_account", department="IT", criticality="critical",
        action="enforce_root_lockdown", approval_required=True, compliance_id="ISO-27001"),
    Policy(policy_id="POL-CLOUD-LAMBDA-001", policy_name="Lambda Secret Exposure",
        description="Rotate secrets on Lambda exposure; Cloud Security Lead approval.",
        asset_type="lambda", department="Cloud", criticality="high",
        action="rotate_secrets", approval_required=True, compliance_id="CIS-8"),
]
_APPROVAL_RULES = [
    ApprovalRule(department="Finance", criticality="critical", action="disable_access_key", approver="Security Manager", approval_level=2),
    ApprovalRule(department="Finance", criticality="critical", action="rotate_credentials", approver="Security Manager", approval_level=2),
    ApprovalRule(department="Data", criticality="critical", action="revoke_access", approver="Data Protection Officer", approval_level=3),
    ApprovalRule(department="Cloud", criticality="medium", action="restrict_access", approver="Cloud Team Lead", approval_level=1),
    ApprovalRule(department="IT", criticality="critical", action="terminate_instance", approver="CISO", approval_level=3),
    ApprovalRule(department="IT", criticality="high", action="isolate_instance", approver="Security Manager", approval_level=2),
    ApprovalRule(department="IT", criticality="critical", action="enforce_root_lockdown", approver="CISO", approval_level=3),
    ApprovalRule(department="Cloud", criticality="high", action="rotate_secrets", approver="Cloud Security Lead", approval_level=2),
]
_ESCALATION = [
    EscalationMatrix(department="Finance", severity="Sev1", escalation_level="L3", notify_role="CISO + Executive Management"),
    EscalationMatrix(department="Finance", severity="Sev2", escalation_level="L2", notify_role="Security Manager"),
    EscalationMatrix(department="Data", severity="Sev1", escalation_level="L3", notify_role="CISO + Legal/DPO"),
    EscalationMatrix(department="Data", severity="Sev2", escalation_level="L2", notify_role="Data Protection Officer"),
    EscalationMatrix(department="IT", severity="Sev1", escalation_level="L3", notify_role="CISO + Executive Management"),
    EscalationMatrix(department="IT", severity="Sev2", escalation_level="L2", notify_role="IR Lead / SOC Manager"),
    EscalationMatrix(department="Cloud", severity="Sev2", escalation_level="L2", notify_role="Cloud Team Lead"),
    EscalationMatrix(department="Cloud", severity="Sev3", escalation_level="L1", notify_role="Cloud Operations"),
]

def seed_if_empty(session_factory: Callable[[], Session]) -> None:
    with session_factory() as s:
        if s.scalar(select(Compliance).limit(1)) is not None: return
        s.add_all(_COMPLIANCE); s.flush()
        s.add_all(_POLICIES + _APPROVAL_RULES + _ESCALATION); s.commit()
