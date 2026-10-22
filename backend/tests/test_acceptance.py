"""Five sample acceptance ticket tests from PRD specification."""
from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed import seed_all
from app.workflow.graph import create_support_graph


@pytest.mark.asyncio
async def test_acceptance_1_add_team_member(db_session: AsyncSession):
    """Ticket 1: 'How do I add a team member?' -> Account -> auto-resolve."""
    await seed_all(db_session)
    graph = create_support_graph(checkpointer=MemorySaver())

    state = {
        "ticket_id": "acc-1",
        "customer_email": "priya.sharma@acmecorp.com",
        "subject": "How do I add a team member?",
        "body": "We just hired someone new. How do I invite them to our team dashboard?",
    }
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "acc-1"}})

    assert result["domain"] == "ACCOUNT_MANAGEMENT"
    assert result["status"] == "RESOLVED"
    assert result["final_reply"] is not None


@pytest.mark.asyncio
async def test_acceptance_2_charged_twice(db_session: AsyncSession):
    """Ticket 2: 'I was charged twice, Rs 2,999 each' -> Billing -> dispute -> escalate."""
    await seed_all(db_session)
    graph = create_support_graph(checkpointer=MemorySaver())

    state = {
        "ticket_id": "acc-2",
        "customer_email": "priya.sharma@acmecorp.com",
        "subject": "Charged twice on renewal",
        "body": "I was charged twice, Rs 2,999 each on my card. Please refund the extra charge.",
    }
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "acc-2"}})

    # Halts before resolving
    snapshot = graph.get_state({"configurable": {"thread_id": "acc-2"}})
    assert snapshot.next == ("prepare_for_review",)
    assert snapshot.values.get("escalation_required") is True
    assert "Mandatory escalation" in (snapshot.values.get("escalation_reason") or "")


@pytest.mark.asyncio
async def test_acceptance_3_gantt_chrome_bug(db_session: AsyncSession):
    """Ticket 3: 'Gantt chart not loading on Chrome' -> Technical -> workaround -> auto-resolve."""
    await seed_all(db_session)
    graph = create_support_graph(checkpointer=MemorySaver())

    state = {
        "ticket_id": "acc-3",
        "customer_email": "rahul.mehta@startup.io",
        "subject": "Gantt chart not loading on Chrome",
        "body": "The Gantt chart screen is completely blank on Chrome 124.",
    }
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "acc-3"}})

    assert result["domain"] == "TECHNICAL_SUPPORT"
    assert result["status"] == "RESOLVED"
    assert "hardware acceleration" in result["final_reply"].lower() or "workaround" in result["final_reply"].lower()


@pytest.mark.asyncio
async def test_acceptance_4_delete_account(db_session: AsyncSession):
    """Ticket 4: 'Please delete my account and all data' -> Account -> deletion -> escalate."""
    await seed_all(db_session)
    graph = create_support_graph(checkpointer=MemorySaver())

    state = {
        "ticket_id": "acc-4",
        "customer_email": "anjali.patel@freelance.dev",
        "subject": "Account deletion",
        "body": "Please delete my account and all data under GDPR requirements.",
    }
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "acc-4"}})

    snapshot = graph.get_state({"configurable": {"thread_id": "acc-4"}})
    assert snapshot.next == ("prepare_for_review",)
    assert snapshot.values.get("escalation_required") is True


@pytest.mark.asyncio
async def test_acceptance_5_vague_low_confidence(db_session: AsyncSession):
    """Ticket 5: 'Something is wrong but I don't know what' -> Low confidence -> escalate."""
    await seed_all(db_session)
    graph = create_support_graph(checkpointer=MemorySaver())

    state = {
        "ticket_id": "acc-5",
        "customer_email": "user@example.com",
        "subject": "Something is wrong but I don't know what",
        "body": "Random glitch happened maybe.",
    }
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "acc-5"}})

    snapshot = graph.get_state({"configurable": {"thread_id": "acc-5"}})
    assert snapshot.next == ("prepare_for_review",)
    assert snapshot.values.get("escalation_required") is True
