"""Account management specialist tools."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.tools.technical import search_knowledge_base


async def get_account_details(
    customer_id: str, session: AsyncSession
) -> dict | None:
    """
    Fetch comprehensive account details for a customer.

    Args:
        customer_id: The customer UUID.
        session: Active async DB session.

    Returns:
        Dict with profile, 2FA status, team size, subscription plan, or None.
    """
    stmt = sa.select(Customer).where(Customer.id == customer_id)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        return None
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "subscription_plan": customer.subscription_plan,
        "tfa_enabled": customer.tfa_enabled,
        "team_size": customer.team_size,
        "company": customer.company,
    }


__all__ = ["get_account_details", "search_knowledge_base"]
