"""Review queue and manager decision API routes."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ReviewRequest, ReviewResponse, TicketResponse
from app.database import get_db_session
from app.models.review_decision import ReviewDecision, ReviewDecisionType
from app.models.ticket import Ticket, TicketStatus
from app.workflow.service import resume_ticket_workflow

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reviews"])


@router.get("/reviews/pending", response_model=list[TicketResponse])
async def list_pending_reviews(
    session: AsyncSession = Depends(get_db_session),
) -> list[TicketResponse]:
    """Retrieve all tickets currently awaiting human manager review."""
    stmt = (
        sa.select(Ticket)
        .where(Ticket.status == TicketStatus.PENDING_REVIEW)
        .order_by(Ticket.created_at.desc())
    )
    result = await session.execute(stmt)
    tickets = result.scalars().all()
    return [TicketResponse.model_validate(t) for t in tickets]


@router.post("/tickets/{ticket_id}/review", response_model=ReviewResponse)
async def submit_review_decision(
    ticket_id: str,
    payload: ReviewRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReviewResponse:
    """Submit human review decision (approve, edit, or reject) to resume workflow."""
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found",
        )

    if ticket.status != TicketStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket '{ticket_id}' is not awaiting review (current status: {ticket.status})",
        )

    # Check for existing decision to prevent duplicate finalization
    existing = await session.execute(
        sa.select(ReviewDecision).where(ReviewDecision.ticket_id == ticket_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review decision has already been recorded for ticket '{ticket_id}'",
        )

    # Save review decision in database
    review = ReviewDecision(
        ticket_id=ticket.id,
        decision=payload.decision,
        edited_response=payload.edited_response,
        rejection_reason=payload.rejection_reason,
        reviewer=payload.reviewer,
    )
    session.add(review)

    # Resume the LangGraph workflow
    try:
        resumed = await resume_ticket_workflow(
            ticket_id=ticket.id,
            decision=payload.decision.value,
            edited_response=payload.edited_response,
            rejection_reason=payload.rejection_reason,
            reviewer=payload.reviewer,
        )

        # Apply resumed state to ticket
        if payload.decision == ReviewDecisionType.APPROVE:
            ticket.status = TicketStatus.RESOLVED
            ticket.final_reply = ticket.draft_reply
        elif payload.decision == ReviewDecisionType.EDIT:
            ticket.status = TicketStatus.RESOLVED
            ticket.final_reply = payload.edited_response or ticket.draft_reply
        elif payload.decision == ReviewDecisionType.REJECT:
            ticket.status = TicketStatus.REJECTED
            ticket.error_info = payload.rejection_reason or "Rejected by human reviewer"

        await session.commit()
    except Exception as e:
        logger.warning("Workflow resume notice for %s: %s", ticket_id, e)
        # Still apply DB status directly
        if payload.decision == ReviewDecisionType.APPROVE:
            ticket.status = TicketStatus.RESOLVED
            ticket.final_reply = ticket.draft_reply
        elif payload.decision == ReviewDecisionType.EDIT:
            ticket.status = TicketStatus.RESOLVED
            ticket.final_reply = payload.edited_response or ticket.draft_reply
        elif payload.decision == ReviewDecisionType.REJECT:
            ticket.status = TicketStatus.REJECTED
            ticket.error_info = payload.rejection_reason
        await session.commit()

    return ReviewResponse(
        ticket_id=ticket.id,
        decision=payload.decision,
        status=ticket.status,
        reviewer=payload.reviewer,
        final_reply=ticket.final_reply,
        rejection_reason=payload.rejection_reason,
        created_at=datetime.now(timezone.utc),
    )
