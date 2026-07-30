"""
Four independent Business Context tools (LangChain tool-calling).

Each tool has a pure implementation function (testable without LangChain) and a
LangChain `@tool` wrapper built by `make_business_tools(...)` with dependency-injected
session factory + summary LLM call, plus a `collector` dict used as the node's working
memory across tool calls.

  1. enterprise_asset_resolver     — AWS resource  -> enterprise asset (PostgreSQL)
  2. business_metadata_retrieval   — asset id       -> enterprise metadata (PostgreSQL)
  3. normalize_business_metadata   — resolved+meta  -> normalized business fields (Formatter)
  4. business_summary              — normalized     -> summary + reasoning (Llama 3.2)
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Asset, Application, Owner, Department, BusinessUnit
from .schemas import AssetResolution, AssetMetadata, BusinessSummary
from .prompts import load_business_summary_prompt
from .logger import log
from .utils import parse_json


# --------------------------------------------------------------------------- #
# Shared, reusable DB access (no duplicate query logic)
# --------------------------------------------------------------------------- #
def _find_asset(session: Session, *, aws_resource_id: Optional[str] = None,
                asset_id: Optional[str] = None) -> Optional[Asset]:
    if asset_id:
        return session.get(Asset, asset_id)
    if aws_resource_id:
        a = session.scalar(select(Asset).where(Asset.aws_resource_id == aws_resource_id))
        if a is None:  # tolerate ARNs / partial ids
            a = session.scalar(select(Asset).where(Asset.aws_resource_id.like(f"%{aws_resource_id}%")))
        return a
    return None


def _bundle(session: Session, asset: Asset) -> dict[str, Any]:
    app = session.get(Application, asset.application_id)
    owner = session.get(Owner, asset.owner_id)
    dept = session.get(Department, asset.department_id)
    bu = session.get(BusinessUnit, asset.business_unit)
    return {"asset": asset, "app": app, "owner": owner, "dept": dept, "bu": bu}


# --------------------------------------------------------------------------- #
# Pure implementations (dependency-injected session factory)
# --------------------------------------------------------------------------- #
def resolve_asset_impl(session_factory: Callable[[], Session], aws_resource_id: str) -> Optional[AssetResolution]:
    with session_factory() as s:
        a = _find_asset(s, aws_resource_id=aws_resource_id)
        if not a:
            return None
        return AssetResolution(asset_id=a.asset_id, asset_name=a.asset_name, asset_type=a.asset_type,
                               application_id=a.application_id, business_unit=a.business_unit)


def retrieve_metadata_impl(session_factory: Callable[[], Session], asset_id: str) -> Optional[AssetMetadata]:
    with session_factory() as s:
        a = _find_asset(s, asset_id=asset_id)
        if not a:
            return None
        b = _bundle(s, a)
        app, owner, dept = b["app"], b["owner"], b["dept"]
        return AssetMetadata(
            owner=owner.owner_name, owner_email=owner.email, owner_team=owner.team,
            department=dept.department_name, application_name=app.application_name,
            application_description=app.description, criticality=a.criticality,
            environment=a.environment, business_function=a.business_function,
            contains_sensitive_data=a.contains_sensitive_data,
            business_priority=app.business_priority, sla=app.sla, business_unit=a.business_unit)


def normalize_impl(session_factory: Callable[[], Session], asset_id: str) -> Optional[dict[str, Any]]:
    with session_factory() as s:
        a = _find_asset(s, asset_id=asset_id)
        if not a:
            return None
        b = _bundle(s, a); app, owner, dept = b["app"], b["owner"], b["dept"]
        return {
            "asset_name": a.asset_name, "asset_type": a.asset_type,
            "application_name": app.application_name, "application_description": app.description,
            "department": dept.department_name, "business_unit": a.business_unit,
            "owner": owner.owner_name, "owner_email": owner.email, "owner_team": owner.team,
            "environment": a.environment, "criticality": a.criticality,
            "contains_sensitive_data": a.contains_sensitive_data,
            "business_function": a.business_function,
            "business_priority": app.business_priority, "sla": app.sla,
        }


def summary_impl(summary_call: Callable[[str, str], str], normalized: dict[str, Any]) -> BusinessSummary:
    """LLM summary grounded strictly on the normalized metadata; deterministic fallback if LLM fails."""
    system = load_business_summary_prompt()
    user = "Normalized enterprise metadata (facts only, do not invent):\n" + json.dumps(normalized, indent=2)
    try:
        data = parse_json(summary_call(system, user))
        if data and data.get("summary"):
            return BusinessSummary(summary=str(data["summary"]),
                                   reasoning=str(data.get("reasoning", "")))
    except Exception as ex:
        log("business_summary_llm_error", error=str(ex))
    # grounded fallback (no invented facts)
    s = (f"{normalized['asset_name']} is a {normalized['criticality']} {normalized['asset_type']} "
         f"in {normalized['environment']} supporting the {normalized['application_name']} application "
         f"({normalized['department']} / {normalized['business_unit']}), owned by {normalized['owner']}. "
         f"Business priority {normalized['business_priority']}, SLA {normalized['sla']}. "
         f"{'Contains sensitive data.' if normalized['contains_sensitive_data'] else 'No sensitive data.'}")
    return BusinessSummary(summary=s, reasoning="Grounded summary assembled from retrieved PostgreSQL metadata.")


# --------------------------------------------------------------------------- #
# LangChain tool factory (dependency injection + shared collector)
# --------------------------------------------------------------------------- #
def make_business_tools(session_factory: Callable[[], Session],
                        summary_call: Callable[[str, str], str],
                        collector: dict[str, Any]) -> list:
    """Build the four LangChain tools bound to the injected deps and working-memory collector."""
    from langchain_core.tools import tool

    @tool
    def enterprise_asset_resolver(aws_resource_id: str) -> str:
        """Map an AWS resource (ARN, EC2 instance id, IAM user, or S3 bucket) to an enterprise asset."""
        log("asset_resolution_started", aws_resource_id=aws_resource_id)
        res = resolve_asset_impl(session_factory, aws_resource_id)
        if not res:
            return json.dumps({"resolved": False, "message": f"No enterprise asset for '{aws_resource_id}'."})
        collector["resolution"] = res.model_dump()
        return res.model_dump_json()

    @tool
    def business_metadata_retrieval(asset_id: str) -> str:
        """Retrieve enterprise metadata (owner, department, application, criticality, etc.) for an asset id."""
        meta = retrieve_metadata_impl(session_factory, asset_id)
        if not meta:
            return json.dumps({"found": False, "message": f"No metadata for asset '{asset_id}'."})
        collector["metadata"] = meta.model_dump()
        log("metadata_retrieved", asset_id=asset_id)
        return meta.model_dump_json()

    @tool
    def normalize_business_metadata(asset_id: str) -> str:
        """Normalize the resolved asset and its metadata into structured business-context fields."""
        norm = normalize_impl(session_factory, asset_id)
        if not norm:
            return json.dumps({"normalized": False, "message": f"No asset '{asset_id}' to normalize."})
        collector["normalized"] = norm
        return json.dumps(norm)

    @tool
    def business_summary(asset_id: str) -> str:
        """Generate a concise business summary and reasoning from the normalized metadata (facts only)."""
        norm = collector.get("normalized") or normalize_impl(session_factory, asset_id)
        if not norm:
            return json.dumps({"summarized": False, "message": f"No normalized metadata for '{asset_id}'."})
        log("llm_started", tool="business_summary")
        summ = summary_impl(summary_call, norm)
        collector["summary"] = summ.model_dump()
        log("llm_finished", tool="business_summary")
        return summ.model_dump_json()

    return [enterprise_asset_resolver, business_metadata_retrieval,
            normalize_business_metadata, business_summary]
