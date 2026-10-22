"""Tests for ticket classification logic."""
from __future__ import annotations

import pytest

from app.models.ticket import TicketDomain
from app.workflow.llm import classify_ticket
from app.workflow.schemas import ClassificationResult


@pytest.mark.asyncio
async def test_classification_billing():
    """Billing ticket correctly classified as BILLING."""
    res = await classify_ticket("Invoice issue", "I was charged twice on my invoice.")
    assert isinstance(res, ClassificationResult)
    assert res.domain == TicketDomain.BILLING
    assert res.confidence >= 0.70


@pytest.mark.asyncio
async def test_classification_technical():
    """Technical ticket correctly classified as TECHNICAL_SUPPORT."""
    res = await classify_ticket("Gantt chart not working", "The Gantt chart is blank on Chrome.")
    assert isinstance(res, ClassificationResult)
    assert res.domain == TicketDomain.TECHNICAL_SUPPORT
    assert res.confidence >= 0.70


@pytest.mark.asyncio
async def test_classification_account():
    """Account ticket correctly classified as ACCOUNT_MANAGEMENT."""
    res = await classify_ticket("Reset password", "I cannot log in and need to reset my password.")
    assert isinstance(res, ClassificationResult)
    assert res.domain == TicketDomain.ACCOUNT_MANAGEMENT
    assert res.confidence >= 0.70


@pytest.mark.asyncio
async def test_classification_technical_data_loss():
    """Data loss report is classified as TECHNICAL_SUPPORT domain."""
    res = await classify_ticket(
        "Critical data loss: production records wiped",
        "Our database experienced complete data loss and customer records were wiped and corrupted.",
    )
    assert isinstance(res, ClassificationResult)
    assert res.domain == TicketDomain.TECHNICAL_SUPPORT
    assert res.confidence >= 0.70


@pytest.mark.asyncio
async def test_classification_technical_security():
    """Security concern / vulnerability is classified as TECHNICAL_SUPPORT domain."""
    res = await classify_ticket(
        "Security breach alert: unauthorized vulnerability exploit",
        "We detected an unauthorized credential leak and potential CVE exploit on our API.",
    )
    assert isinstance(res, ClassificationResult)
    assert res.domain == TicketDomain.TECHNICAL_SUPPORT
    assert res.confidence >= 0.70


@pytest.mark.asyncio
async def test_classification_unknown():
    """Vague / gibberish text classifies with low confidence or UNKNOWN."""
    res = await classify_ticket("asdf123", "random noise xyz")
    assert isinstance(res, ClassificationResult)
    assert res.confidence < 0.65 or res.domain == TicketDomain.UNKNOWN

