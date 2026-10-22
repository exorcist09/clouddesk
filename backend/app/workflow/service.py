"""Background workflow execution and resume service."""
from __future__ import annotations

import json
import logging
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import sqlalchemy as sa

from app.database import get_session_factory
from app.models.ticket import Ticket, TicketDomain, TicketStatus
from app.workflow.graph import create_support_graph

logger = logging.getLogger(__name__)

# Shared workflow checkpointer across API requests
_shared_checkpointer = MemorySaver()
_support_graph = create_support_graph(checkpointer=_shared_checkpointer)


def get_support_graph():
    """Return the compiled support workflow graph."""
    return _support_graph


async def run_ticket_workflow(ticket_id: str) -> None:
    """Execute LangGraph ticket workflow in background."""
    factory = get_session_factory()

    async with factory() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            logger.error("Ticket %s not found for workflow run", ticket_id)
            return

        ticket.status = TicketStatus.PROCESSING
        ticket.thread_id = ticket_id
        await session.commit()

        initial_state = {
            "ticket_id": ticket.id,
            "customer_id": ticket.customer_id,
            "customer_email": ticket.customer_email,
            "subject": ticket.subject,
            "body": ticket.body,
        }

    config = {"configurable": {"thread_id": ticket_id}}

    try:
        graph = get_support_graph()
        await graph.ainvoke(initial_state, config=config)

        # Inspect state after run
        state_snapshot = graph.get_state(config)
        values = state_snapshot.values

        async with factory() as session:
            t = await session.get(Ticket, ticket_id)
            if not t:
                return

            # Update classification
            domain_val = values.get("domain")
            if domain_val and domain_val in TicketDomain.__members__:
                t.domain = TicketDomain[domain_val]
            t.confidence = values.get("confidence")
            t.classification_explanation = values.get("classification_explanation")

            # Update specialist results & draft
            if values.get("specialist_results"):
                t.specialist_results = json.dumps(values["specialist_results"], default=str)
            draft = values.get("draft") or {}
            t.draft_reply = draft.get("reply_text")
            t.escalation_required = bool(values.get("escalation_required", False))
            t.escalation_reason = values.get("escalation_reason")

            # If waiting for review (interrupted)
            if "prepare_for_review" in state_snapshot.next:
                t.status = TicketStatus.PENDING_REVIEW
                t.workflow_stage = "prepare_for_review"
            elif values.get("status") == "RESOLVED":
                t.status = TicketStatus.RESOLVED
                t.workflow_stage = "auto_resolve"
                t.final_reply = values.get("final_reply")
            else:
                t.status = TicketStatus.RESOLVED
                t.final_reply = values.get("final_reply") or t.draft_reply

            await session.commit()
    except Exception as e:
        logger.exception("Error executing ticket workflow for %s: %s", ticket_id, e)
        async with factory() as session:
            t = await session.get(Ticket, ticket_id)
            if t:
                t.status = TicketStatus.FAILED
                t.error_info = str(e)
                await session.commit()


async def resume_ticket_workflow(
    ticket_id: str,
    decision: str,
    edited_response: str | None = None,
    rejection_reason: str | None = None,
    reviewer: str = "manager",
) -> dict[str, Any]:
    """Resume an interrupted workflow with human review decision."""
    config = {"configurable": {"thread_id": ticket_id}}
    graph = get_support_graph()

    resume_payload = {
        "decision": decision,
        "edited_response": edited_response,
        "rejection_reason": rejection_reason,
        "reviewer": reviewer,
    }

    resumed_output = await graph.ainvoke(
        Command(resume=resume_payload),
        config=config,
    )
    return resumed_output
