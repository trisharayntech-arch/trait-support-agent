"""Admin endpoints: knowledge-base document management and escalation review.

All routes here are gated by the verify_admin_key dependency (see utils/security.py).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from database import db
from models.schemas import (
    DocumentInfo,
    DocumentUploadResponse,
    EscalationResponse,
    TicketResponse,
    TicketStatusUpdate,
)
from services.document_service import DocumentServiceError, ingest_document, remove_document
from utils.logger import get_logger
from utils.security import verify_admin_key

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin_key)])


@router.post("/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    file_bytes = await file.read()

    try:
        result = ingest_document(file.filename, file_bytes)
    except DocumentServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during document upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while processing the document.",
        ) from exc

    message = "Document indexed successfully."
    if result.get("suspicious_patterns_flagged"):
        message += " Note: content flagged for review (possible instruction-like text in document)."

    return DocumentUploadResponse(
        document=DocumentInfo(
            id=result["id"],
            filename=result["filename"],
            file_type=result["file_type"],
            chunk_count=result["chunk_count"],
            uploaded_at=_now_placeholder(),
            status=result["status"],
        ),
        message=message,
    )


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    rows = db.list_documents()
    return [
        DocumentInfo(
            id=r["id"],
            filename=r["filename"],
            file_type=r["file_type"],
            chunk_count=r["chunk_count"],
            uploaded_at=r["uploaded_at"],
            status=r["status"],
        )
        for r in rows
    ]


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_document(document_id: int) -> None:
    remove_document(document_id)


@router.get("/escalations", response_model=list[EscalationResponse])
def list_escalations(status_filter: str | None = None) -> list[EscalationResponse]:
    rows = db.list_escalations(status=status_filter)
    output = []
    for r in rows:
        last_message = db.get_last_user_message(r["session_id"])
        output.append(
            EscalationResponse(
                id=r["id"],
                session_id=r["session_id"],
                reason=r["reason"],
                status=r["status"],
                created_at=r["created_at"],
                last_customer_message=last_message,
            )
        )
    return output


@router.post("/escalations/{escalation_id}/resolve", status_code=status.HTTP_200_OK)
def resolve_escalation(escalation_id: int) -> dict:
    db.update_escalation_status(escalation_id, "resolved")
    return {"id": escalation_id, "status": "resolved"}


def _now_placeholder():
    # uploaded_at is set by the DB default; for the immediate response we
    # return "now" for display purposes only (actual value is in list_documents).
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)

@router.get("/tickets", response_model=list[TicketResponse])
def list_tickets(status_filter: str | None = None) -> list[TicketResponse]:
    rows = db.list_tickets(status=status_filter)

    return [
        TicketResponse(
            id=row["id"],
            session_id=row["session_id"],
            customer_message=row["customer_message"],
            category=row["category"],
            priority=row["priority"],
            assigned_team=row["assigned_team"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int) -> TicketResponse:
    row = db.get_ticket(ticket_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    return TicketResponse(
        id=row["id"],
        session_id=row["session_id"],
        customer_message=row["customer_message"],
        category=row["category"],
        priority=row["priority"],
        assigned_team=row["assigned_team"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch(
    "/tickets/{ticket_id}/status",
    response_model=TicketResponse,
)
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
) -> TicketResponse:
    row = db.get_ticket(ticket_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    db.update_ticket_status(ticket_id, payload.status.value)

    updated = db.get_ticket(ticket_id)

    return TicketResponse(
        id=updated["id"],
        session_id=updated["session_id"],
        customer_message=updated["customer_message"],
        category=updated["category"],
        priority=updated["priority"],
        assigned_team=updated["assigned_team"],
        status=updated["status"],
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
@router.get("/analytics")
def get_analytics() -> dict:
    return db.get_ticket_analytics()

@router.get("/common-issues")
def get_common_issues(limit: int = 10) -> list[dict]:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100.",
        )

    return db.get_common_issues(limit=limit)

@router.get("/kb-improvement")
def get_kb_improvement(limit: int = 10) -> list[dict]:
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100.",
        )

    return db.get_kb_improvement_candidates(limit=limit)