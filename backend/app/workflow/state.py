"""LangGraph state definition for customer support tickets."""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class TicketState(TypedDict, total=False):
    ticket_id: str
    customer_id: Optional[str]
    customer_email: str
    subject: str
    body: str

    domain: Optional[str]
    confidence: Optional[float]
    classification_explanation: Optional[str]

    specialist_results: Optional[dict[str, Any]]
    draft: Optional[dict[str, Any]]

    escalation_required: bool
    escalation_reason: Optional[str]

    review_decision: Optional[dict[str, Any]]
    final_reply: Optional[str]

    status: str
    error_info: Optional[str]
    messages: list[dict[str, Any]]
