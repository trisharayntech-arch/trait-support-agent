"""Input and file validation utilities."""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from config.settings import get_settings

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# Very small, defense-in-depth heuristic for obvious instruction-injection
# patterns inside uploaded documents. Not a substitute for the structural
# prompt-isolation done in agents/support_agent.py — see README security notes.
_SUSPICIOUS_PATTERNS = [
    re.compile(r"ignore (all|previous|prior) instructions", re.IGNORECASE),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
    re.compile(r"disregard (the )?(above|prior)", re.IGNORECASE),
]


class ValidationError(Exception):
    """Raised when user-supplied input or a file fails validation."""


def sanitize_filename(filename: str) -> str:
    """Strip path components to prevent path traversal; keep only the basename."""
    name = PurePosixPath(filename).name
    name = re.sub(r"[^A-Za-z0-9_.\-]", "_", name)
    if not name:
        raise ValidationError("Filename is invalid after sanitization.")
    return name


def validate_file_extension(filename: str) -> str:
    ext = PurePosixPath(filename.lower()).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def validate_file_size(size_bytes: int) -> None:
    settings = get_settings()
    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty.")
    if size_bytes > settings.max_upload_bytes:
        raise ValidationError(
            f"File exceeds max allowed size of {settings.max_upload_mb} MB."
        )


def validate_chat_message(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        raise ValidationError("Message cannot be empty.")
    if len(cleaned) > 4000:
        raise ValidationError("Message is too long (max 4000 characters).")
    return cleaned


def flag_suspicious_content(text: str) -> list[str]:
    """Return a list of matched suspicious-pattern descriptions found in document text.

    This does not block ingestion — it only surfaces a warning to the admin and
    is logged, because the real defense is prompt isolation at generation time.
    """
    findings = []
    for pattern in _SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            findings.append(pattern.pattern)
    return findings
