"""
Single FAISS vector store for ALL enterprise knowledge (playbooks, TheHive cases,
threat intel, MITRE notes). Documents are loaded from the documents/ folders, parsed
for metadata, chunked, and indexed.

If FAISS / sentence-transformers are unavailable, a lightweight in-memory keyword store
with the SAME interface is used (dependency-injectable, so the node always runs and is
testable). Metadata filtering is supported by both backends.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .logger import log

_HERE = os.path.dirname(__file__)
_DOCS_DIR = os.path.join(_HERE, "documents")
_META_KEYS = ("source_type", "attack_type", "mitre_technique", "asset_type",
              "severity", "department", "title", "case_id")


@dataclass
class KDoc:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Loading + chunking
# --------------------------------------------------------------------------- #
def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    meta: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def load_documents(docs_dir: str = _DOCS_DIR) -> list[KDoc]:
    docs: list[KDoc] = []
    for root, _, files in os.walk(docs_dir):
        for fn in sorted(files):
            path = os.path.join(root, fn)
            raw = open(path, encoding="utf-8").read()
            if fn.endswith(".json"):
                obj = json.loads(raw)
                meta = {k: obj.get(k) for k in _META_KEYS if obj.get(k) is not None}
                content = json.dumps(obj, indent=2)
            else:
                meta, body = _parse_frontmatter(raw)
                content = body
            meta = {k: str(v).lower() if k in ("source_type", "attack_type", "asset_type",
                    "severity", "department") else v for k, v in meta.items()}
            meta["path"] = os.path.relpath(path, docs_dir)
            docs.append(KDoc(content=content, metadata=meta))
    log("documents_loaded", count=len(docs))
    return docs


def _chunk(docs: list[KDoc], size: int = 1200, overlap: int = 120) -> list[KDoc]:
    out: list[KDoc] = []
    for d in docs:
        # keep structured JSON cases whole so downstream json.loads works
        if d.metadata.get("source_type") == "thehive_case" or len(d.content) <= size:
            out.append(d); continue
        i = 0
        while i < len(d.content):
            out.append(KDoc(content=d.content[i:i + size], metadata=dict(d.metadata)))
            i += size - overlap
    return out


def _match_filter(meta: dict[str, Any], where: Optional[dict[str, Any]]) -> bool:
    if not where:
        return True
    for k, v in where.items():
        if v is None:
            continue
        mv = meta.get(k)
        # 'any' documents match any requested value for that key
        if mv == "any":
            continue
        if str(mv).lower() != str(v).lower():
            return False
    return True


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #
class _KeywordStore:
    """Fallback store: token-overlap scoring + metadata filter. No external deps."""
    def __init__(self, docs: list[KDoc]):
        self._docs = docs

    @staticmethod
    def _tok(s: str) -> set[str]:
        return set(re.findall(r"[a-z0-9_.]+", s.lower()))

    def search(self, query: str, k: int = 4, where: Optional[dict] = None) -> list[dict]:
        # A real narrowing filter (attack_type/asset_type/mitre_technique, beyond just
        # source_type) is authoritative on its own: a doc matching it is targeted
        # evidence even when the free-text query is sparse/placeholder text with zero
        # token overlap (e.g. a terse or missing incident description). Previously,
        # requiring nonzero overlap on top of an exact filter match silently threw
        # away exact matches, forcing the LLM synthesis step to reason over zero
        # evidence — which it should not be trusted to safely refuse (see
        # knowledge_node's has_evidence guard). A bare source_type filter (no real
        # narrowing) still requires overlap, so a genuinely irrelevant query correctly
        # returns nothing rather than arbitrary same-type documents.
        q = self._tok(query)
        narrowed = bool(where) and len(where) > 1
        scored = []
        for d in self._docs:
            if not _match_filter(d.metadata, where):
                continue
            overlap = len(q & self._tok(d.content + " " + " ".join(map(str, d.metadata.values()))))
            if overlap or narrowed:
                scored.append((overlap, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"content": d.content, "metadata": d.metadata, "score": s} for s, d in scored[:k]]


class _FaissStore:
    """Primary store: langchain FAISS + sentence-transformers embeddings."""
    def __init__(self, docs: list[KDoc]):
        from langchain_community.vectorstores import FAISS
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except Exception:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.documents import Document
        emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        lc_docs = [Document(page_content=d.content, metadata=d.metadata) for d in docs]
        self._vs = FAISS.from_documents(lc_docs, emb)

    def search(self, query: str, k: int = 4, where: Optional[dict] = None) -> list[dict]:
        flt = {kk: vv for kk, vv in (where or {}).items() if vv is not None}
        results = self._vs.similarity_search_with_score(query, k=max(k * 3, k))
        out = []
        for doc, score in results:
            if _match_filter(doc.metadata, flt):
                out.append({"content": doc.page_content, "metadata": doc.metadata, "score": float(score)})
            if len(out) >= k:
                break
        return out


class KnowledgeVectorStore:
    """Single vector DB for all knowledge; auto-selects FAISS, falls back to keyword store."""
    def __init__(self, docs_dir: str = _DOCS_DIR, force_backend: Optional[str] = None):
        docs = _chunk(load_documents(docs_dir))
        self.backend = "keyword"
        if force_backend != "keyword":
            try:
                self._store = _FaissStore(docs); self.backend = "faiss"
            except Exception as ex:
                log("faiss_unavailable_fallback_keyword", error=str(ex))
                self._store = _KeywordStore(docs)
        else:
            self._store = _KeywordStore(docs)
        log("vector_store_ready", backend=self.backend, chunks=len(docs))

    def search(self, query: str, k: int = 4, where: Optional[dict] = None) -> list[dict]:
        return self._store.search(query, k=k, where=where)
