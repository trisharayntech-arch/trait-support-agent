"""
Text chunking for embedding.

Uses LangChain's RecursiveCharacterTextSplitter — this is one of the few
places LangChain genuinely simplifies things (a well-tuned recursive splitter
that respects paragraph/sentence boundaries) versus writing/maintaining a
custom splitter ourselves.
"""
from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks sized per configured chunk_size/overlap."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if c.strip()]
