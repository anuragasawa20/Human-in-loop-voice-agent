"""
Pydantic models for request/response validation.

Design Decision:
- Use Pydantic for automatic validation and OpenAPI docs
- Clear separation between Create, Update, and Response models
- Enums for status to prevent invalid states
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    """
    Request lifecycle states.

    State Machine:
    PENDING → IN_PROGRESS → RESOLVED
        ↓                      ↓
    TIMEOUT              TIMEOUT
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"


class Priority(str, Enum):
    """Request priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class KBSource(str, Enum):
    """Knowledge base entry sources."""

    INITIAL_PROMPT = "initial_prompt"
    SUPERVISOR_ANSWER = "supervisor_answer"
    MANUAL_ENTRY = "manual_entry"


# Help Request Models
class HelpRequestCreate(BaseModel):
    """Data required to create a new help request."""

    caller_id: str = Field(..., description="Phone number or session ID")
    caller_name: Optional[str] = Field(None, description="Caller's name if provided")
    question: str = Field(..., min_length=1, description="The question being asked")
    context: str = Field(..., description="Conversation context")
    call_session_id: str = Field(..., description="Associated call session")
    priority: Priority = Field(default=Priority.MEDIUM, description="Request priority")


class HelpRequestUpdate(BaseModel):
    """Data for updating a help request (supervisor response)."""

    supervisor_response: str = Field(
        ..., min_length=1, description="Answer from supervisor"
    )
    supervisor_id: str = Field(..., description="ID of the supervisor responding")


class HelpRequestResponse(BaseModel):
    """Complete help request data for responses."""

    id: str
    caller_id: str
    caller_name: Optional[str]
    question: str
    context: str
    call_session_id: str
    status: RequestStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    timeout_at: datetime
    resolved_at: Optional[datetime]
    supervisor_response: Optional[str]
    supervisor_id: Optional[str]

    class Config:
        from_attributes = True


# Knowledge Base Models
class KnowledgeEntryCreate(BaseModel):
    """Data required to create a KB entry."""

    question: str = Field(..., min_length=1, description="The question")
    answer: str = Field(..., min_length=1, description="The answer")
    category: str = Field(default="general", description="Category")
    confidence: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Confidence score"
    )
    source: KBSource = Field(default=KBSource.MANUAL_ENTRY, description="Entry source")
    source_request_id: Optional[str] = Field(None, description="Source help request ID")


class KnowledgeEntryUpdate(BaseModel):
    """Data for updating a KB entry."""

    answer: Optional[str] = Field(None, min_length=1)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    category: Optional[str] = None


class KnowledgeEntryResponse(BaseModel):
    """Complete KB entry data for responses."""

    id: str
    question: str
    question_normalized: str
    answer: str
    category: str
    confidence: float
    source: str
    source_request_id: Optional[str]
    usage_count: int
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


# Call Session Models
class CallSessionResponse(BaseModel):
    """Call session data for responses."""

    id: str
    caller_id: str
    caller_phone: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    transcript: Optional[str]
    help_requested: bool
    help_request_ids: list[str]
    resolved_during_call: bool
    status: str

    class Config:
        from_attributes = True


# Notification Models
class NotificationRequest(BaseModel):
    """Data for sending a notification."""

    recipient: str = Field(..., description="Phone number or contact")
    message: str = Field(..., min_length=1, description="Notification message")
    request_id: str = Field(..., description="Related help request ID")


# Response Models
class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response."""

    success: bool = False
    error: str
    details: Optional[str] = None
