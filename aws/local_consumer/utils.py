"""Utility functions for working with Security Hub finding documents."""

from __future__ import annotations

from typing import Any


def get_severity_label(finding: dict[str, Any]) -> str:
    """Return a normalized severity label from a Security Hub finding."""
    severity = finding.get("Severity", {})
    label = severity.get("Label") or severity.get("Normalized") or "UNKNOWN"
    return str(label).upper()


def get_attack_type(finding: dict[str, Any]) -> str:
    """Return the best available attack or finding type description."""
    types = finding.get("Types")
    if isinstance(types, list) and types:
        return str(types[0])

    finding_type = finding.get("Type")
    if finding_type:
        return str(finding_type)

    product_fields = finding.get("ProductFields", {})
    if isinstance(product_fields, dict):
        for key in ("aws/securityhub/FindingId", "ThreatPurpose", "AttackType"):
            if product_fields.get(key):
                return str(product_fields[key])

    return "Unknown"


def get_primary_resource(finding: dict[str, Any]) -> str:
    """Return a concise representation of the first affected resource."""
    resources = finding.get("Resources")
    if isinstance(resources, list) and resources:
        resource = resources[0]
        if isinstance(resource, dict):
            return str(resource.get("Id") or resource.get("Type") or "Unknown")
        return str(resource)
    return "Unknown"


def get_finding_title(finding: dict[str, Any]) -> str:
    """Return the finding title with a stable fallback."""
    return str(finding.get("Title") or finding.get("Description") or "Untitled finding")

