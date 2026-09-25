"""Pydantic schemas used across the API boundary (requests/responses)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SupportChannel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    OTHER = "other"


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=4000)
    channel: SupportChannel = SupportChannel.WEB

    @field_validator("message")
    @classmethod
    def strip_and_check(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("message cannot be empty or whitespace only")
        return cleaned


class SourceChunk(BaseModel):
    document_name: str
    chunk_preview: str
    similarity_score: float


class ChatResponse(BaseModel):
    session_id: str
    channel: SupportChannel
    answer: str
    confidence_score: float
    is_confident: bool
    sources: list[SourceChunk] = Field(default_factory=list)
    escalation_suggested: bool
    escalation_id: int | None = None


class EscalationStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class EscalationCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    reason: str = Field(default="Customer requested human assistance", max_length=1000)


class EscalationResponse(BaseModel):
    id: int
    session_id: str
    reason: str
    status: EscalationStatus
    created_at: datetime
    last_customer_message: str | None = None


class DocumentInfo(BaseModel):
    id: int
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: datetime
    status: str


class DocumentUploadResponse(BaseModel):
    document: DocumentInfo
    message: str


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime


class ConversationHistory(BaseModel):
    session_id: str
    messages: list[ConversationMessage]

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketResponse(BaseModel):
    id: int
    session_id: str
    customer_message: str
    category: str
    priority: TicketPriority
    assigned_team: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime


class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class FeedbackRating(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class FeedbackCreateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: int
    session_id: str
    rating: FeedbackRating
    comment: str | None = None
    created_at: datetime

class SupportChannel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    OTHER = "other"