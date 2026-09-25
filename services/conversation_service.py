"""Conversation history persistence service."""
from __future__ import annotations

from database import db


def log_user_message(session_id: str, content: str) -> None:
    db.insert_message(session_id=session_id, role="user", content=content)


def log_assistant_message(session_id: str, content: str, confidence_score: float) -> None:
    db.insert_message(
        session_id=session_id, role="assistant", content=content, confidence_score=confidence_score
    )


def get_history(session_id: str) -> list[dict]:
    return db.get_conversation_history(session_id)
