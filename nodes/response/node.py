"""Response Planning Node.

Produces the final ordered, organization-aware response plan from the
entire InvestigationState. This is the last node in the MVP graph — it only
plans; it never executes, calls the AWS SDK, notifies anyone, or verifies
anything.
"""
from __future__ import annotations

from graph.state import InvestigationState
from models.llm import invoke_structured
from prompts.response_prompt import RESPONSE_PLANNING_SYSTEM_PROMPT
from schemas.response_plan import ResponsePlan
from utils.logging import get_logger
from utils.timing import timed

logger = get_logger(__name__)

NODE_NAME = "response_planning"


def _build_user_prompt(state: InvestigationState) -> str:
    incident = state["incident"]
    return (
        f"Incident: {incident.incident_id} - {incident.title}\n"
        f"AWS recommended remediation: {incident.aws_recommended_remediation}\n\n"
        f"Business context: {state['business_context'].model_dump_json(indent=2)}\n\n"
        f"Policy context: {state['policy_context'].model_dump_json(indent=2)}\n\n"
        f"Knowledge context: {state['knowledge_context'].model_dump_json(indent=2)}\n\n"
        f"Risk assessment: {state['risk_assessment'].model_dump_json(indent=2)}\n\n"
        "Produce the ordered response plan."
    )


def response_planning_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)

    with timed() as elapsed:
        try:
            response_plan: ResponsePlan = invoke_structured(
                system_prompt=RESPONSE_PLANNING_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(state),
                schema=ResponsePlan,
            )
        except Exception as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            raise

    duration = elapsed()
    logger.info(
        "node_end",
        node=NODE_NAME,
        duration_s=duration,
        action_count=len(response_plan.actions),
        overall_requires_approval=response_plan.overall_requires_approval,
    )

    return {
        "response_plan": response_plan,
        "completed_nodes": [NODE_NAME],
        "reasoning_log": [{"node": NODE_NAME, "reason": "Generated ordered enterprise response plan."}],
    }
