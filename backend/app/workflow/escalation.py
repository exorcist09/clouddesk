"""Deterministic escalation rules for CloudDesk support tickets."""
from __future__ import annotations

import re
from typing import Any, Optional


def check_escalation(
    domain: str,
    subject: str,
    body: str,
    confidence: float = 1.0,
    confidence_threshold: float = 0.65,
    specialist_results: Optional[dict[str, Any]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Evaluate deterministic escalation rules.
    Returns (requires_escalation, reason).
    """
    text = f"{subject} {body}".lower()

    # Rule 1: Confidence below threshold
    if confidence < confidence_threshold:
        return True, f"Low classification confidence: {confidence:.2f} (threshold: {confidence_threshold:.2f})"

    # Rule 2: Domain-specific triggers
    domain_upper = domain.upper() if domain else "UNKNOWN"

    if domain_upper == "BILLING":
        # Check refund request
        if re.search(r"\b(refund|reimburse|money\s*back)\b", text):
            return True, "Mandatory escalation: Customer requesting refund"

        # Check billing dispute / duplicate charge
        if re.search(r"\b(dispute|charged\s*twice|double\s*charge|duplicate\s*charge|unauthorized\s*charge)\b", text):
            return True, "Mandatory escalation: Billing dispute or duplicate charge reported"

        # Check transaction amount > 5000 from payments or text
        if specialist_results and "payments" in specialist_results:
            payments = specialist_results.get("payments", [])
            for p in payments:
                if float(p.get("amount", 0)) > 5000.0:
                    return True, f"Mandatory escalation: Transaction amount exceeds ₹5000 (₹{p.get('amount')})"

        # Check explicit high amounts in ticket text (e.g. ₹6000, 6000 INR, $1000)
        amt_match = re.findall(r"(?:₹|rs\.?|inr|\$)\s*(\d+[\d,]*)", text)
        for m in amt_match:
            try:
                amt = float(m.replace(",", ""))
                if amt > 5000.0:
                    return True, f"Mandatory escalation: Mentioned amount exceeds ₹5000 (₹{amt})"
            except ValueError:
                pass

    elif domain_upper == "TECHNICAL_SUPPORT":
        # Check security / breach
        if re.search(r"\b(security|vulnerability|breach|cve|hacked|leak|exploit)\b", text):
            return True, "Mandatory escalation: Security concern or vulnerability reported"

        # Check data loss
        if re.search(r"\b(data\s*loss|lost\s*data|records?\s*deleted|corrupted|wiped)\b", text):
            return True, "Mandatory escalation: Customer reported data loss or corruption"

        # Check if no knowledge base articles or workarounds found
        if specialist_results is not None:
            articles = specialist_results.get("articles", [])
            bugs = specialist_results.get("bugs", [])
            outages = specialist_results.get("outages", [])
            if not articles and not bugs and not outages:
                return True, "Mandatory escalation: No matching knowledge article or known issue found"

    elif domain_upper == "ACCOUNT_MANAGEMENT":
        # Check deletion
        if re.search(r"\b(delete\s*(my\s*)?account|close\s*account|erase\s*data|gdpr|permanent\s*removal)\b", text):
            return True, "Mandatory escalation: Account deletion or data erasure requested"

        # Check ownership transfer
        if re.search(r"\b(transfer\s*ownership|change\s*owner|new\s*owner|account\s*transfer)\b", text):
            return True, "Mandatory escalation: Account ownership transfer requested"

        # Check unauthorized access
        if re.search(r"\b(unauthorized\s*access|compromised|stolen\s*credentials|locked\s*out)\b", text):
            return True, "Mandatory escalation: Unauthorized account access or compromised credentials"

    elif domain_upper == "UNKNOWN":
        return True, "Mandatory escalation: Ticket domain could not be identified"

    return False, None
