"""
Tests for the retrieval confidence gate.

These tests patch rag.vector_store.query_similar_chunks directly so they do
NOT require a live OpenAI API key or network access — they validate the
decision logic in rag/retriever.py in isolation.
"""
from unittest.mock import patch

from rag.retriever import retrieve


def test_retrieve_confident_when_top_score_above_threshold():
    fake_chunks = [
        {"text": "Our refund policy allows 30 days.", "document_name": "policy.pdf", "similarity_score": 0.9}
    ]
    with patch("rag.retriever.query_similar_chunks", return_value=fake_chunks):
        result = retrieve("What is your refund policy?")
    assert result.is_confident is True
    assert result.top_score == 0.9


def test_retrieve_not_confident_when_no_chunks_found():
    with patch("rag.retriever.query_similar_chunks", return_value=[]):
        result = retrieve("What is the meaning of life?")
    assert result.is_confident is False
    assert result.top_score == 0.0


def test_retrieve_not_confident_when_score_below_threshold(monkeypatch):
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.5")
    from config.settings import get_settings

    get_settings.cache_clear()

    fake_chunks = [{"text": "irrelevant snippet", "document_name": "misc.pdf", "similarity_score": 0.2}]
    with patch("rag.retriever.query_similar_chunks", return_value=fake_chunks):
        result = retrieve("Completely unrelated question")
    assert result.is_confident is False
    get_settings.cache_clear()
