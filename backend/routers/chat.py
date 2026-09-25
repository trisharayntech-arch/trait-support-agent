"""Customer-facing chat and escalation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from agents.support_agent import create_escalation, handle_customer_message
from database import db
from models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationMessage,
    EscalationCreateRequest,
    EscalationResponse,
    FeedbackCreateRequest,
    FeedbackResponse,
    SourceChunk,
)
from utils.logger import get_logger
from utils.validators import ValidationError, validate_chat_message
from services.issue_classifier import classify_issue

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        message = validate_chat_message(request.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        result = handle_customer_message(request.session_id, message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error in chat handling")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your message.",
        ) from exc

        escalation_id = None

    # Classify the customer's issue so actionable support requests
    # can be routed to the appropriate team.
    classification = classify_issue(message)

    ticket_id = None

    # Create tickets for actionable support categories.
    actionable_categories = {
        "billing_refund",
        "order_delivery",
        "technical_support",
        "account",
        "complaint",
    }

    if classification.category in actionable_categories:
        ticket_id = db.create_ticket(
            session_id=request.session_id,
            customer_message=message,
            category=classification.category,
            priority=classification.priority,
            assigned_team=classification.assigned_team,
        )

    if result.escalation_suggested:
        escalation_id = create_escalation(
            request.session_id,
            reason="Low-confidence answer or generation failure",
        )

    return ChatResponse(
    session_id=request.session_id,
    channel=request.channel,
        answer=result.answer,
        confidence_score=result.confidence_score,
        is_confident=result.is_confident,
        sources=[
            SourceChunk(
                document_name=c["document_name"],
                chunk_preview=c["text"][:200],
                similarity_score=c["similarity_score"],
            )
            for c in result.sources
        ],
        escalation_suggested=result.escalation_suggested,
        escalation_id=escalation_id,
    )


@router.get("/history/{session_id}", response_model=ConversationHistory)
def get_history(session_id: str) -> ConversationHistory:
    rows = db.get_conversation_history(session_id)
    return ConversationHistory(
        session_id=session_id,
        messages=[
            ConversationMessage(role=r["role"], content=r["content"], created_at=r["created_at"])
            for r in rows
        ],
    )


@router.post("/escalate", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
def escalate(request: EscalationCreateRequest) -> EscalationResponse:
    escalation_id = create_escalation(request.session_id, request.reason)
    last_message = db.get_last_user_message(request.session_id)
    rows = db.list_escalations()
    record = next((r for r in rows if r["id"] == escalation_id), None)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Escalation could not be retrieved."
        )
    return EscalationResponse(
        id=record["id"],
        session_id=record["session_id"],
        reason=record["reason"],
        status=record["status"],
        created_at=record["created_at"],
        last_customer_message=last_message,
    )

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(request: FeedbackCreateRequest) -> FeedbackResponse:
    feedback_id = db.create_feedback(
        session_id=request.session_id,
        rating=request.rating.value,
        comment=request.comment,
    )

    rows = db.list_feedback()
    record = next(
        (row for row in rows if row["id"] == feedback_id),
        None,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback could not be retrieved.",
        )

    return FeedbackResponse(
        id=record["id"],
        session_id=record["session_id"],
        rating=record["rating"],
        comment=record["comment"],
        created_at=record["created_at"],
    )
@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(request: FeedbackCreateRequest) -> FeedbackResponse:
    feedback_id = db.create_feedback(
        session_id=request.session_id,
        rating=request.rating.value,
        comment=request.comment,
    )

    rows = db.list_feedback()
    record = next(
        (row for row in rows if row["id"] == feedback_id),
        None,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback could not be retrieved.",
        )

    return FeedbackResponse(
        id=record["id"],
        session_id=record["session_id"],
        rating=record["rating"],
        comment=record["comment"],
        created_at=record["created_at"],
    )