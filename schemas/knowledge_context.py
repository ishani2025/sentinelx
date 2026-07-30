"""Output of the Knowledge Node: cybersecurity knowledge retrieved from the
FAISS enterprise knowledge base (MITRE ATT&CK, playbooks, historical
incidents, TheHive case summaries, threat intelligence).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedDocument(BaseModel):
    doc_id: str
    title: str
    doc_type: str = Field(..., description="e.g. mitre_attack, playbook, historical_incident, thehive_case, threat_intel")
    snippet: str
    relevance_score: float
    mitre_techniques: list[str] = Field(default_factory=list)


class KnowledgeContext(BaseModel):
    retrieved_documents: list[RetrievedDocument] = Field(default_factory=list)
    playbook_recommendations: list[str] = Field(default_factory=list)
    historical_context: str = Field(default="")
    knowledge_summary: str
