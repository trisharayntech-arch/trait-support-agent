"""Embedding generation via an OpenAI-compatible API."""
from __future__ import annotations

from openai import OpenAI, OpenAIError

from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


def _get_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingError(
            "OPENAI_API_KEY is not configured. Set it in your .env file."
        )
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of text chunks."""
    if not texts:
        return []
    settings = get_settings()
    client = _get_client()
    try:
        response = client.embeddings.create(model=settings.embedding_model, input=texts)
        return [item.embedding for item in response.data]
    except OpenAIError as exc:
        logger.exception("Embedding API call failed")
        raise EmbeddingError(f"Failed to generate embeddings: {exc}") from exc


def embed_query(text: str) -> list[float]:
    """Generate an embedding for a single query string."""
    result = embed_texts([text])
    return result[0]
