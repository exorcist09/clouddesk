"""Workflow schemas for classification, drafting, and human review."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.models.ticket import TicketDomain
from app.models.review_decision import ReviewDecisionType


class ClassificationResult(BaseModel):
    domain: TicketDomain = Field(description="Classified ticket domain")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score 0.0 to 1.0")
    explanation: str = Field(default="", description="Reasoning for domain classification")


class DraftResponse(BaseModel):
    reply_text: str = Field(description="Drafted response text for customer")
    summary: str = Field(default="", description="Internal summary of resolution")
    sources: list[str] = Field(default_factory=list, description="Knowledge base or tool sources used")
    requires_escalation: bool = Field(default=False, description="Flag indicating human review required")
    escalation_reason: Optional[str] = Field(default=None, description="Trigger reason if escalation required")


class ReviewDecisionInput(BaseModel):
    decision: ReviewDecisionType
    edited_response: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewer: str = "manager"
