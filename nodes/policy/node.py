"""Policy Node.

Retrieves applicable policies, required approvals, compliance constraints,
and escalation routing from PostgreSQL (filtered deterministically by the
already-gathered business context), then asks the shared LLM to explain why
each retrieved record applies and summarize it.
"""
from __future__ import annotations

import json

from database.postgres import session_scope
from graph.state import InvestigationState
from models.llm import invoke_structured
from nodes.policy.tools import fetch_policy_records
from prompts.policy_prompt import POLICY_SYSTEM_PROMPT
from schemas.incident import Incident
from schemas.policy_context import PolicyContext
from utils.logging import get_logger
from utils.timing import timed

logger = get_logger(__name__)

NODE_NAME = "policy"


def _build_user_prompt(incident: Incident, business_summary: str, records: dict) -> str:
    return (
        f"Incident: {incident.incident_id} - {incident.title} (severity {incident.severity.value})\n"
        f"Business context summary: {business_summary}\n\n"
        "Policy records retrieved from PostgreSQL that already matched this "
        "incident's environment/criticality/data-sensitivity:\n"
        f"{json.dumps(records, indent=2)}"
    )


def policy_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)
    incident = state["incident"]
    business_context = state["business_context"]

    with timed() as elapsed:
        try:
            with session_scope() as db:
                records = fetch_policy_records(db, incident, business_context)

            policy_context: PolicyContext = invoke_structured(
                system_prompt=POLICY_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(incident, business_context.business_summary, records),
                schema=PolicyContext,
            )
        except Exception as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            raise

    duration = elapsed()
    logger.info(
        "node_end",
        node=NODE_NAME,
        duration_s=duration,
        policies_found=len(policy_context.applicable_policies),
    )

    return {
        "policy_context": policy_context,
        "completed_nodes": [NODE_NAME],
        "reasoning_log": [{"node": NODE_NAME, "reason": "Retrieved and interpreted applicable policy for this incident."}],
    }
