"""Tests for account management specialist tools."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed import seed_all
from app.tools.account import get_account_details


@pytest.mark.asyncio
async def test_account_details_seeded_customer(db_session: AsyncSession):
    """Fetch full profile for seeded customer."""
    await seed_all(db_session)

    customer_id = "00000000-0000-0000-0000-000000000001"
    details = await get_account_details(customer_id, db_session)
    assert details is not None
    assert details["email"] == "priya.sharma@acmecorp.com"
    assert details["tfa_enabled"] is True
    assert details["team_size"] == 42


@pytest.mark.asyncio
async def test_account_details_missing_customer(db_session: AsyncSession):
    """Missing customer returns None."""
    details = await get_account_details("00000000-0000-0000-0000-000000000999", db_session)
    assert details is None
