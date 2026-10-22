from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # billing | technical_support | account_management
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # OpenRouter embedding vector (supports any dimension: 384, 768, 1024, 1536)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(), nullable=True)

    def __repr__(self) -> str:
        return f"<KnowledgeArticle id={self.id} title={self.title!r}>"
