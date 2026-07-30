"""SQL retrieval tool for the Business Context Node.

Looks up every asset affected by the incident in PostgreSQL by resource id,
hostname, or IP address, and returns plain dict records (joined with
Application/Department/Owner) for the LLM to summarize. Never estimates
anything itself — a resource with no matching record is reported as such.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import Asset
from schemas.incident import AffectedResource


def _asset_criticality(asset: Asset) -> str:
    if asset.business_criticality_override:
        return asset.business_criticality_override
    if asset.application:
        return asset.application.business_criticality
    return "MEDIUM"


def _asset_data_sensitivity(asset: Asset) -> str:
    if asset.data_sensitivity_override:
        return asset.data_sensitivity_override
    if asset.application:
        return asset.application.data_sensitivity
    return "internal"


def _find_asset(db: Session, resource: AffectedResource) -> Asset | None:
    candidates = {
        value
        for value in (resource.resource_id, resource.hostname, resource.ip_address)
        if value
    }
    if not candidates:
        return None

    stmt = (
        select(Asset)
        .options(joinedload(Asset.application), joinedload(Asset.department))
        .where(
            (Asset.asset_identifier.in_(candidates))
            | (Asset.hostname.in_(candidates))
            | (Asset.ip_address.in_(candidates))
        )
    )
    return db.execute(stmt).unique().scalars().first()


def fetch_business_records(db: Session, affected_resources: list[AffectedResource]) -> list[dict]:
    """Returns one record per affected resource: either the matched asset's
    full business context, or `{"found": False, ...}` if nothing matched.
    """
    records: list[dict] = []

    for resource in affected_resources:
        asset = _find_asset(db, resource)
        if asset is None:
            records.append(
                {
                    "found": False,
                    "queried_resource_id": resource.resource_id,
                    "queried_hostname": resource.hostname,
                }
            )
            continue

        records.append(
            {
                "found": True,
                "asset_id": asset.asset_identifier,
                "hostname": asset.hostname,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "department_name": asset.department.name if asset.department else None,
                "application_name": asset.application.name if asset.application else None,
                "owner_name": asset.application.owner.name if asset.application else None,
                "owner_email": asset.application.owner.email if asset.application else None,
                "business_criticality": _asset_criticality(asset),
                "data_sensitivity": _asset_data_sensitivity(asset),
            }
        )

    return records
