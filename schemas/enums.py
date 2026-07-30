"""Shared enumerations used across investigation schemas.

Kept as plain `str` enums (rather than duplicated `Literal[...]` unions in
every schema module) so severity/criticality vocabulary stays consistent
between the incident, business, policy, risk, and response schemas.
"""
from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BusinessCriticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DataSensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def severity_rank(value: str) -> int:
    """Ordinal rank for LOW/MEDIUM/HIGH/CRITICAL vocabulary shared by
    Severity and BusinessCriticality, used for threshold comparisons
    (e.g. "does this asset meet or exceed this policy's criticality
    threshold?").
    """
    return _SEVERITY_RANK.get(value.upper(), 0)


class GraphNode(str, Enum):
    """Canonical node names the Supervisor is allowed to route to."""

    SUPERVISOR = "supervisor"
    BUSINESS_CONTEXT = "business_context"
    POLICY = "policy"
    KNOWLEDGE = "knowledge"
    RISK_ASSESSMENT = "risk_assessment"
    RESPONSE_PLANNING = "response_planning"
    END = "END"
