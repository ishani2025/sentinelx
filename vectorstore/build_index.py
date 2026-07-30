"""Builds the FAISS enterprise knowledge index from `vectorstore/documents/`.

Reads the manifest (doc_id, title, doc_type, mitre_techniques) alongside
each markdown source file, chunks each document, embeds the chunks with
SentenceTransformers, and persists a FAISS index to `FAISS_INDEX_DIR`.

Run as a script:
    python -m vectorstore.build_index
"""
from __future__ import annotations

import json
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


def _load_manifest(documents_dir: Path) -> list[dict]:
    manifest_path = documents_dir / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)["documents"]


def _build_documents(documents_dir: Path) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n## ", "\n\n", "\n", " "]
    )
    documents: list[Document] = []

    for entry in _load_manifest(documents_dir):
        source_path = documents_dir / entry["file"]
        text = source_path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)

        for chunk_index, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "doc_id": entry["doc_id"],
                        "title": entry["title"],
                        "doc_type": entry["doc_type"],
                        "mitre_techniques": entry.get("mitre_techniques", []),
                        "source_file": entry["file"],
                        "chunk_index": chunk_index,
                    },
                )
            )

    return documents


def build_index() -> None:
    settings = get_settings()
    documents_dir = Path(settings.faiss_documents_dir)
    index_dir = Path(settings.faiss_index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    documents = _build_documents(documents_dir)
    logger.info("vectorstore_chunking_complete", chunk_count=len(documents), documents_dir=str(documents_dir))

    embeddings = HuggingFaceEmbeddings(model_name=settings.faiss_embedding_model)
    index = FAISS.from_documents(documents, embeddings)
    index.save_local(str(index_dir))

    logger.info("vectorstore_index_built", index_dir=str(index_dir))


if __name__ == "__main__":
    build_index()
    print("FAISS enterprise knowledge index built successfully.")
