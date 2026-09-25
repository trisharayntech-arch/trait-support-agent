"""Extract raw text from uploaded document files (PDF, TXT, DOCX)."""
from __future__ import annotations

import io

from pypdf import PdfReader
from docx import Document as DocxDocument

from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoadError(Exception):
    """Raised when a document's text cannot be extracted."""


def extract_text(file_bytes: bytes, extension: str) -> str:
    """Extract plain text from file bytes based on extension (.pdf, .txt, .docx)."""
    try:
        if extension == ".txt":
            return _extract_txt(file_bytes)
        if extension == ".pdf":
            return _extract_pdf(file_bytes)
        if extension == ".docx":
            return _extract_docx(file_bytes)
        raise DocumentLoadError(f"Unsupported extension: {extension}")
    except DocumentLoadError:
        raise
    except Exception as exc:  # noqa: BLE001 - convert any parser error into a domain error
        logger.exception("Failed to extract text from document")
        raise DocumentLoadError(f"Could not read file contents: {exc}") from exc


def _extract_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="replace")


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    if reader.is_encrypted:
        raise DocumentLoadError("PDF is password-protected and cannot be processed.")
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    text = "\n".join(pages_text).strip()
    if not text:
        raise DocumentLoadError(
            "No extractable text found in PDF (it may be a scanned image without OCR)."
        )
    return text


def _extract_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise DocumentLoadError("No extractable text found in DOCX file.")
    return text
