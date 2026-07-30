"""Typed retrievers over the single KnowledgeVectorStore (metadata-filtered by source_type)."""
from __future__ import annotations
from typing import Any, Optional
from .vector_store import KnowledgeVectorStore
from .logger import log

class KnowledgeRetriever:
    """Reusable retrieval facade. Each method filters the single vector DB by source_type."""
    def __init__(self, store: KnowledgeVectorStore):
        self._store = store

    def _search(self, source_type: str, query: str, k: int, extra: Optional[dict] = None) -> list[dict]:
        where = {"source_type": source_type}
        if extra:
            where.update({k2: v for k2, v in extra.items() if v})
        docs = self._store.search(query, k=k, where=where)
        log("documents_retrieved", source_type=source_type, count=len(docs))
        return docs

    def playbooks(self, query: str, attack_type: Optional[str] = None,
                  asset_type: Optional[str] = None, k: int = 3) -> list[dict]:
        return self._search("playbook", query, k, {"attack_type": attack_type, "asset_type": asset_type})

    def cases(self, query: str, attack_type: Optional[str] = None,
              asset_type: Optional[str] = None, k: int = 3) -> list[dict]:
        return self._search("thehive_case", query, k, {"attack_type": attack_type, "asset_type": asset_type})

    def threat_intel(self, query: str, mitre_technique: Optional[str] = None, k: int = 2) -> list[dict]:
        return self._search("threat_intel", query, k, {"mitre_technique": mitre_technique})

    def mitre(self, query: str, mitre_technique: Optional[str] = None, k: int = 2) -> list[dict]:
        return self._search("mitre_note", query, k, {"mitre_technique": mitre_technique})
