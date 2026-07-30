"""Risk Assessment Node.

Estimates enterprise risk purely from the incident, business context,
policy context, and knowledge context already gathered — this node
retrieves nothing new and never proposes remediation.
"""
from __future__ import annotations

from graph.state import InvestigationState
from models.llm import invoke_structured
from prompts.risk_prompt import RISK_ASSESSMENT_SYSTEM_PROMPT
from schemas.business_context import BusinessContext
from schemas.incident import Incident
from schemas.knowledge_context import KnowledgeContext
from schemas.policy_context import PolicyContext
from schemas.risk_assessment import RiskAssessment
from utils.logging import get_logger
from utils.timing import timed

logger = get_logger(__name__)

NODE_NAME = "risk_assessment"


def _build_user_prompt(
    incident: Incident,
    business_context: BusinessContext,
    policy_context: PolicyContext,
    knowledge_context: KnowledgeContext,
) -> str:
    return (
        f"Incident: {incident.incident_id} - {incident.title}\n"
        f"AWS severity: {incident.severity.value}, AWS confidence: {incident.confidence_score}\n"
        f"Description: {incident.description}\n\n"
        f"Business context: {business_context.model_dump_json(indent=2)}\n\n"
        f"Policy context: {policy_context.model_dump_json(indent=2)}\n\n"
        f"Knowledge context: {knowledge_context.model_dump_json(indent=2)}\n\n"
        "Estimate enterprise risk for this incident."
    )


def risk_assessment_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)

    with timed() as elapsed:
        try:
            risk_assessment: RiskAssessment = invoke_structured(
                system_prompt=RISK_ASSESSMENT_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(
                    state["incident"], state["business_context"], state["policy_context"], state["knowledge_context"]
                ),
                schema=RiskAssessment,
            )
        except Exception as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            raise

    duration = elapsed()
    logger.info(
        "node_end",
        node=NODE_NAME,
        duration_s=duration,
        priority=risk_assessment.priority.value,
        business_impact=risk_assessment.business_impact.value,
    )

    return {
        "risk_assessment": risk_assessment,
        "completed_nodes": [NODE_NAME],
        "reasoning_log": [{"node": NODE_NAME, "reason": "Estimated enterprise risk from gathered context."}],
    }
