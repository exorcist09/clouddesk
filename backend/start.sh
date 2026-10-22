#!/bin/bash
set -e

echo "Starting CloudDesk API service..."

# Run alembic migrations
echo "Applying database migrations..."
alembic upgrade head || echo "Migration notice: continuing..."

# Run seed script
echo "Seeding initial data..."
python -m app.seed || echo "Seed notice: continuing..."

# Setup LangGraph checkpoint tables
echo "Ensuring LangGraph checkpoint tables..."
python -c "
import asyncio, os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
async def init():
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith('postgresql+psycopg://'):
        url = url.replace('postgresql+psycopg://', 'postgresql://')
    elif url.startswith('postgresql+asyncpg://'):
        url = url.replace('postgresql+asyncpg://', 'postgresql://')
    if not url:
        u = os.environ.get('POSTGRES_USER', 'clouddesk')
        p = os.environ.get('POSTGRES_PASSWORD', 'clouddesk')
        h = os.environ.get('POSTGRES_HOST', 'db')
        port = os.environ.get('POSTGRES_PORT', '5432')
        d = os.environ.get('POSTGRES_DB', 'clouddesk')
        url = f'postgresql://{u}:{p}@{h}:{port}/{d}'
    try:
        async with AsyncPostgresSaver.from_conn_string(url) as cp:
            await cp.setup()
    except Exception as e:
        print('Checkpoint notice:', e)
asyncio.run(init())
" || true

echo "Starting Uvicorn server on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
