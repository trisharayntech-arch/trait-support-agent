"""Retrieval logic: fetch relevant chunks and compute an aggregate confidence score."""
from __future__ import annotations

from dataclasses import dataclass

from config.settings import get_settings
from rag.vector_store import query_similar_chunks


@dataclass
class RetrievalResult:
    chunks: list[dict]
    top_score: float
    is_confident: bool


def retrieve(query: str) -> RetrievalResult:
    settings = get_settings()
    chunks = query_similar_chunks(query, top_k=settings.top_k_results)
    top_score = chunks[0]["similarity_score"] if chunks else 0.0
    is_confident = bool(chunks) and top_score >= settings.confidence_threshold
    return RetrievalResult(chunks=chunks, top_score=top_score, is_confident=is_confident)
