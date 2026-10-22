"""Tests for idempotent seed data."""
from __future__ import annotations

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_seed_creates_customers(db_session: AsyncSession):
    """Seed must produce at least 5 customers."""
    from app.seed import seed_all

    await seed_all(db_session)
    result = await db_session.execute(sa.text("SELECT COUNT(*) FROM customers"))
    count = result.scalar()
    assert count >= 5, f"Expected >=5 customers, got {count}"


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session: AsyncSession):
    """Running seed twice must not create duplicate records."""
    from app.seed import seed_all

    await seed_all(db_session)
    count_after_first = (
        await db_session.execute(sa.text("SELECT COUNT(*) FROM customers"))
    ).scalar()

    await seed_all(db_session)
    count_after_second = (
        await db_session.execute(sa.text("SELECT COUNT(*) FROM customers"))
    ).scalar()

    assert count_after_first == count_after_second, (
        "Seed created duplicate records on second run"
    )


@pytest.mark.asyncio
async def test_seed_creates_knowledge_articles(db_session: AsyncSession):
    """Seed must produce at least 8 knowledge articles with embeddings."""
    from app.seed import seed_all

    await seed_all(db_session)
    result = await db_session.execute(
        sa.text("SELECT COUNT(*) FROM knowledge_articles WHERE embedding IS NOT NULL")
    )
    count = result.scalar()
    assert count >= 8, f"Expected >=8 articles with embeddings, got {count}"


@pytest.mark.asyncio
async def test_seed_duplicate_charge_scenario(db_session: AsyncSession):
    """Seed must create a customer with exactly two ₹2999 charges."""
    from app.seed import seed_all

    await seed_all(db_session)
    result = await db_session.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM payments p
            JOIN customers c ON c.id = p.customer_id
            WHERE p.amount = 2999 AND p.currency = 'INR'
            GROUP BY c.id
            HAVING COUNT(*) = 2
            """
        )
    )
    rows = result.fetchall()
    assert len(rows) >= 1, "No customer found with exactly two ₹2999 charges"


@pytest.mark.asyncio
async def test_seed_creates_known_bugs(db_session: AsyncSession):
    """Seed must include the Gantt chart Chrome bug with a workaround."""
    from app.seed import seed_all

    await seed_all(db_session)
    result = await db_session.execute(
        sa.text(
            "SELECT workaround FROM known_bugs WHERE LOWER(title) LIKE '%gantt%'"
        )
    )
    row = result.fetchone()
    assert row is not None, "Gantt chart bug not seeded"
    assert row[0], "Gantt chart bug has no workaround"


@pytest.mark.asyncio
async def test_seed_articles_cover_all_domains(db_session: AsyncSession):
    """Each specialist domain must have at least one knowledge article."""
    from app.seed import seed_all

    await seed_all(db_session)
    for domain in ("billing", "technical_support", "account_management"):
        result = await db_session.execute(
            sa.text(
                "SELECT COUNT(*) FROM knowledge_articles WHERE category = :cat"
            ),
            {"cat": domain},
        )
        count = result.scalar()
        assert count >= 1, f"No articles for domain: {domain}"
