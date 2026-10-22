from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    subscription_plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )  # free | pro | enterprise
    tfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    team_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        "Payment", back_populates="customer", lazy="select"
    )
    tickets: Mapped[list["Ticket"]] = relationship(  # noqa: F821
        "Ticket", back_populates="customer", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} email={self.email}>"
