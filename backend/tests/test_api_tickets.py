"""Tests for tickets API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.ticket import Ticket, TicketStatus


@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient):
    """POST /api/tickets creates a ticket and returns 201."""
    payload = {
        "customer_email": "testuser@acme.com",
        "customer_name": "Test User",
        "subject": "Question about invoice",
        "body": "Can you please clarify line item 2 on my invoice?",
    }
    resp = await client.post("/api/tickets", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["customer_email"] == "testuser@acme.com"
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_create_ticket_validation_error(client: AsyncClient):
    """POST /api/tickets with invalid email or empty body returns 422."""
    payload = {
        "customer_email": "not-an-email",
        "subject": "",
        "body": "",
    }
    resp = await client.post("/api/tickets", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_ticket_details(client: AsyncClient, db_session):
    """GET /api/tickets/{id} returns ticket details."""
    t = Ticket(
        customer_email="detail@test.com",
        subject="Detail test",
        body="Body test",
        status=TicketStatus.PENDING,
    )
    db_session.add(t)
    await db_session.flush()

    resp = await client.get(f"/api/tickets/{t.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(t.id)
    assert data["customer_email"] == "detail@test.com"


@pytest.mark.asyncio
async def test_get_ticket_not_found(client: AsyncClient):
    """GET /api/tickets/{id} with unknown ID returns 404."""
    resp = await client.get("/api/tickets/00000000-0000-0000-0000-000000000999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_tickets_pagination(client: AsyncClient, db_session):
    """GET /api/tickets lists tickets with pagination."""
    for i in range(3):
        t = Ticket(
            customer_email=f"list{i}@test.com",
            subject=f"Subject {i}",
            body="Body text",
            status=TicketStatus.PENDING,
        )
        db_session.add(t)
    await db_session.flush()

    resp = await client.get("/api/tickets?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tickets"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 3
