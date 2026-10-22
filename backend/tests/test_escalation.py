"""Tests for deterministic escalation rules."""
from __future__ import annotations

import pytest

from app.workflow.escalation import check_escalation


def test_escalation_low_confidence():
    """Confidence below threshold triggers mandatory escalation."""
    is_esc, reason = check_escalation("BILLING", "Question", "Help me", confidence=0.50, confidence_threshold=0.65)
    assert is_esc is True
    assert "Low classification confidence" in (reason or "")


def test_escalation_billing_refund():
    """Refund request triggers mandatory billing escalation."""
    is_esc, reason = check_escalation("BILLING", "Refund please", "I want a refund for last month")
    assert is_esc is True
    assert "refund" in (reason or "").lower()


def test_escalation_billing_double_charge():
    """Duplicate charge triggers mandatory billing escalation."""
    is_esc, reason = check_escalation("BILLING", "Payment problem", "I was charged twice for the plan")
    assert is_esc is True
    assert "dispute" in (reason or "").lower() or "duplicate" in (reason or "").lower()


def test_escalation_billing_high_amount():
    """Amount exceeding ₹5000 triggers escalation."""
    specialist = {"payments": [{"amount": 7500.0, "status": "completed"}]}
    is_esc, reason = check_escalation("BILLING", "Payment query", "Check my payment", specialist_results=specialist)
    assert is_esc is True
    assert "exceeds ₹5000" in (reason or "")


def test_escalation_tech_security():
    """Security vulnerability triggers mandatory tech escalation."""
    is_esc, reason = check_escalation("TECHNICAL_SUPPORT", "Security flaw", "Found an SQL injection vulnerability")
    assert is_esc is True
    assert "Security" in (reason or "")


def test_escalation_tech_data_loss():
    """Data loss triggers mandatory tech escalation."""
    is_esc, reason = check_escalation("TECHNICAL_SUPPORT", "Data gone", "Our project records were deleted and wiped")
    assert is_esc is True
    assert "data loss" in (reason or "").lower()


def test_escalation_tech_no_articles():
    """Empty specialist results trigger escalation."""
    specialist = {"articles": [], "bugs": [], "outages": []}
    is_esc, reason = check_escalation("TECHNICAL_SUPPORT", "Quantum capacitor error", "Widget broke", specialist_results=specialist)
    assert is_esc is True
    assert "No matching knowledge article" in (reason or "")


def test_escalation_account_delete():
    """Account deletion triggers mandatory escalation."""
    is_esc, reason = check_escalation("ACCOUNT_MANAGEMENT", "Close account", "Please delete my account and data")
    assert is_esc is True
    assert "deletion" in (reason or "").lower()


def test_escalation_account_ownership():
    """Ownership transfer triggers mandatory escalation."""
    is_esc, reason = check_escalation("ACCOUNT_MANAGEMENT", "Admin change", "I want to transfer ownership to another user")
    assert is_esc is True
    assert "ownership" in (reason or "").lower()


def test_escalation_account_unauthorized_access():
    """Unauthorized access triggers mandatory escalation."""
    is_esc, reason = check_escalation("ACCOUNT_MANAGEMENT", "Help", "Someone had unauthorized access to our account")
    assert is_esc is True
    assert "Unauthorized" in (reason or "")


def test_no_escalation_for_standard_ticket():
    """Normal FAQ ticket does not escalate."""
    specialist = {"articles": [{"title": "Changing 2FA", "content": "Steps to change 2FA"}], "bugs": [], "outages": []}
    is_esc, reason = check_escalation("ACCOUNT_MANAGEMENT", "How to update 2FA", "How do I change my phone number?", specialist_results=specialist)
    assert is_esc is False
    assert reason is None
