"""LangGraph workflow definition for CloudDesk smart agent."""
from __future__ import annotations

from typing import Any, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from app.workflow.nodes import (
    account_specialist_node,
    apply_escalation_rules_node,
    auto_resolve_node,
    billing_specialist_node,
    check_confidence_edge,
    check_escalation_edge,
    classify_ticket_node,
    handle_review_decision_node,
    prepare_for_review_node,
    route_to_specialist_edge,
    technical_specialist_node,
)
from app.workflow.state import TicketState


def create_support_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> Any:
    """Build and compile the support ticket processing StateGraph."""
    workflow = StateGraph(TicketState)

    # 1. Add core nodes
    workflow.add_node("classify", classify_ticket_node)
    workflow.add_node("billing_specialist", billing_specialist_node)
    workflow.add_node("technical_specialist", technical_specialist_node)
    workflow.add_node("account_specialist", account_specialist_node)
    workflow.add_node("apply_escalation", apply_escalation_rules_node)
    workflow.add_node("prepare_for_review", prepare_for_review_node)
    workflow.add_node("auto_resolve", auto_resolve_node)
    workflow.add_node("handle_review_decision", handle_review_decision_node)

    # 2. Add edges & conditional transitions
    workflow.add_edge(START, "classify")

    # After classify: check confidence
    workflow.add_conditional_edges(
        "classify",
        check_confidence_edge,
        {
            "route": "route_check",
            "escalate": "prepare_for_review",
        },
    )

    # Route check dummy node / router
    def _route_node(state: TicketState) -> dict[str, Any]:
        return {}

    workflow.add_node("route_check", _route_node)
    workflow.add_conditional_edges(
        "route_check",
        route_to_specialist_edge,
        {
            "billing": "billing_specialist",
            "technical": "technical_specialist",
            "account": "account_specialist",
            "escalate": "prepare_for_review",
        },
    )

    # Specialists -> apply escalation rules
    workflow.add_edge("billing_specialist", "apply_escalation")
    workflow.add_edge("technical_specialist", "apply_escalation")
    workflow.add_edge("account_specialist", "apply_escalation")

    # Escalation check -> review or auto-resolve
    workflow.add_conditional_edges(
        "apply_escalation",
        check_escalation_edge,
        {
            "escalate": "prepare_for_review",
            "resolve": "auto_resolve",
        },
    )

    # Resume flow after human manager input
    workflow.add_edge("prepare_for_review", "handle_review_decision")
    workflow.add_edge("handle_review_decision", END)
    workflow.add_edge("auto_resolve", END)

    # Default to MemorySaver if none passed (safe for tests & in-memory execution)
    cp = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=cp)
