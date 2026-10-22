"""Graph node functions for CloudDesk support ticket pipeline."""
from __future__ import annotations

import logging
from typing import Any, Optional

from langgraph.types import interrupt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session_factory
from app.tools.account import get_account_details
from app.tools.billing import get_current_subscription, get_customer_billing_history
from app.tools.technical import (
    get_known_bugs,
    get_outage_status,
    search_knowledge_base,
)
from app.workflow.escalation import check_escalation
from app.workflow.llm import classify_ticket, generate_draft
from app.workflow.state import TicketState

logger = logging.getLogger(__name__)


async def classify_ticket_node(state: TicketState) -> dict[str, Any]:
    """Classify ticket into support domain with confidence score."""
    subject = state.get("subject", "")
    body = state.get("body", "")

    settings = get_settings()
    result = await classify_ticket(subject, body)
    is_low_conf = result.confidence < settings.confidence_threshold

    updates: dict[str, Any] = {
        "domain": result.domain.value,
        "confidence": result.confidence,
        "classification_explanation": result.explanation,
        "status": "PROCESSING",
    }
    if is_low_conf:
        updates["escalation_required"] = True
        updates["escalation_reason"] = (
            f"Low classification confidence: {result.confidence:.2f} "
            f"(threshold: {settings.confidence_threshold:.2f})"
        )

    return updates


def check_confidence_edge(state: TicketState) -> str:
    """Conditional router based on classification confidence threshold."""
    settings = get_settings()
    conf = state.get("confidence", 0.0) or 0.0
    if conf < settings.confidence_threshold:
        return "escalate"
    return "route"


def route_to_specialist_edge(state: TicketState) -> str:
    """Route ticket to appropriate domain specialist node."""
    domain = (state.get("domain") or "").upper()
    if domain == "BILLING":
        return "billing"
    if domain == "TECHNICAL_SUPPORT":
        return "technical"
    if domain == "ACCOUNT_MANAGEMENT":
        return "account"
    return "escalate"


async def billing_specialist_node(state: TicketState) -> dict[str, Any]:
    """Retrieve billing history and generate draft reply."""
    customer_id = state.get("customer_id")
    subject = state.get("subject", "")
    body = state.get("body", "")

    specialist_data: dict[str, Any] = {"payments": [], "subscription": None}

    factory = get_session_factory()
    async with factory() as session:
        if customer_id:
            specialist_data["payments"] = await get_customer_billing_history(customer_id, session)
            specialist_data["subscription"] = await get_current_subscription(customer_id, session)

    draft = await generate_draft("BILLING", subject, body, specialist_data)
    return {
        "specialist_results": specialist_data,
        "draft": draft.model_dump(),
    }


async def technical_specialist_node(state: TicketState) -> dict[str, Any]:
    """Search knowledge base, known bugs, and outages; generate draft."""
    subject = state.get("subject", "")
    body = state.get("body", "")
    query = f"{subject} {body}"

    specialist_data: dict[str, Any] = {"articles": [], "bugs": [], "outages": []}

    factory = get_session_factory()
    async with factory() as session:
        specialist_data["bugs"] = await get_known_bugs(subject, session)
        specialist_data["outages"] = await get_outage_status("all", session)
        specialist_data["articles"] = await search_knowledge_base(query, session, limit=3)

    draft = await generate_draft("TECHNICAL_SUPPORT", subject, body, specialist_data)
    return {
        "specialist_results": specialist_data,
        "draft": draft.model_dump(),
    }


async def account_specialist_node(state: TicketState) -> dict[str, Any]:
    """Fetch customer profile, 2FA info, and account articles; generate draft."""
    customer_id = state.get("customer_id")
    subject = state.get("subject", "")
    body = state.get("body", "")
    query = f"{subject} {body}"

    specialist_data: dict[str, Any] = {"account": None, "articles": []}

    factory = get_session_factory()
    async with factory() as session:
        if customer_id:
            specialist_data["account"] = await get_account_details(customer_id, session)
        specialist_data["articles"] = await search_knowledge_base(
            query, session, category="account_management", limit=3
        )

    draft = await generate_draft("ACCOUNT_MANAGEMENT", subject, body, specialist_data)
    return {
        "specialist_results": specialist_data,
        "draft": draft.model_dump(),
    }


def apply_escalation_rules_node(state: TicketState) -> dict[str, Any]:
    """Enforce deterministic business escalation rules."""
    settings = get_settings()
    domain = state.get("domain", "") or ""
    subject = state.get("subject", "") or ""
    body = state.get("body", "") or ""
    confidence = state.get("confidence", 1.0) or 1.0
    specialist_results = state.get("specialist_results")

    # If the LLM draft itself asked for escalation, track it
    draft = state.get("draft") or {}
    if draft.get("requires_escalation"):
        return {
            "escalation_required": True,
            "escalation_reason": draft.get("escalation_reason") or "Specialist flagged for review",
        }

    is_esc, reason = check_escalation(
        domain=domain,
        subject=subject,
        body=body,
        confidence=confidence,
        confidence_threshold=settings.confidence_threshold,
        specialist_results=specialist_results,
    )
    return {
        "escalation_required": is_esc,
        "escalation_reason": reason,
    }


def check_escalation_edge(state: TicketState) -> str:
    """Conditional router checking if human review is needed."""
    if state.get("escalation_required"):
        return "escalate"
    return "resolve"


def prepare_for_review_node(state: TicketState) -> dict[str, Any]:
    """Set status to PENDING_REVIEW and pause execution for human manager."""
    # Trigger LangGraph interrupt for human-in-the-loop review
    decision = interrupt({
        "ticket_id": state.get("ticket_id"),
        "reason": state.get("escalation_reason"),
        "draft": state.get("draft"),
    })
    return {
        "status": "PENDING_REVIEW",
        "review_decision": decision,
    }


def auto_resolve_node(state: TicketState) -> dict[str, Any]:
    """Auto-resolve ticket with final reply from approved draft."""
    draft = state.get("draft") or {}
    reply = draft.get("reply_text", "")
    return {
        "status": "RESOLVED",
        "final_reply": reply,
    }


def handle_review_decision_node(state: TicketState) -> dict[str, Any]:
    """Process human review decision after resumption."""
    decision = state.get("review_decision") or {}
    dec_type = (decision.get("decision") or "APPROVE").upper()

    draft = state.get("draft") or {}
    if dec_type == "APPROVE":
        return {
            "status": "RESOLVED",
            "final_reply": draft.get("reply_text", ""),
        }
    elif dec_type == "EDIT":
        edited = decision.get("edited_response") or draft.get("reply_text", "")
        return {
            "status": "RESOLVED",
            "final_reply": edited,
        }
    elif dec_type == "REJECT":
        reason = decision.get("rejection_reason") or "Rejected by human reviewer"
        return {
            "status": "REJECTED",
            "error_info": reason,
        }

    return {"status": "RESOLVED"}
