"""Pydantic v2 models for the Business Context Node."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class AssetResolution(BaseModel):
    """Output of the Enterprise Asset Resolver tool."""
    asset_id: str
    asset_name: str
    asset_type: str
    application_id: str
    business_unit: str
    resolved: bool = True

class AssetMetadata(BaseModel):
    """Output of the Business Metadata Retrieval tool."""
    owner: str
    owner_email: str
    owner_team: str
    department: str
    application_name: str
    application_description: str
    criticality: str
    environment: str
    business_function: str
    contains_sensitive_data: bool
    business_priority: str
    sla: str
    business_unit: str

class BusinessSummary(BaseModel):
    """Output of the Business Summary (LLM) tool."""
    summary: str
    reasoning: str

class BusinessContext(BaseModel):
    """Validated output written to InvestigationState.business_context."""
    asset_name: str
    asset_type: str
    application_name: str
    application_description: str
    department: str
    business_unit: str
    owner: str
    owner_email: str
    owner_team: str
    environment: str
    criticality: str
    contains_sensitive_data: bool
    business_function: str
    business_priority: str
    sla: str
    summary: str
    reasoning: str

class BusinessNodeError(BaseModel):
    error: str
    detail: str
