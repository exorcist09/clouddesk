"""Tests for API error handling and edge cases."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.ticket import Ticket, TicketStatus


@pytest.mark.asyncio
async def test_review_non_pending_ticket_bad_request(client: AsyncClient, db_session):
    """Submitting review for ticket that is already RESOLVED returns 400 Bad Request."""
    t = Ticket(
        customer_email="resolved@test.com",
        subject="Already resolved",
        body="Body",
        status=TicketStatus.RESOLVED,
    )
    db_session.add(t)
    await db_session.flush()

    resp = await client.post(
        f"/api/tickets/{t.id}/review",
        json={"decision": "APPROVE"},
    )
    assert resp.status_code == 400
    assert "not awaiting review" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_review_non_existent_ticket_not_found(client: AsyncClient):
    """Submitting review for non-existent ticket returns 404."""
    resp = await client.post(
        "/api/tickets/00000000-0000-0000-0000-000000000999/review",
        json={"decision": "APPROVE"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """GET /health returns 200 with service ok."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
