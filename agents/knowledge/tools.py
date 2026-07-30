"""Three independent LangChain retrieval tools over the single knowledge vector DB.
The LLM decides which to call. Each stores results in a shared collector."""
from __future__ import annotations
import json
from typing import Any, Callable, Optional
from .retriever import KnowledgeRetriever
from .logger import log

def make_knowledge_tools(retriever: KnowledgeRetriever, collector: dict[str, Any]) -> list:
    from langchain_core.tools import tool

    @tool
    def enterprise_playbook_retriever(query: str, attack_type: Optional[str] = None,
                                      asset_type: Optional[str] = None) -> str:
        """Retrieve enterprise incident-response playbooks relevant to the attack (FAISS)."""
        log("retriever_selected", tool="enterprise_playbook_retriever")
        docs = retriever.playbooks(query, attack_type=attack_type, asset_type=asset_type)
        collector.setdefault("playbooks", []).extend(docs)
        return json.dumps(docs)

    @tool
    def thehive_case_retriever(query: str, attack_type: Optional[str] = None,
                               asset_type: Optional[str] = None) -> str:
        """Retrieve similar historical TheHive security cases (FAISS)."""
        log("retriever_selected", tool="thehive_case_retriever")
        docs = retriever.cases(query, attack_type=attack_type, asset_type=asset_type)
        collector.setdefault("cases", []).extend(docs)
        return json.dumps(docs)

    @tool
    def threat_intelligence_retriever(query: str, mitre_technique: Optional[str] = None) -> str:
        """Retrieve threat-intelligence reports (actors, campaigns, IOCs, MITRE) from FAISS."""
        log("retriever_selected", tool="threat_intelligence_retriever")
        docs = retriever.threat_intel(query, mitre_technique=mitre_technique)
        docs += retriever.mitre(query, mitre_technique=mitre_technique)
        collector.setdefault("threat_intel", []).extend(docs)
        return json.dumps(docs)

    return [enterprise_playbook_retriever, thehive_case_retriever, threat_intelligence_retriever]
