"""FastAPI application entry point for CloudDesk."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown."""
    settings = get_settings()
    logger.info("Starting CloudDesk Backend with LLM model: %s", settings.openrouter_model)
    logger.info("Using embedding model: %s", settings.embedding_model)
    yield
    logger.info("Shutting down CloudDesk Backend")


app = FastAPI(
    title="CloudDesk Customer Support Agent API",
    version="1.0.0",
    description="Smart Customer Support Agent with LangGraph multi-agent routing, RAG, and human-in-the-loop review.",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health_check():
    """Service health check."""
    return {"status": "ok", "service": "clouddesk-api"}


@app.get("/", tags=["system"])
async def root():
    """API root redirecting to docs."""
    return {
        "message": "Welcome to CloudDesk Smart Support Agent API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }
