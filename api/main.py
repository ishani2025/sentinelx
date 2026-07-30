"""SentinelX FastAPI application.

Exposes a single endpoint, `POST /investigate`, that runs an AWS Security
Hub / GuardDuty investigation report through the SentinelX LangGraph
workflow and returns the completed InvestigationState (business context,
policy context, knowledge context, risk assessment, response plan).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from graph.graph import run_investigation
from models.llm import LLMOutputError
from schemas.incident import Incident
from schemas.investigation_state import InvestigationStateModel
from utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="SentinelX",
    description="Deterministic AI Security Response Orchestration Platform. "
    "Enriches an AWS Security Hub / GuardDuty investigation with enterprise "
    "context and produces an organization-aware response plan.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/investigate", response_model=InvestigationStateModel)
def investigate(incident: Incident) -> InvestigationStateModel:
    """Runs the full SentinelX graph for a single AWS investigation report."""
    try:
        final_state = run_investigation(incident)
    except LLMOutputError as error:
        logger.error("investigation_failed", incident_id=incident.incident_id, error=str(error))
        raise HTTPException(status_code=502, detail=f"LLM failed to produce valid output: {error}") from error
    except Exception as error:  # noqa: BLE001 - surface any node failure as a 500 with context
        logger.error("investigation_failed", incident_id=incident.incident_id, error=str(error))
        raise HTTPException(status_code=500, detail=f"Investigation failed: {error}") from error

    try:
        return InvestigationStateModel.model_validate(final_state)
    except ValidationError as error:
        logger.error("investigation_state_invalid", incident_id=incident.incident_id, error=str(error))
        raise HTTPException(status_code=500, detail=f"Investigation completed but produced an invalid state: {error}") from error


if __name__ == "__main__":
    import uvicorn

    from config.settings import get_settings

    settings = get_settings()
    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=True)
