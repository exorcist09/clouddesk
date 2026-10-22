"""Tests for human review queue and review decision API routes."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.ticket import Ticket, TicketStatus


@pytest.mark.asyncio
async def test_list_pending_reviews(client: AsyncClient, db_session):
    """GET /api/reviews/pending returns only tickets in PENDING_REVIEW."""
    t_pending = Ticket(
        customer_email="rev1@test.com",
        subject="Pending review ticket",
        body="Body",
        status=TicketStatus.PENDING_REVIEW,
        escalation_required=True,
        escalation_reason="Refund requested",
        draft_reply="We will refund you",
    )
    t_resolved = Ticket(
        customer_email="rev2@test.com",
        subject="Resolved ticket",
        body="Body",
        status=TicketStatus.RESOLVED,
    )
    db_session.add(t_pending)
    db_session.add(t_resolved)
    await db_session.flush()

    resp = await client.get("/api/reviews/pending")
    assert resp.status_code == 200
    data = resp.json()
    ids = [item["id"] for item in data]
    assert str(t_pending.id) in ids
    assert str(t_resolved.id) not in ids


@pytest.mark.asyncio
async def test_submit_review_approve(client: AsyncClient, db_session):
    """POST /api/tickets/{id}/review with APPROVE finalizes ticket."""
    t = Ticket(
        customer_email="approve@test.com",
        subject="Approve test",
        body="Body",
        status=TicketStatus.PENDING_REVIEW,
        draft_reply="Draft reply text",
    )
    db_session.add(t)
    await db_session.flush()

    resp = await client.post(
        f"/api/tickets/{t.id}/review",
        json={"decision": "APPROVE", "reviewer": "manager_carol"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RESOLVED"
    assert data["final_reply"] == "Draft reply text"


@pytest.mark.asyncio
async def test_submit_review_edit(client: AsyncClient, db_session):
    """POST /api/tickets/{id}/review with EDIT finalizes ticket with edited text."""
    t = Ticket(
        customer_email="edit@test.com",
        subject="Edit test",
        body="Body",
        status=TicketStatus.PENDING_REVIEW,
        draft_reply="Original draft",
    )
    db_session.add(t)
    await db_session.flush()

    resp = await client.post(
        f"/api/tickets/{t.id}/review",
        json={
            "decision": "EDIT",
            "edited_response": "Manager edited response text",
            "reviewer": "manager_dan",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RESOLVED"
    assert data["final_reply"] == "Manager edited response text"


@pytest.mark.asyncio
async def test_submit_review_reject(client: AsyncClient, db_session):
    """POST /api/tickets/{id}/review with REJECT marks ticket as REJECTED."""
    t = Ticket(
        customer_email="reject@test.com",
        subject="Reject test",
        body="Body",
        status=TicketStatus.PENDING_REVIEW,
        draft_reply="Draft",
    )
    db_session.add(t)
    await db_session.flush()

    resp = await client.post(
        f"/api/tickets/{t.id}/review",
        json={
            "decision": "REJECT",
            "rejection_reason": "Policy violation",
            "reviewer": "manager_dan",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_duplicate_review_conflict(client: AsyncClient, db_session):
    """Submitting review twice returns 409 Conflict."""
    t = Ticket(
        customer_email="dup_rev@test.com",
        subject="Dup review test",
        body="Body",
        status=TicketStatus.PENDING_REVIEW,
        draft_reply="Draft",
    )
    db_session.add(t)
    await db_session.flush()

    # First review succeeds
    r1 = await client.post(
        f"/api/tickets/{t.id}/review",
        json={"decision": "APPROVE"},
    )
    assert r1.status_code == 200

    # Second review must fail with 409 or 400
    r2 = await client.post(
        f"/api/tickets/{t.id}/review",
        json={"decision": "APPROVE"},
    )
    assert r2.status_code in (400, 409)
