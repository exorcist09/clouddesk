"""Pydantic API request and response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.review_decision import ReviewDecisionType
from app.models.ticket import TicketDomain, TicketStatus


class TicketCreateRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: Optional[str] = None
    customer_email: str
    customer_name: Optional[str] = None
    subject: str
    body: str
    domain: Optional[TicketDomain] = None
    confidence: Optional[float] = None
    classification_explanation: Optional[str] = None
    status: TicketStatus
    workflow_stage: Optional[str] = None
    specialist_results: Optional[str] = None
    draft_reply: Optional[str] = None
    final_reply: Optional[str] = None
    escalation_required: bool = False
    escalation_reason: Optional[str] = None
    error_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int


class TicketStatusResponse(BaseModel):
    ticket_id: str
    status: TicketStatus
    workflow_stage: Optional[str] = None
    escalation_required: bool = False
    escalation_reason: Optional[str] = None


class TicketReplyResponse(BaseModel):
    ticket_id: str
    status: TicketStatus
    final_reply: Optional[str] = None


class ReviewRequest(BaseModel):
    decision: ReviewDecisionType
    edited_response: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewer: str = "manager"


class ReviewResponse(BaseModel):
    ticket_id: str
    decision: ReviewDecisionType
    status: TicketStatus
    reviewer: str
    final_reply: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
