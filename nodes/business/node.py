"""Business Context Node.

Retrieves enterprise business context (ownership, department, application,
criticality, environment, data sensitivity) for every asset affected by the
incident, via the SQL Tool in `nodes.business.tools`, then asks the shared
LLM to summarize (never estimate risk from) those records.
"""
from __future__ import annotations

import json

from database.postgres import session_scope
from graph.state import InvestigationState
from models.llm import invoke_structured
from nodes.business.tools import fetch_business_records
from prompts.business_prompt import BUSINESS_CONTEXT_SYSTEM_PROMPT
from schemas.business_context import BusinessContext
from schemas.incident import Incident
from utils.logging import get_logger
from utils.timing import timed

logger = get_logger(__name__)

NODE_NAME = "business_context"


def _build_user_prompt(incident: Incident, records: list[dict]) -> str:
    return (
        f"Incident: {incident.incident_id} - {incident.title}\n"
        f"Description: {incident.description}\n"
        f"Affected resources: {[r.resource_id for r in incident.affected_resources]}\n\n"
        "Business records retrieved from PostgreSQL for these resources "
        "(one entry per affected resource; 'found': false means no matching "
        "asset record exists):\n"
        f"{json.dumps(records, indent=2)}"
    )


def business_context_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)
    incident = state["incident"]

    with timed() as elapsed:
        try:
            with session_scope() as db:
                records = fetch_business_records(db, incident.affected_resources)

            business_context: BusinessContext = invoke_structured(
                system_prompt=BUSINESS_CONTEXT_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(incident, records),
                schema=BusinessContext,
            )
        except Exception as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            raise

    duration = elapsed()
    logger.info("node_end", node=NODE_NAME, duration_s=duration, assets_found=len(business_context.affected_assets))

    return {
        "business_context": business_context,
        "completed_nodes": [NODE_NAME],
        "reasoning_log": [{"node": NODE_NAME, "reason": "Retrieved and summarized business context for affected assets."}],
    }
