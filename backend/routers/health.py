"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from rag.vector_store import collection_count

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    try:
        chunk_count = collection_count()
        vector_store_ok = True
    except Exception:  # noqa: BLE001
        chunk_count = None
        vector_store_ok = False

    return {
        "status": "ok",
        "vector_store_reachable": vector_store_ok,
        "indexed_chunk_count": chunk_count,
    }
