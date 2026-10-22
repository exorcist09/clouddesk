from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TicketDomain(str, enum.Enum):
    BILLING = "BILLING"
    TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT"
    ACCOUNT_MANAGEMENT = "ACCOUNT_MANAGEMENT"
    UNKNOWN = "UNKNOWN"


class TicketStatus(str, enum.Enum):
    PENDING = "PENDING"           # received, not yet processed
    PROCESSING = "PROCESSING"     # workflow running
    PENDING_REVIEW = "PENDING_REVIEW"  # paused, awaiting human
    RESOLVED = "RESOLVED"         # auto-resolved or manager approved
    REJECTED = "REJECTED"         # manager rejected
    NEEDS_FOLLOW_UP = "NEEDS_FOLLOW_UP"  # requires further action
    FAILED = "FAILED"             # unrecoverable error


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    domain: Mapped[TicketDomain | None] = mapped_column(
        Enum(TicketDomain, name="ticket_domain"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Workflow state
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        nullable=False,
        default=TicketStatus.PENDING,
        index=True,
    )
    workflow_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # LangGraph thread_id for checkpoint lookup
    thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Content
    specialist_results: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_reply: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Escalation
    escalation_required: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error tracking
    error_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer: Mapped["Customer | None"] = relationship(  # noqa: F821
        "Customer", back_populates="tickets"
    )
    review_decision: Mapped["ReviewDecision | None"] = relationship(  # noqa: F821
        "ReviewDecision", back_populates="ticket", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status} domain={self.domain}>"
