"""
Idempotent seed script for CloudDesk.

Run with:
    python -m app.seed

Or call seed_all(session) from application startup.

Design: all inserts use ON CONFLICT DO NOTHING / merge patterns.
Re-running is always safe.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.knowledge_article import KnowledgeArticle
from app.models.known_bug import KnownBug
from app.models.outage import Outage
from app.models.payment import Payment

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Static seed data
# ──────────────────────────────────────────────────────────────────────────────

CUSTOMERS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Priya Sharma",
        "email": "priya.sharma@acmecorp.com",
        "subscription_plan": "enterprise",
        "tfa_enabled": True,
        "team_size": 42,
        "company": "Acme Corp",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "Rahul Mehta",
        "email": "rahul.mehta@startup.io",
        "subscription_plan": "pro",
        "tfa_enabled": False,
        "team_size": 8,
        "company": "Startup IO",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "Anjali Patel",
        "email": "anjali.patel@freelance.dev",
        "subscription_plan": "free",
        "tfa_enabled": False,
        "team_size": 1,
        "company": None,
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "Vikram Singh",
        "email": "vikram.singh@bigco.in",
        "subscription_plan": "enterprise",
        "tfa_enabled": True,
        "team_size": 150,
        "company": "BigCo India",
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "name": "Nisha Kapoor",
        "email": "nisha.kapoor@midmarket.com",
        "subscription_plan": "pro",
        "tfa_enabled": True,
        "team_size": 25,
        "company": "MidMarket Solutions",
    },
]

# Payments for customer 00000000-...0001 (Priya) — includes duplicate ₹2999 charge
PAYMENTS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "amount": 9999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-001",
        "description": "Enterprise Plan — Annual Subscription",
    },
    {
        "id": "10000000-0000-0000-0000-000000000002",
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "amount": 2999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-002",
        "description": "Add-on: Advanced Analytics",
    },
    {
        "id": "10000000-0000-0000-0000-000000000003",
        # Duplicate charge — same amount, same customer, different reference
        "customer_id": "00000000-0000-0000-0000-000000000001",
        "amount": 2999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-003",
        "description": "Add-on: Advanced Analytics (duplicate charge)",
    },
    {
        "id": "10000000-0000-0000-0000-000000000004",
        "customer_id": "00000000-0000-0000-0000-000000000002",
        "amount": 1999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-004",
        "description": "Pro Plan — Monthly",
    },
    {
        "id": "10000000-0000-0000-0000-000000000005",
        "customer_id": "00000000-0000-0000-0000-000000000002",
        "amount": 1999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-005",
        "description": "Pro Plan — Monthly",
    },
    {
        "id": "10000000-0000-0000-0000-000000000006",
        "customer_id": "00000000-0000-0000-0000-000000000005",
        "amount": 4999.00,
        "currency": "INR",
        "status": "completed",
        "reference": "PAY-2026-006",
        "description": "Pro Plan — Annual",
    },
]

KNOWLEDGE_ARTICLES = [
    # ── Account Management ──────────────────────────────────────────────────
    {
        "title": "How to Add a Team Member to Your CloudDesk Account",
        "content": (
            "To add a team member to CloudDesk:\n"
            "1. Go to Settings → Team Management.\n"
            "2. Click 'Invite Member'.\n"
            "3. Enter the team member's email address and choose their role "
            "(Admin, Agent, or Viewer).\n"
            "4. Click 'Send Invitation'.\n"
            "The team member will receive an email with a link to join your workspace. "
            "They must accept the invite within 48 hours. "
            "Pro and Enterprise plans support unlimited team members. "
            "Free plan is limited to 3 team members."
        ),
        "category": "account_management",
        "source": "help-center",
    },
    {
        "title": "Resetting Your CloudDesk Password",
        "content": (
            "If you've forgotten your password:\n"
            "1. Click 'Forgot password?' on the login page.\n"
            "2. Enter your registered email address.\n"
            "3. Check your inbox for a reset link (valid for 1 hour).\n"
            "4. Follow the link to set a new password.\n"
            "If you don't receive the email, check your spam folder or contact support."
        ),
        "category": "account_management",
        "source": "help-center",
    },
    {
        "title": "Setting Up Two-Factor Authentication (2FA)",
        "content": (
            "To enable 2FA on your CloudDesk account:\n"
            "1. Go to Settings → Security.\n"
            "2. Click 'Enable 2FA'.\n"
            "3. Scan the QR code with an authenticator app (Google Authenticator, Authy).\n"
            "4. Enter the 6-digit code to confirm setup.\n"
            "Once enabled, you'll be prompted for a 2FA code on each login. "
            "Enterprise accounts can enforce 2FA org-wide from the Admin panel."
        ),
        "category": "account_management",
        "source": "help-center",
    },
    # ── Billing ─────────────────────────────────────────────────────────────
    {
        "title": "Understanding Your CloudDesk Invoice",
        "content": (
            "Your monthly invoice is generated on the billing cycle start date. "
            "It includes:\n"
            "- Base subscription cost for your plan.\n"
            "- Any add-ons or extra usage charges.\n"
            "- Applied credits or discounts.\n"
            "You can download invoices as PDF from Billing → Invoice History. "
            "Invoices are also emailed to the billing contact on the account."
        ),
        "category": "billing",
        "source": "help-center",
    },
    {
        "title": "Upgrading or Downgrading Your Subscription Plan",
        "content": (
            "To change your CloudDesk subscription plan:\n"
            "1. Go to Billing → Plan.\n"
            "2. Select the new plan.\n"
            "3. Confirm the change.\n"
            "Upgrades take effect immediately and are prorated. "
            "Downgrades take effect at the end of the current billing period. "
            "Note: downgrading may remove access to features or team member slots "
            "exceeding the new plan's limits."
        ),
        "category": "billing",
        "source": "help-center",
    },
    {
        "title": "Requesting a Refund for CloudDesk Charges",
        "content": (
            "Refund requests are reviewed by our billing team. "
            "To request a refund:\n"
            "1. Contact support with your invoice number and reason.\n"
            "2. Our team will review within 2 business days.\n"
            "3. Approved refunds are processed within 5-7 business days.\n"
            "Refunds are typically issued for billing errors or duplicate charges. "
            "Subscription refunds are not available after 14 days from billing date."
        ),
        "category": "billing",
        "source": "help-center",
    },
    # ── Technical Support ────────────────────────────────────────────────────
    {
        "title": "Gantt Chart Not Loading or Displaying Incorrectly",
        "content": (
            "If the Gantt chart is not loading or shows a blank screen, especially on Chrome:\n"
            "Known issue: Chrome versions 120+ have a rendering bug affecting WebGL-based "
            "Gantt charts in certain viewport sizes.\n"
            "Workaround:\n"
            "1. Disable hardware acceleration in Chrome: "
            "Settings → System → uncheck 'Use hardware acceleration when available', restart Chrome.\n"
            "2. Alternatively, use Firefox or Edge as a temporary workaround.\n"
            "3. Or press Ctrl+Shift+J to open DevTools, then close it — this often forces a re-render.\n"
            "Our engineering team is tracking this issue (BUG-4821) and a fix is targeted for "
            "the next Chrome update compatibility patch."
        ),
        "category": "technical_support",
        "source": "help-center",
    },
    {
        "title": "Troubleshooting CloudDesk Slow Performance",
        "content": (
            "If CloudDesk is loading slowly:\n"
            "1. Clear your browser cache and cookies.\n"
            "2. Disable browser extensions (some ad-blockers interfere with our API calls).\n"
            "3. Check your internet connection speed.\n"
            "4. Try a different browser or incognito mode.\n"
            "5. Check our status page at status.clouddesk.io for any ongoing incidents.\n"
            "If the issue persists, contact support with your browser version and a HAR file."
        ),
        "category": "technical_support",
        "source": "help-center",
    },
    {
        "title": "Integrating CloudDesk with Slack",
        "content": (
            "To connect CloudDesk with Slack:\n"
            "1. Go to Settings → Integrations → Slack.\n"
            "2. Click 'Connect to Slack' and authorize the app.\n"
            "3. Choose which channels to receive notifications in.\n"
            "4. Configure notification rules (new tickets, status changes, escalations).\n"
            "You can disconnect the integration at any time from the same settings page."
        ),
        "category": "technical_support",
        "source": "help-center",
    },
]

KNOWN_BUGS = [
    {
        "id": "20000000-0000-0000-0000-000000000001",
        "title": "Gantt Chart Not Loading on Chrome — WebGL Rendering Bug",
        "description": (
            "Chrome versions 120+ have a WebGL rendering issue that causes the Gantt chart "
            "component to render blank or fail to load entirely in certain viewport configurations. "
            "Affects approximately 15% of Chrome users on affected versions."
        ),
        "workaround": (
            "1. Disable Chrome hardware acceleration: Settings → System → uncheck "
            "'Use hardware acceleration when available', then restart Chrome.\n"
            "2. Use Firefox or Edge as a temporary alternative.\n"
            "3. Open Chrome DevTools (Ctrl+Shift+J) then close it to force re-render."
        ),
        "service": "project-management",
        "status": "open",
        "affected_browsers": "Chrome 120+",
    },
    {
        "id": "20000000-0000-0000-0000-000000000002",
        "title": "Email Notifications Delayed During Peak Hours",
        "description": (
            "Email notifications for ticket updates may be delayed by 5-15 minutes "
            "during peak usage hours (9-11 AM and 2-4 PM IST). "
            "No emails are lost; they are queued and eventually delivered."
        ),
        "workaround": (
            "Check the CloudDesk dashboard directly for real-time ticket status. "
            "In-app notifications are not affected."
        ),
        "service": "notifications",
        "status": "monitoring",
        "affected_browsers": None,
    },
    {
        "id": "20000000-0000-0000-0000-000000000003",
        "title": "CSV Export Fails for Reports with More than 10,000 Rows",
        "description": (
            "Exporting reports larger than 10,000 rows as CSV times out with a 504 error. "
            "The export job is cancelled server-side."
        ),
        "workaround": (
            "Use date range filters to export in smaller batches. "
            "For example, export one month at a time."
        ),
        "service": "reporting",
        "status": "open",
        "affected_browsers": None,
    },
]

OUTAGES = [
    {
        "id": "30000000-0000-0000-0000-000000000001",
        "service": "api",
        "description": (
            "Intermittent 503 errors on API endpoints affecting approximately 3% of requests. "
            "Issue was traced to a misconfigured load balancer. Fully resolved."
        ),
        "status": "resolved",
        "started_at": datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc),
        "resolved_at": datetime(2026, 10, 15, 12, 30, 0, tzinfo=timezone.utc),
    },
    {
        "id": "30000000-0000-0000-0000-000000000002",
        "service": "notifications",
        "description": (
            "Email notification delivery delays of 5-15 minutes during peak hours. "
            "Root cause: third-party email provider queue buildup."
        ),
        "status": "monitoring",
        "started_at": datetime(2026, 10, 20, 9, 0, 0, tzinfo=timezone.utc),
        "resolved_at": None,
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Seed functions
# ──────────────────────────────────────────────────────────────────────────────


async def _upsert_customers(session: AsyncSession) -> None:
    for data in CUSTOMERS:
        exists = await session.scalar(
            sa.select(sa.func.count()).where(Customer.email == data["email"])
        )
        if not exists:
            session.add(Customer(**data))
    await session.flush()


async def _upsert_payments(session: AsyncSession) -> None:
    for data in PAYMENTS:
        exists = await session.scalar(
            sa.select(sa.func.count()).where(Payment.id == data["id"])
        )
        if not exists:
            session.add(Payment(**data))
    await session.flush()


async def _upsert_knowledge_articles(session: AsyncSession) -> None:
    from app.embeddings import embed_batch

    # Only insert articles that don't already exist by title
    new_articles = []
    for data in KNOWLEDGE_ARTICLES:
        exists = await session.scalar(
            sa.select(sa.func.count()).where(
                KnowledgeArticle.title == data["title"]
            )
        )
        if not exists:
            new_articles.append(data)

    if not new_articles:
        return

    # Batch embed all new articles at once
    texts = [a["content"] for a in new_articles]
    vectors = embed_batch(texts)

    for article_data, vector in zip(new_articles, vectors):
        session.add(KnowledgeArticle(**article_data, embedding=vector))
    await session.flush()


async def _upsert_known_bugs(session: AsyncSession) -> None:
    for data in KNOWN_BUGS:
        exists = await session.scalar(
            sa.select(sa.func.count()).where(KnownBug.id == data["id"])
        )
        if not exists:
            session.add(KnownBug(**data))
    await session.flush()


async def _upsert_outages(session: AsyncSession) -> None:
    for data in OUTAGES:
        exists = await session.scalar(
            sa.select(sa.func.count()).where(Outage.id == data["id"])
        )
        if not exists:
            session.add(Outage(**data))
    await session.flush()


async def seed_all(session: AsyncSession) -> None:
    """
    Populate the database with deterministic mock data.

    Safe to call multiple times — re-running does not create duplicates.
    """
    logger.info("Seeding customers...")
    await _upsert_customers(session)

    logger.info("Seeding payments...")
    await _upsert_payments(session)

    logger.info("Seeding knowledge articles (generating embeddings if needed)...")
    await _upsert_knowledge_articles(session)

    logger.info("Seeding known bugs...")
    await _upsert_known_bugs(session)

    logger.info("Seeding outages...")
    await _upsert_outages(session)

    await session.commit()
    logger.info("Seeding complete.")


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    from app.database import get_session_factory

    async def _main() -> None:
        logging.basicConfig(level=logging.INFO)
        factory = get_session_factory()
        async with factory() as session:
            await seed_all(session)

    asyncio.run(_main())
