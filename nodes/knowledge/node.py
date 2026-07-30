"""Knowledge Node.

Retrieves relevant cybersecurity knowledge from the FAISS enterprise
knowledge base (MITRE ATT&CK references, playbooks, historical incidents,
TheHive cases, threat intel) via semantic search over the incident
description and MITRE techniques, then asks the shared LLM to summarize
only what was retrieved.
"""
from __future__ import annotations

import json

from graph.state import InvestigationState
from models.llm import invoke_structured
from prompts.knowledge_prompt import KNOWLEDGE_SYSTEM_PROMPT
from schemas.incident import Incident
from schemas.knowledge_context import KnowledgeContext
from utils.logging import get_logger
from utils.timing import timed
from vectorstore.retriever import retrieve

logger = get_logger(__name__)

NODE_NAME = "knowledge"
RETRIEVAL_K = 6


def _build_query(incident: Incident) -> str:
    technique_text = "; ".join(f"{t.technique_id} {t.name}" for t in incident.mitre_techniques)
    return f"{incident.title}. {incident.description} Techniques observed: {technique_text}"


def _build_user_prompt(incident: Incident, retrieved: list[dict]) -> str:
    return (
        f"Incident: {incident.incident_id} - {incident.title}\n"
        f"Description: {incident.description}\n"
        f"MITRE techniques (AWS-provided): {[t.technique_id for t in incident.mitre_techniques]}\n\n"
        "Documents retrieved via semantic search over the enterprise knowledge base:\n"
        f"{json.dumps(retrieved, indent=2)}"
    )


def knowledge_node(state: InvestigationState) -> dict:
    logger.info("node_start", node=NODE_NAME)
    incident = state["incident"]

    with timed() as elapsed:
        try:
            documents = retrieve(_build_query(incident), k=RETRIEVAL_K)
            retrieved = [
                {
                    "doc_id": doc.metadata.get("doc_id"),
                    "title": doc.metadata.get("title"),
                    "doc_type": doc.metadata.get("doc_type"),
                    "mitre_techniques": doc.metadata.get("mitre_techniques", []),
                    "content": doc.page_content,
                }
                for doc in documents
            ]

            knowledge_context: KnowledgeContext = invoke_structured(
                system_prompt=KNOWLEDGE_SYSTEM_PROMPT,
                user_prompt=_build_user_prompt(incident, retrieved),
                schema=KnowledgeContext,
            )
        except Exception as error:
            logger.error("node_error", node=NODE_NAME, error=str(error))
            raise

    duration = elapsed()
    logger.info(
        "node_end",
        node=NODE_NAME,
        duration_s=duration,
        documents_retrieved=len(knowledge_context.retrieved_documents),
    )

    return {
        "knowledge_context": knowledge_context,
        "completed_nodes": [NODE_NAME],
        "reasoning_log": [{"node": NODE_NAME, "reason": "Retrieved and summarized relevant enterprise knowledge."}],
    }
