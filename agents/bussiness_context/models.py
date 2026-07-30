"""SQLAlchemy 2.0 ORM models for enterprise business context."""
from __future__ import annotations
from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Department(Base):
    __tablename__ = "departments"
    department_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(128))
    manager: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128))

class Owner(Base):
    __tablename__ = "owners"
    owner_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    owner_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128))
    phone: Mapped[str] = mapped_column(String(64))
    team: Mapped[str] = mapped_column(String(128))

class BusinessUnit(Base):
    __tablename__ = "business_units"
    business_unit: Mapped[str] = mapped_column(String(64), primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(32))

class Application(Base):
    __tablename__ = "applications"
    application_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    application_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    business_priority: Mapped[str] = mapped_column(String(32))
    sla: Mapped[str] = mapped_column(String(32))
    department_id: Mapped[str] = mapped_column(String(32), ForeignKey("departments.department_id"))

class Asset(Base):
    __tablename__ = "assets"
    asset_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(128))
    aws_resource_id: Mapped[str] = mapped_column(String(256), index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    application_id: Mapped[str] = mapped_column(String(32), ForeignKey("applications.application_id"))
    owner_id: Mapped[str] = mapped_column(String(32), ForeignKey("owners.owner_id"))
    department_id: Mapped[str] = mapped_column(String(32), ForeignKey("departments.department_id"))
    business_unit: Mapped[str] = mapped_column(String(64), ForeignKey("business_units.business_unit"))
    environment: Mapped[str] = mapped_column(String(32))
    criticality: Mapped[str] = mapped_column(String(32))
    contains_sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)
    business_function: Mapped[str] = mapped_column(String(256))
