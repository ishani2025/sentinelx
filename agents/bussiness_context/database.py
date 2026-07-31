"""PostgreSQL engine/session factory + realistic, internally-consistent seed data.

Seed departments (Finance, Sales, Data Science, IT), data classifications, and criticality
tiers align with the roles and data-classification scheme defined in
docs/governance/SentinelX_Security_Policy.md so downstream Policy/Risk nodes stay consistent.
"""
from __future__ import annotations
import os
from typing import Callable
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Department, Owner, BusinessUnit, Application, Asset

DATABASE_URL = os.getenv("BUSINESS_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+psycopg://sentinelx:sentinelx@localhost:5432/sentinelx"))

def make_engine(url: str | None = None):
    return create_engine(url or DATABASE_URL, future=True, pool_pre_ping=True)

def make_session_factory(url: str | None = None) -> Callable[[], Session]:
    engine = make_engine(url); Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)

_DEPARTMENTS = [
    Department(department_id="DEP-FIN", department_name="Finance", manager="Carol Danvers", email="finance-mgr@acme.com"),
    Department(department_id="DEP-SALES", department_name="Sales", manager="Frank Castle", email="sales-mgr@acme.com"),
    Department(department_id="DEP-DS", department_name="Data Science", manager="Grace Hopper", email="ds-mgr@acme.com"),
    Department(department_id="DEP-IT", department_name="IT", manager="Henry Pym", email="it-mgr@acme.com"),
]
_OWNERS = [
    Owner(owner_id="OWN-ALICE", owner_name="Alice Johnson", email="alice.johnson@acme.com", phone="+1-555-0101", team="Payroll Engineering"),
    Owner(owner_id="OWN-BOB", owner_name="Bob Smith", email="bob.smith@acme.com", phone="+1-555-0102", team="Portal Engineering"),
    Owner(owner_id="OWN-CHARLIE", owner_name="Charlie Diaz", email="charlie.diaz@acme.com", phone="+1-555-0103", team="Analytics"),
]
_BUSINESS_UNITS = [
    BusinessUnit(business_unit="Corporate Finance", description="Financial systems and payroll", risk_level="high"),
    BusinessUnit(business_unit="Revenue", description="Customer-facing sales systems", risk_level="high"),
    BusinessUnit(business_unit="R&D", description="Research and analytics", risk_level="medium"),
]
_APPLICATIONS = [
    Application(application_id="APP-PAYROLL", application_name="Payroll", description="Processes employee salaries and tax withholding.", business_priority="Highest", sla="99.99%", department_id="DEP-FIN"),
    Application(application_id="APP-PORTAL", application_name="Customer Portal", description="Public customer self-service portal.", business_priority="Critical", sla="99.9%", department_id="DEP-SALES"),
    Application(application_id="APP-ANALYTICS", application_name="Analytics", description="Internal analytics and reporting.", business_priority="Medium", sla="99.0%", department_id="DEP-DS"),
]
_ASSETS = [
    Asset(asset_id="AST-PAY-EC2", asset_name="Payroll Server", aws_resource_id="i-0payroll123456789",
          asset_type="ec2", application_id="APP-PAYROLL", owner_id="OWN-ALICE", department_id="DEP-FIN",
          business_unit="Corporate Finance", environment="production", criticality="critical",
          contains_sensitive_data=True, business_function="Payroll processing (salary & tax data)"),
    Asset(asset_id="AST-PAY-IAM", asset_name="Payroll IAM User", aws_resource_id="jsmith",
          asset_type="iam_user", application_id="APP-PAYROLL", owner_id="OWN-ALICE", department_id="DEP-FIN",
          business_unit="Corporate Finance", environment="production", criticality="critical",
          contains_sensitive_data=True, business_function="Payroll service account identity"),
    Asset(asset_id="AST-PAY-S3", asset_name="Customer PII Bucket", aws_resource_id="acme-customer-pii",
          asset_type="s3", application_id="APP-PAYROLL", owner_id="OWN-ALICE", department_id="DEP-FIN",
          business_unit="Corporate Finance", environment="production", criticality="critical",
          contains_sensitive_data=True, business_function="Stores customer PII records"),
    Asset(asset_id="AST-PORTAL-EC2", asset_name="Customer Portal Server", aws_resource_id="i-0portal456789012",
          asset_type="ec2", application_id="APP-PORTAL", owner_id="OWN-BOB", department_id="DEP-SALES",
          business_unit="Revenue", environment="production", criticality="critical",
          contains_sensitive_data=False, business_function="Serves customer portal traffic"),
    Asset(asset_id="AST-ANALYTICS-EC2", asset_name="Analytics Server", aws_resource_id="i-0analytics78901234",
          asset_type="ec2", application_id="APP-ANALYTICS", owner_id="OWN-CHARLIE", department_id="DEP-DS",
          business_unit="R&D", environment="development", criticality="medium",
          contains_sensitive_data=False, business_function="Runs internal analytics jobs"),
    # Matches the sample GuardDuty "EC2 Instance Communicating with Cryptocurrency Mining
    # Pool" finding (resource_id i-0abc123456789 / resource_name Production-WebServer):
    # a second, Sales-owned public web server fronting the Customer Portal fleet.
    Asset(asset_id="AST-WEB-EC2", asset_name="Production-WebServer", aws_resource_id="i-0abc123456789",
          asset_type="ec2", application_id="APP-PORTAL", owner_id="OWN-BOB", department_id="DEP-SALES",
          business_unit="Revenue", environment="production", criticality="critical",
          contains_sensitive_data=False, business_function="Public-facing web server for the customer portal"),
]

def seed_if_empty(session_factory: Callable[[], Session]) -> None:
    with session_factory() as s:
        if s.scalar(select(Department).limit(1)) is not None: return
        s.add_all(_DEPARTMENTS + _OWNERS + _BUSINESS_UNITS); s.flush()
        s.add_all(_APPLICATIONS); s.flush()
        s.add_all(_ASSETS); s.commit()
