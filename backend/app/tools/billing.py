"""Billing specialist tools."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.payment import Payment


async def get_customer_billing_history(
    customer_id: str, session: AsyncSession
) -> list[dict]:
    """
    Fetch billing and payment history for a customer.

    Args:
        customer_id: The customer UUID.
        session: Active async DB session.

    Returns:
        List of payment dictionaries ordered newest to oldest.
    """
    stmt = (
        sa.select(Payment)
        .where(Payment.customer_id == customer_id)
        .order_by(Payment.created_at.desc())
    )
    result = await session.execute(stmt)
    payments = result.scalars().all()
    return [
        {
            "id": p.id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "reference": p.reference,
            "timestamp": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payments
    ]


async def get_current_subscription(
    customer_id: str, session: AsyncSession
) -> dict | None:
    """
    Get current subscription plan and status for a customer.

    Args:
        customer_id: The customer UUID.
        session: Active async DB session.

    Returns:
        Dictionary with subscription details, or None if not found.
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
        "team_size": customer.team_size,
        "company": customer.company,
    }
