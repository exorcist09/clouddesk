"""Tests for technical specialist tools and vector search."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed import seed_all
from app.tools.technical import (
    get_known_bugs,
    get_outage_status,
    search_knowledge_base,
)


@pytest.mark.asyncio
async def test_get_known_bugs_gantt(db_session: AsyncSession):
    """Known bug query returns Gantt chart bug and workaround."""
    await seed_all(db_session)

    bugs = await get_known_bugs("gantt", db_session)
    assert len(bugs) >= 1
    assert "chrome" in bugs[0]["title"].lower() or "gantt" in bugs[0]["title"].lower()
    assert bugs[0]["workaround"] is not None


@pytest.mark.asyncio
async def test_get_outage_status(db_session: AsyncSession):
    """Outage query returns status for service or all."""
    await seed_all(db_session)

    outages = await get_outage_status("all", db_session)
    assert len(outages) >= 1

    api_outages = await get_outage_status("api", db_session)
    assert len(api_outages) >= 1
    assert api_outages[0]["service"] == "api"


@pytest.mark.asyncio
async def test_search_knowledge_base_empty_query(db_session: AsyncSession):
    """Empty query returns empty list."""
    results = await search_knowledge_base("", db_session)
    assert results == []


@pytest.mark.asyncio
async def test_search_knowledge_base_seeded(db_session: AsyncSession):
    """Vector search returns relevant knowledge articles."""
    await seed_all(db_session)

    results = await search_knowledge_base("two-factor authentication", db_session, limit=3)
    assert isinstance(results, list)
    if results:
        assert "title" in results[0]
        assert "content" in results[0]
