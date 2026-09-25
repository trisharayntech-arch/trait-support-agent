"""
ChromaDB-backed vector store wrapper.

Isolated behind this module so the retrieval backend (Chroma vs FAISS vs
something else in the future TRAIT platform) can be swapped without touching
calling code in services/ or agents/.
"""
from __future__ import annotations

import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import get_settings
from rag.embeddings import embed_query, embed_texts
from utils.logger import get_logger

logger = get_logger(__name__)

_COLLECTION_NAME = "trait_knowledge_base"
_client = None  # lazily initialized singleton


def _get_client():
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _get_collection():
    client = _get_client()
    return client.get_or_create_collection(name=_COLLECTION_NAME)


def add_document_chunks(document_id: int, filename: str, chunks: list[str]) -> int:
    """Embed and store chunks for a document. Returns number of chunks stored."""
    if not chunks:
        return 0
    embeddings = embed_texts(chunks)
    collection = _get_collection()
    ids = [f"{document_id}_{uuid.uuid4().hex[:8]}" for _ in chunks]
    metadatas = [
        {"document_id": document_id, "document_name": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    return len(chunks)


def delete_document_chunks(document_id: int) -> None:
    collection = _get_collection()
    collection.delete(where={"document_id": document_id})


def query_similar_chunks(query_text: str, top_k: int) -> list[dict]:
    """Return top_k most similar chunks with similarity scores (0..1, higher = closer)."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    query_embedding = embed_query(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for doc, meta, distance in zip(docs, metas, distances):
        # Chroma's default distance is squared L2 for normalized embeddings;
        # convert to an approximate 0..1 similarity score for a human-readable
        # confidence signal. This is a heuristic, not a calibrated probability.
        similarity = max(0.0, 1.0 - (distance / 2.0))
        output.append(
            {
                "text": doc,
                "document_name": meta.get("document_name", "unknown"),
                "document_id": meta.get("document_id"),
                "similarity_score": round(similarity, 4),
            }
        )
    return output


def collection_count() -> int:
    return _get_collection().count()
