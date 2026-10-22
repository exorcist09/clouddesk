"""Technical support specialist tools including vector search."""
from __future__ import annotations

import logging
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings import embed_text
from app.models.knowledge_article import KnowledgeArticle
from app.models.known_bug import KnownBug
from app.models.outage import Outage

logger = logging.getLogger(__name__)


async def search_knowledge_base(
    query: str,
    session: AsyncSession,
    category: str | None = None,
    limit: int = 3,
    max_distance: float = 0.85,
) -> list[dict]:
    """
    Semantic search across knowledge articles using pgvector cosine distance.

    Args:
        query: Natural language query text.
        session: Active async DB session.
        category: Optional category filter ('billing', 'technical_support', 'account_management').
        limit: Max articles to return.
        max_distance: Max cosine distance threshold (lower is closer).

    Returns:
        List of matching articles sorted by relevance.
    """
    if not query.strip():
        return []

    # Get query embedding vector via OpenRouter
    query_vector = embed_text(query)

    # Cosine distance operator <=> in pgvector
    distance_col = KnowledgeArticle.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        sa.select(KnowledgeArticle, distance_col)
        .where(KnowledgeArticle.embedding.is_not(None))
    )

    if category:
        stmt = stmt.where(KnowledgeArticle.category == category)

    stmt = stmt.order_by(distance_col.asc()).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()

    matches = []
    for article, dist in rows:
        distance = float(dist) if dist is not None else 1.0
        # If distance exceeds threshold, it is considered irrelevant
        if distance <= max_distance:
            matches.append(
                {
                    "id": article.id,
                    "title": article.title,
                    "content": article.content,
                    "category": article.category,
                    "source": article.source,
                    "relevance_score": round(max(0.0, 1.0 - distance), 3),
                }
            )

    return matches


async def get_known_bugs(query: str, session: AsyncSession) -> list[dict]:
    """
    Search known issues and workarounds by keyword or service name.

    Args:
        query: Search term (e.g., 'gantt', 'chrome', 'export').
        session: Active async DB session.

    Returns:
        List of matching known bug dictionaries.
    """
    search_pattern = f"%{query.strip().lower()}%"
    stmt = sa.select(KnownBug).where(
        sa.or_(
            sa.func.lower(KnownBug.title).like(search_pattern),
            sa.func.lower(KnownBug.description).like(search_pattern),
            sa.func.lower(KnownBug.service).like(search_pattern),
        )
    )
    result = await session.execute(stmt)
    bugs = result.scalars().all()
    return [
        {
            "id": b.id,
            "title": b.title,
            "description": b.description,
            "workaround": b.workaround,
            "service": b.service,
            "status": b.status,
        }
        for b in bugs
    ]


async def get_outage_status(service: str, session: AsyncSession) -> list[dict]:
    """
    Check current service outages or incidents.

    Args:
        service: Service name to inspect, or 'all'.
        session: Active async DB session.

    Returns:
        List of active/recent outages for the service.
    """
    stmt = sa.select(Outage)
    if service and service.strip().lower() != "all":
        svc = f"%{service.strip().lower()}%"
        stmt = stmt.where(
            sa.or_(
                sa.func.lower(Outage.service).like(svc),
                sa.literal(service.strip().lower()).like(sa.func.concat("%", sa.func.lower(Outage.service), "%")),
            )
        )

    stmt = stmt.order_by(Outage.started_at.desc())
    result = await session.execute(stmt)
    outages = result.scalars().all()
    return [
        {
            "id": o.id,
            "service": o.service,
            "description": o.description,
            "status": o.status,
            "started_at": o.started_at.isoformat() if o.started_at else None,
            "resolved_at": o.resolved_at.isoformat() if o.resolved_at else None,
        }
        for o in outages
    ]
