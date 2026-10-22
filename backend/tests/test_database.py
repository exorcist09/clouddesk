"""Tests for database connection and schema initialization."""
from __future__ import annotations

import pytest
import pytest_asyncio
import sqlalchemy as sa


@pytest.mark.asyncio
async def test_database_connects(test_engine):
    """DB is reachable and returns a result."""
    async with test_engine.connect() as conn:
        result = await conn.execute(sa.text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_pgvector_extension_enabled(test_engine):
    """pgvector extension must be installed."""
    async with test_engine.connect() as conn:
        result = await conn.execute(
            sa.text(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
        )
        row = result.fetchone()
    assert row is not None, "pgvector extension not installed"


@pytest.mark.asyncio
async def test_all_tables_exist(test_engine):
    """All expected tables must be present after schema creation."""
    expected = {
        "customers",
        "payments",
        "tickets",
        "knowledge_articles",
        "known_bugs",
        "outages",
        "review_decisions",
    }
    async with test_engine.connect() as conn:
        result = await conn.execute(
            sa.text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
        )
        existing = {row[0] for row in result.fetchall()}
    missing = expected - existing
    assert not missing, f"Missing tables: {missing}"


@pytest.mark.asyncio
async def test_customer_email_unique_constraint(db_session):
    """Duplicate customer emails must be rejected."""
    from app.models.customer import Customer

    c1 = Customer(name="Alice", email="dup@test.com")
    c2 = Customer(name="Bob", email="dup@test.com")
    db_session.add(c1)
    await db_session.flush()

    db_session.add(c2)
    with pytest.raises(Exception):  # IntegrityError
        await db_session.flush()


@pytest.mark.asyncio
async def test_review_decision_unique_per_ticket(db_session):
    """A second review decision on the same ticket must be rejected."""
    from app.models.customer import Customer
    from app.models.ticket import Ticket, TicketStatus
    from app.models.review_decision import ReviewDecision, ReviewDecisionType

    cust = Customer(name="Test", email="unique-rd@test.com")
    db_session.add(cust)
    await db_session.flush()

    ticket = Ticket(
        customer_email="unique-rd@test.com",
        subject="Test",
        body="body",
        status=TicketStatus.PENDING_REVIEW,
    )
    db_session.add(ticket)
    await db_session.flush()

    rd1 = ReviewDecision(
        ticket_id=ticket.id, decision=ReviewDecisionType.APPROVE
    )
    db_session.add(rd1)
    await db_session.flush()

    rd2 = ReviewDecision(
        ticket_id=ticket.id, decision=ReviewDecisionType.REJECT
    )
    db_session.add(rd2)
    with pytest.raises(Exception):  # IntegrityError — unique constraint
        await db_session.flush()
