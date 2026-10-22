"""OpenRouter LLM client with structured JSON parsing and fallback."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.models.ticket import TicketDomain
from app.workflow.schemas import ClassificationResult, DraftResponse

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def _fallback_classify(subject: str, body: str) -> ClassificationResult:
    """Heuristic fallback classification when OpenRouter API is unavailable or unconfigured."""
    text = f"{subject} {body}".lower()

    if any(k in text for k in ["bill", "invoice", "payment", "charge", "refund", "subscription", "pricing", "cost", "receipt"]):
        return ClassificationResult(
            domain=TicketDomain.BILLING,
            confidence=0.92,
            explanation="Detected billing keywords in ticket text",
        )
    if any(k in text for k in ["bug", "error", "crash", "gantt", "slow", "down", "outage", "broken", "fail", "chrome", "webgl"]):
        return ClassificationResult(
            domain=TicketDomain.TECHNICAL_SUPPORT,
            confidence=0.95,
            explanation="Detected technical issue keywords in ticket text",
        )
    if any(k in text for k in ["account", "password", "2fa", "login", "team", "invite", "delete", "profile", "user"]):
        return ClassificationResult(
            domain=TicketDomain.ACCOUNT_MANAGEMENT,
            confidence=0.90,
            explanation="Detected account management keywords in ticket text",
        )

    return ClassificationResult(
        domain=TicketDomain.UNKNOWN,
        confidence=0.40,
        explanation="Unable to confidently determine domain from text",
    )


def _fallback_draft(
    domain: str,
    subject: str,
    specialist_results: Optional[dict[str, Any]] = None,
) -> DraftResponse:
    """Fallback draft generation when offline or API key absent."""
    specialist_results = specialist_results or {}
    articles = specialist_results.get("articles", [])
    bugs = specialist_results.get("bugs", [])

    sources = [a.get("title", "") for a in articles if a.get("title")]
    sources.extend([b.get("title", "") for b in bugs if b.get("title")])

    if bugs and bugs[0].get("workaround"):
        reply = (
            f"Hello,\n\nWe have identified a known issue regarding '{subject}'. "
            f"Workaround: {bugs[0]['workaround']}\n\nOur team is working on a permanent fix."
        )
    elif articles:
        reply = (
            f"Hello,\n\nBased on our knowledge base for '{articles[0]['title']}':\n"
            f"{articles[0]['content']}\n\nPlease let us know if you need more assistance."
        )
    else:
        reply = (
            f"Hello,\n\nThank you for reaching out regarding '{subject}'. "
            "Our support team has received your ticket and is looking into this."
        )

    return DraftResponse(
        reply_text=reply,
        summary=f"Processed inquiry regarding {subject}",
        sources=sources,
        requires_escalation=False,
    )


async def call_openrouter_llm(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    json_mode: bool = False,
    timeout: float = 30.0,
) -> Optional[str]:
    """Call OpenRouter completions endpoint with retries."""
    settings = get_settings()
    api_key = settings.openrouter_api_key

    if not api_key or "your_" in api_key or "dummy" in api_key.lower():
        return None

    model_name = model or settings.openrouter_model
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(OPENROUTER_CHAT_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            logger.warning("OpenRouter LLM returned %d: %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("OpenRouter LLM request failed: %s", e)

    return None


async def classify_ticket(subject: str, body: str) -> ClassificationResult:
    """Classify ticket into domain using OpenRouter with structured fallback."""
    system_prompt = (
        "You are an expert customer support classifier for CloudDesk.\n"
        "Classify the ticket into exactly one domain: BILLING, TECHNICAL_SUPPORT, ACCOUNT_MANAGEMENT, or UNKNOWN.\n"
        "Provide a confidence score between 0.0 and 1.0.\n"
        "Return ONLY JSON: {\"domain\": \"...\", \"confidence\": 0.95, \"explanation\": \"...\"}"
    )
    user_prompt = f"Subject: {subject}\nBody: {body}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = await call_openrouter_llm(messages, json_mode=True)
    if response_text:
        try:
            data = json.loads(response_text)
            domain_str = data.get("domain", "UNKNOWN").upper()
            domain = TicketDomain[domain_str] if domain_str in TicketDomain.__members__ else TicketDomain.UNKNOWN
            confidence = float(data.get("confidence", 0.5))
            return ClassificationResult(
                domain=domain,
                confidence=min(1.0, max(0.0, confidence)),
                explanation=data.get("explanation", ""),
            )
        except Exception as e:
            logger.warning("Failed to parse LLM classification JSON: %s", e)

    return _fallback_classify(subject, body)


async def generate_draft(
    domain: str,
    subject: str,
    body: str,
    specialist_results: Optional[dict[str, Any]] = None,
) -> DraftResponse:
    """Generate professional draft reply using OpenRouter LLM with fallback."""
    system_prompt = (
        "You are a professional customer support specialist for CloudDesk.\n"
        "Draft a helpful, polite reply addressing the customer's inquiry using the retrieved knowledge.\n"
        "Return JSON format:\n"
        "{\n"
        "  \"reply_text\": \"...\",\n"
        "  \"summary\": \"...\",\n"
        "  \"sources\": [\"...\"],\n"
        "  \"requires_escalation\": false\n"
        "}"
    )
    context_str = json.dumps(specialist_results or {}, indent=2, default=str)
    user_prompt = (
        f"Domain: {domain}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"Context from internal tools:\n{context_str}\n"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = await call_openrouter_llm(messages, json_mode=True)
    if response_text:
        try:
            data = json.loads(response_text)
            return DraftResponse(
                reply_text=data.get("reply_text", ""),
                summary=data.get("summary", ""),
                sources=data.get("sources", []),
                requires_escalation=bool(data.get("requires_escalation", False)),
            )
        except Exception as e:
            logger.warning("Failed to parse LLM draft JSON: %s", e)

    return _fallback_draft(domain, subject, specialist_results)
