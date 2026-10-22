"""Tests for billing specialist tools."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed import seed_all
from app.tools.billing import get_current_subscription, get_customer_billing_history


@pytest.mark.asyncio
async def test_billing_history_seeded_customer(db_session: AsyncSession):
    """Seed DB and fetch billing history for known customer."""
    await seed_all(db_session)

    # Customer 1 (Priya Sharma) has payments
    customer_id = "00000000-0000-0000-0000-000000000001"
    history = await get_customer_billing_history(customer_id, db_session)
    assert len(history) >= 1
    assert "amount" in history[0]
    assert "currency" in history[0]
    assert "reference" in history[0]


@pytest.mark.asyncio
async def test_billing_history_missing_customer(db_session: AsyncSession):
    """Missing customer returns empty billing list."""
    history = await get_customer_billing_history("00000000-0000-0000-0000-000000000999", db_session)
    assert history == []


@pytest.mark.asyncio
async def test_current_subscription(db_session: AsyncSession):
    """Fetch current subscription plan for customer."""
    await seed_all(db_session)

    customer_id = "00000000-0000-0000-0000-000000000001"
    sub = await get_current_subscription(customer_id, db_session)
    assert sub is not None
    assert sub["subscription_plan"] == "enterprise"
    assert sub["name"] == "Priya Sharma"


@pytest.mark.asyncio
async def test_current_subscription_missing_customer(db_session: AsyncSession):
    """Missing customer returns None for subscription."""
    sub = await get_current_subscription("00000000-0000-0000-0000-000000000999", db_session)
    assert sub is None
