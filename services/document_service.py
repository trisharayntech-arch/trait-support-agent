"""Document ingestion service: validate -> extract -> chunk -> embed -> store."""
from __future__ import annotations

from database import db
from rag.chunking import chunk_text
from rag.document_loader import DocumentLoadError, extract_text
from rag.embeddings import EmbeddingError
from rag.vector_store import add_document_chunks, delete_document_chunks
from utils.logger import get_logger
from utils.validators import (
    ValidationError,
    flag_suspicious_content,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
)

logger = get_logger(__name__)


class DocumentServiceError(Exception):
    """Raised when document ingestion fails at any stage."""


def ingest_document(filename: str, file_bytes: bytes) -> dict:
    """Full ingestion pipeline for one uploaded document.

    Returns a dict describing the stored document record.
    Raises DocumentServiceError on any failure (validation, extraction, or embedding).
    """
    safe_name = sanitize_filename(filename)

    try:
        extension = validate_file_extension(safe_name)
        validate_file_size(len(file_bytes))
    except ValidationError as exc:
        raise DocumentServiceError(str(exc)) from exc

    document_id = db.insert_document(filename=safe_name, file_type=extension)

    try:
        text = extract_text(file_bytes, extension)

        suspicious = flag_suspicious_content(text)
        if suspicious:
            logger.warning(
                "Suspicious instruction-like patterns found in '%s': %s", safe_name, suspicious
            )

        chunks = chunk_text(text)
        if not chunks:
            raise DocumentServiceError("Document produced no usable text chunks.")

        stored_count = add_document_chunks(document_id, safe_name, chunks)
        db.update_document_status(document_id, status="indexed", chunk_count=stored_count)

        return {
            "id": document_id,
            "filename": safe_name,
            "file_type": extension,
            "chunk_count": stored_count,
            "status": "indexed",
            "suspicious_patterns_flagged": suspicious,
        }

    except (DocumentLoadError, EmbeddingError, DocumentServiceError) as exc:
        db.update_document_status(document_id, status="failed", chunk_count=0)
        logger.error("Ingestion failed for '%s': %s", safe_name, exc)
        raise DocumentServiceError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - guarantee status is recorded even on unexpected errors
        db.update_document_status(document_id, status="failed", chunk_count=0)
        logger.exception("Unexpected ingestion failure for '%s'", safe_name)
        raise DocumentServiceError(f"Unexpected error while processing document: {exc}") from exc


def remove_document(document_id: int) -> None:
    delete_document_chunks(document_id)
    db.delete_document(document_id)


def get_all_documents() -> list[dict]:
    return db.list_documents()
