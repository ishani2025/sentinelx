"""SQLAlchemy ORM models for enterprise business context and policy data.

Two families of tables:
  - Business context: Department, Owner, Application, Asset
  - Policy: Policy, ApprovalRule, ComplianceRequirement, EscalationRule

Everything is designed to be internally consistent: an Asset belongs to a
Department and (optionally) an Application; the Application has a business
criticality, environment, and data sensitivity that flow down to any Asset
that doesn't override them; Policy/ApprovalRule/ComplianceRequirement rows
reference the same criticality/environment/data-sensitivity vocabulary so a
retrieved Asset's attributes can be matched directly against them.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Business context tables -------------------------------------------------


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    head_name: Mapped[str] = mapped_column(String(150), nullable=False)
    cost_center: Mapped[str] = mapped_column(String(20), nullable=False)

    owners: Mapped[list["Owner"]] = relationship(back_populates="department")
    applications: Mapped[list["Application"]] = relationship(back_populates="department")
    assets: Mapped[list["Asset"]] = relationship(back_populates="department")


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="owners")
    applications: Mapped[list["Application"]] = relationship(back_populates="owner")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    business_criticality: Mapped[str] = mapped_column(String(20), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    data_sensitivity: Mapped[str] = mapped_column(String(20), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="applications")
    owner: Mapped["Owner"] = relationship(back_populates="applications")
    assets: Mapped[list["Asset"]] = relationship(back_populates="application")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_identifier: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(150), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[str] = mapped_column(String(30), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), nullable=True)
    # Only set for assets not fully covered by their application's rating
    # (e.g. a user workstation). Falls back to the application's rating.
    business_criticality_override: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_sensitivity_override: Mapped[str | None] = mapped_column(String(20), nullable=True)

    department: Mapped["Department"] = relationship(back_populates="assets")
    application: Mapped["Application | None"] = relationship(back_populates="assets")


# --- Policy tables -------------------------------------------------------------


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Null means "applies regardless of environment/criticality".
    applies_to_environment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    applies_to_criticality: Mapped[str | None] = mapped_column(String(20), nullable=True)

    approval_rules: Mapped[list["ApprovalRule"]] = relationship(back_populates="policy")


class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    required_approver_role: Mapped[str] = mapped_column(String(100), nullable=False)
    # Minimum business criticality that triggers this approval requirement.
    criticality_threshold: Mapped[str] = mapped_column(String(20), nullable=False)
    environment: Mapped[str | None] = mapped_column(String(20), nullable=True)

    policy: Mapped["Policy"] = relationship(back_populates="approval_rules")


class ComplianceRequirement(Base):
    __tablename__ = "compliance_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    requirement: Mapped[str] = mapped_column(String(1000), nullable=False)
    applies_to_data_sensitivity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    applies_to_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)

    department: Mapped["Department | None"] = relationship()


class EscalationRule(Base):
    __tablename__ = "escalation_matrix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    criticality: Mapped[str] = mapped_column(String(20), nullable=False)
    escalate_to_role: Mapped[str] = mapped_column(String(100), nullable=False)
    escalate_to_contact: Mapped[str] = mapped_column(String(200), nullable=False)
    sla_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
