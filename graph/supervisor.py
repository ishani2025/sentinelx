"""The Supervisor node: an LLM that ONLY orchestrates.

It never reasons about cybersecurity, never retrieves enterprise data, and
never generates remediation — it looks at what has completed so far and
decides which specialized node runs next. Its proposal is always validated
(and corrected if necessary) against the deterministic prerequisite graph in
`graph.router`, so a hallucinated or premature routing decision can never
break the workflow, and if the LLM call fails outright the graph still
makes progress via the deterministic fallback.
"""
from __future__ import annotations

from graph.router import next_deterministic_node, validate_next_node
from graph.state import InvestigationState
from models.llm import LLMOutputError, invoke_structured
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from schemas.enums import GraphNode
from schemas.supervisor import SupervisorDecision
from utils.logging import get_logger
from utils.timing import timed

logger = get_logger(__name__)

NODE_NAME = "supervisor"


def _build_user_prompt(state: InvestigationState) -> str:
    incident = state["incident"]
    completed = state.get("completed_nodes", [])
    return (
        f"Incident: {incident.incident_id} - {incident.title}\n"
        f"Severity (AWS-provided): {incident.severity.value}\n"
        f"Completed nodes so far: {completed or 'none'}\n"
        f"Sections populated: business_context={state.get('business_context') is not None}, "
        f"policy_context={state.get('policy_context') is not None}, "
        f"knowledge_context={state.get('knowledge_context') is not None}, "
        f"risk_assessment={state.get('risk_assessment') is not None}, "
        f"response_plan={state.get('response_plan') is not None}\n\n"
        "Which node should run next?"
    )


def supervisor_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)

    with timed() as elapsed:
        try:
            decision: SupervisorDecision = invoke_structured(
                system_prompt=SUPERVISOR_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(state),
                schema=SupervisorDecision,
                temperature=0.0,
            )
            validated = validate_next_node(decision.next_node, state.get("completed_nodes", []))
            reason = decision.reason
        except LLMOutputError as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            validated = next_deterministic_node(state.get("completed_nodes", []))
            reason = f"Supervisor LLM call failed ({error}); used deterministic fallback ordering."

    workflow_complete = validated == GraphNode.END
    duration = elapsed()
    logger.info(
        "node_end", node=NODE_NAME, duration_s=duration, next_node=validated.value, workflow_complete=workflow_complete
    )

    return {
        "current_node": validated.value,
        "workflow_complete": workflow_complete,
        "reasoning_log": [{"node": NODE_NAME, "reason": reason}],
    }
