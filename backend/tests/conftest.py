"""
Test fixtures for database integration tests.
Uses a real PostgreSQL/pgvector database — must be running.
Set TEST_DATABASE_URL to override (default: matches .env.example local defaults).
"""
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.config import get_settings
import app.models  # noqa: F401

from sqlalchemy.pool import NullPool

# Allow tests to override DB URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://clouddesk:clouddesk@localhost:5432/clouddesk_test",
)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create engine with NullPool, create all tables, drop after session."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)

    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yields a session that rolls back after each test."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
