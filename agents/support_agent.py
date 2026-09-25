"""
Support agent orchestrator.

This is the explicit decision logic for the support agent — written out
directly (rather than hidden inside a framework "chain") so the
retrieve -> confidence-check -> generate -> escalate flow is fully auditable.
This is also the natural extension point for turning this into one agent
within the broader TRAIT AI Agent Platform (e.g., adding tool calls, routing
to specialist agents, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from database import db
from rag.retriever import retrieve
from services.conversation_service import log_assistant_message, log_user_message
from services.llm_service import LLMServiceError, generate_answer
from utils.logger import get_logger

logger = get_logger(__name__)

FALLBACK_MESSAGE = (
    "I don't have enough verified information in our knowledge base to answer that "
    "confidently. I don't want to guess about company policies or details, so I'd "
    "recommend connecting you with a human support agent who can help further."
)

LLM_ERROR_MESSAGE = (
    "I'm having trouble generating a response right now. Please try again shortly, "
    "or request to speak with a human agent."
)


@dataclass
class AgentResponse:
    answer: str
    confidence_score: float
    is_confident: bool
    sources: list[dict] = field(default_factory=list)
    escalation_suggested: bool = False


def handle_customer_message(session_id: str, message: str) -> AgentResponse:
    """Main orchestration entrypoint for a single customer turn."""
    log_user_message(session_id, message)

    retrieval = retrieve(message)

    if not retrieval.is_confident:
        logger.info(
            "Low confidence for session %s (top_score=%.3f) — returning fallback.",
            session_id,
            retrieval.top_score,
        )
        response = AgentResponse(
            answer=FALLBACK_MESSAGE,
            confidence_score=retrieval.top_score,
            is_confident=False,
            sources=[],
            escalation_suggested=True,
        )
        log_assistant_message(session_id, response.answer, response.confidence_score)
        return response

    context_texts = [c["text"] for c in retrieval.chunks]

    try:
        answer = generate_answer(message, context_texts)
    except LLMServiceError as exc:
        logger.error("LLM generation failed for session %s: %s", session_id, exc)
        response = AgentResponse(
            answer=LLM_ERROR_MESSAGE,
            confidence_score=retrieval.top_score,
            is_confident=False,
            sources=[],
            escalation_suggested=True,
        )
        log_assistant_message(session_id, response.answer, response.confidence_score)
        return response

    response = AgentResponse(
        answer=answer,
        confidence_score=retrieval.top_score,
        is_confident=True,
        sources=retrieval.chunks,
        escalation_suggested=False,
    )
    log_assistant_message(session_id, response.answer, response.confidence_score)
    return response


def create_escalation(session_id: str, reason: str) -> int:
    """Create an escalation record for a customer session."""
    return db.insert_escalation(session_id=session_id, reason=reason)
