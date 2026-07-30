"""Output of the Business Context Node: enterprise ownership and criticality
data for every asset in the incident, retrieved from PostgreSQL and
summarized (never estimated) by the LLM.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.enums import BusinessCriticality, DataSensitivity, Environment


class AssetBusinessContext(BaseModel):
    asset_id: str
    hostname: str | None = None
    asset_type: str
    application_name: str | None = None
    department_name: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    business_criticality: BusinessCriticality
    environment: Environment
    data_sensitivity: DataSensitivity


class BusinessContext(BaseModel):
    affected_assets: list[AssetBusinessContext] = Field(default_factory=list)
    primary_department: str | None = None
    primary_application: str | None = None
    overall_business_criticality: BusinessCriticality
    business_summary: str = Field(..., description="LLM summary of retrieved business context, no risk estimation")
