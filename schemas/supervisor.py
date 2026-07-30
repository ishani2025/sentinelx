"""Structured output contract for the Supervisor node."""
from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.enums import GraphNode


class SupervisorDecision(BaseModel):
    next_node: GraphNode
    reason: str = Field(..., description="Why this node should run next (orchestration only, no domain reasoning)")
    workflow_complete: bool
