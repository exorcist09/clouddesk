"""Tickets API endpoints."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    TicketCreateRequest,
    TicketListResponse,
    TicketReplyResponse,
    TicketResponse,
    TicketStatusResponse,
)
from app.database import get_db_session
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketDomain, TicketStatus
from app.workflow.service import run_ticket_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
) -> TicketResponse:
    """Create a support ticket and initiate background processing."""
    customer_id = payload.customer_id

    # Auto-link customer by email if customer_id not explicitly passed
    if not customer_id:
        cust_query = sa.select(Customer).where(Customer.email == payload.customer_email)
        cust_res = await session.execute(cust_query)
        customer = cust_res.scalar_one_or_none()
        if customer:
            customer_id = customer.id

    ticket = Ticket(
        customer_email=payload.customer_email,
        customer_name=payload.customer_name,
        customer_id=customer_id,
        subject=payload.subject,
        body=payload.body,
        status=TicketStatus.PENDING,
    )
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    # Launch background workflow
    background_tasks.add_task(run_ticket_workflow, ticket.id)

    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    domain_filter: Optional[TicketDomain] = Query(None, alias="domain"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> TicketListResponse:
    """List tickets with optional status/domain filters and pagination."""
    stmt = sa.select(Ticket)
    count_stmt = sa.select(sa.func.count(Ticket.id))

    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
        count_stmt = count_stmt.where(Ticket.status == status_filter)
    if domain_filter:
        stmt = stmt.where(Ticket.domain == domain_filter)
        count_stmt = count_stmt.where(Ticket.domain == domain_filter)

    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    tickets = result.scalars().all()

    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> TicketResponse:
    """Get full details of a specific ticket."""
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found",
        )
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}/status", response_model=TicketStatusResponse)
async def get_ticket_status(
    ticket_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> TicketStatusResponse:
    """Get lightweight status and workflow stage for a ticket."""
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found",
        )
    return TicketStatusResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        workflow_stage=ticket.workflow_stage,
        escalation_required=ticket.escalation_required,
        escalation_reason=ticket.escalation_reason,
    )


@router.get("/{ticket_id}/reply", response_model=TicketReplyResponse)
async def get_ticket_reply(
    ticket_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> TicketReplyResponse:
    """Get final resolved reply for a ticket."""
    ticket = await session.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found",
        )
    return TicketReplyResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        final_reply=ticket.final_reply,
    )
