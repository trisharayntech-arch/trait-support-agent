"""
Lightweight SQLite access layer.

Deliberately not using a heavy ORM: the schema is small and stable, and a thin
repository layer keeps this easy to later swap for Postgres in the broader
TRAIT AI Agent Platform without dragging along ORM-specific assumptions.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config.settings import get_settings


def _row_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    Path(settings.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_db_path)
    conn.row_factory = _row_factory
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(schema_sql)


# --- Documents ---

def insert_document(filename: str, file_type: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO documents (filename, file_type, status) VALUES (?, ?, 'processing')",
            (filename, file_type),
        )
        return cur.lastrowid


def update_document_status(document_id: int, status: str, chunk_count: int = 0) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?",
            (status, chunk_count, document_id),
        )


def list_documents() -> list[dict]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
        return cur.fetchall()


def delete_document(document_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))


# --- Conversations ---

def insert_message(session_id: str, role: str, content: str, confidence_score: float | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content, confidence_score) VALUES (?, ?, ?, ?)",
            (session_id, role, content, confidence_score),
        )


def get_conversation_history(session_id: str, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT role, content, created_at FROM conversations "
            "WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        )
        return cur.fetchall()


def get_last_user_message(session_id: str) -> str | None:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT content FROM conversations WHERE session_id = ? AND role = 'user' "
            "ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        return row["content"] if row else None


# --- Escalations ---

def insert_escalation(session_id: str, reason: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO escalations (session_id, reason) VALUES (?, ?)",
            (session_id, reason),
        )
        return cur.lastrowid


def list_escalations(status: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if status:
            cur = conn.execute(
                "SELECT * FROM escalations WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            cur = conn.execute("SELECT * FROM escalations ORDER BY created_at DESC")
        return cur.fetchall()


def update_escalation_status(escalation_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE escalations SET status = ? WHERE id = ?", (status, escalation_id))

# --- Tickets ---

def create_ticket(
    session_id: str,
    customer_message: str,
    category: str = "general",
    priority: str = "medium",
    assigned_team: str = "General Support",
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO tickets
            (session_id, customer_message, category, priority, assigned_team)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                customer_message,
                category,
                priority,
                assigned_team,
            ),
        )
        return cur.lastrowid


def list_tickets(status: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if status:
            cur = conn.execute(
                """
                SELECT *
                FROM tickets
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status,),
            )
        else:
            cur = conn.execute(
                """
                SELECT *
                FROM tickets
                ORDER BY created_at DESC
                """
            )

        return cur.fetchall()


def get_ticket(ticket_id: int) -> dict | None:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM tickets WHERE id = ?",
            (ticket_id,),
        )
        return cur.fetchone()


def update_ticket_status(ticket_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tickets
            SET status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (status, ticket_id),
        )

# --- Customer Feedback ---

def create_feedback(
    session_id: str,
    rating: str,
    comment: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO feedback (session_id, rating, comment)
            VALUES (?, ?, ?)
            """,
            (session_id, rating, comment),
        )
        return cur.lastrowid


def list_feedback(
    rating: str | None = None,
) -> list[dict]:
    with get_connection() as conn:
        if rating:
            cur = conn.execute(
                """
                SELECT *
                FROM feedback
                WHERE rating = ?
                ORDER BY created_at DESC
                """,
                (rating,),
            )
        else:
            cur = conn.execute(
                """
                SELECT *
                FROM feedback
                ORDER BY created_at DESC
                """
            )

        return cur.fetchall()

# --- Support Analytics ---

def get_ticket_analytics() -> dict:
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS count FROM tickets"
        ).fetchone()["count"]

        open_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'open'
            """
        ).fetchone()["count"]

        in_progress = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'in_progress'
            """
        ).fetchone()["count"]

        resolved = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'resolved'
            """
        ).fetchone()["count"]

        closed = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tickets
            WHERE status = 'closed'
            """
        ).fetchone()["count"]

        by_category = conn.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM tickets
            GROUP BY category
            ORDER BY count DESC
            """
        ).fetchall()

        by_priority = conn.execute(
            """
            SELECT priority, COUNT(*) AS count
            FROM tickets
            GROUP BY priority
            ORDER BY count DESC
            """
        ).fetchall()

        return {
            "total_tickets": total,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress,
            "resolved_tickets": resolved,
            "closed_tickets": closed,
            "by_category": [
                {
                    "category": row["category"],
                    "count": row["count"],
                }
                for row in by_category
            ],
            "by_priority": [
                {
                    "priority": row["priority"],
                    "count": row["count"],
                }
                for row in by_priority
            ],
        }

# --- Common Issue Analysis ---

def get_common_issues(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                category,
                COUNT(*) AS count
            FROM tickets
            GROUP BY category
            ORDER BY count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "category": row["category"],
                "count": row["count"],
            }
            for row in rows
        ]

# --- Knowledge Base Improvement ---

def get_kb_improvement_candidates(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                customer_message,
                category,
                priority,
                created_at
            FROM tickets
            WHERE category = 'general'
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            {
                "customer_message": row["customer_message"],
                "category": row["category"],
                "priority": row["priority"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]