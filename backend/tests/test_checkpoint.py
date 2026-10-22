"""Tests for LangGraph checkpoint persistence."""
from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.workflow.graph import create_support_graph


@pytest.mark.asyncio
async def test_checkpoint_persists_state():
    """Checkpoint preserves thread state for subsequent lookup and resumption."""
    checkpointer = MemorySaver()
    graph = create_support_graph(checkpointer=checkpointer)

    thread_id = "checkpoint-test-thread-1"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "ticket_id": "t-chk-1",
        "customer_email": "chk@test.com",
        "subject": "Charged twice",
        "body": "Duplicate charge on invoice, refund please",
    }

    # Runs until interrupt
    await graph.ainvoke(initial_state, config=config)

    # Re-instantiate graph with same checkpointer (simulating server reload)
    new_graph = create_support_graph(checkpointer=checkpointer)
    snapshot = new_graph.get_state(config)

    assert snapshot.values["ticket_id"] == "t-chk-1"
    assert snapshot.values["escalation_required"] is True
    assert "prepare_for_review" in snapshot.next
