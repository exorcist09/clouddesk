"""End-to-end workflow execution tests."""
from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed import seed_all
from app.workflow.graph import create_support_graph


@pytest.mark.asyncio
async def test_workflow_auto_resolve_path(db_session: AsyncSession):
    """Normal technical issue with workaround auto-resolves."""
    await seed_all(db_session)

    checkpointer = MemorySaver()
    graph = create_support_graph(checkpointer=checkpointer)

    thread_id = "test-thread-auto-resolve"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "ticket_id": "test-t1",
        "customer_email": "user@example.com",
        "subject": "Gantt chart not loading",
        "body": "The Gantt chart shows blank on Chrome.",
    }

    result = await graph.ainvoke(initial_state, config=config)

    assert result["domain"] == "TECHNICAL_SUPPORT"
    assert result["status"] == "RESOLVED"
    assert result["final_reply"] is not None
    assert len(result["final_reply"]) > 0


@pytest.mark.asyncio
async def test_workflow_escalation_and_approval(db_session: AsyncSession):
    """Duplicate charge escalates to PENDING_REVIEW, manager approves."""
    await seed_all(db_session)

    checkpointer = MemorySaver()
    graph = create_support_graph(checkpointer=checkpointer)

    thread_id = "test-thread-escalate-approve"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "ticket_id": "test-t2",
        "customer_email": "user@example.com",
        "subject": "Payment issue",
        "body": "I was charged twice for ₹2999, please refund.",
    }

    # First invoke pauses at interrupt (prepare_for_review)
    result = await graph.ainvoke(initial_state, config=config)

    # State paused at interrupt
    snapshot = graph.get_state(config)
    assert snapshot.next == ("prepare_for_review",)
    assert snapshot.values.get("escalation_required") is True

    # Manager approves
    from langgraph.types import Command
    resumed = await graph.ainvoke(
        Command(resume={"decision": "APPROVE", "reviewer": "manager_alice"}),
        config=config,
    )

    assert resumed["status"] == "RESOLVED"
    assert resumed["final_reply"] is not None


@pytest.mark.asyncio
async def test_workflow_escalation_and_rejection(db_session: AsyncSession):
    """Manager rejects draft."""
    await seed_all(db_session)

    checkpointer = MemorySaver()
    graph = create_support_graph(checkpointer=checkpointer)

    thread_id = "test-thread-escalate-reject"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "ticket_id": "test-t3",
        "customer_email": "user@example.com",
        "subject": "Delete account",
        "body": "Please delete my account and data immediately.",
    }

    await graph.ainvoke(initial_state, config=config)

    from langgraph.types import Command
    resumed = await graph.ainvoke(
        Command(resume={"decision": "REJECT", "rejection_reason": "Incomplete verification", "reviewer": "manager_bob"}),
        config=config,
    )

    assert resumed["status"] == "REJECTED"
    assert "Incomplete verification" in resumed["error_info"]
