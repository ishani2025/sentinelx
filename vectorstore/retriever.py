"""Semantic retrieval over the FAISS enterprise knowledge index, with
optional metadata filtering (doc_type, mitre_technique).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)


class VectorStoreNotBuiltError(RuntimeError):
    """Raised when the FAISS index has not been built yet."""


@lru_cache(maxsize=1)
def _load_index() -> FAISS:
    settings = get_settings()
    index_dir = Path(settings.faiss_index_dir)
    if not (index_dir / "index.faiss").exists():
        raise VectorStoreNotBuiltError(
            f"No FAISS index found at {index_dir}. Run `python -m vectorstore.build_index` first."
        )
    embeddings = HuggingFaceEmbeddings(model_name=settings.faiss_embedding_model)
    return FAISS.load_local(str(index_dir), embeddings, allow_dangerous_deserialization=True)


def retrieve(
    query: str,
    *,
    k: int = 5,
    doc_type: str | None = None,
    mitre_technique: str | None = None,
    fetch_k: int = 20,
) -> list[Document]:
    """Retrieves the top-`k` most relevant chunks for `query`.

    `doc_type` and `mitre_technique` are applied as post-hoc metadata
    filters over a wider `fetch_k` similarity search, since FAISS chunks
    carry list-valued metadata (mitre_techniques) that a plain equality
    filter can't express.
    """
    index = _load_index()
    candidates = index.similarity_search(query, k=fetch_k)

    def matches(doc: Document) -> bool:
        if doc_type and doc.metadata.get("doc_type") != doc_type:
            return False
        if mitre_technique and mitre_technique not in doc.metadata.get("mitre_techniques", []):
            return False
        return True

    filtered = [doc for doc in candidates if matches(doc)]
    results = filtered[:k] if (doc_type or mitre_technique) else candidates[:k]

    logger.info(
        "vectorstore_retrieve",
        query=query,
        k=k,
        doc_type=doc_type,
        mitre_technique=mitre_technique,
        result_count=len(results),
    )
    return results
