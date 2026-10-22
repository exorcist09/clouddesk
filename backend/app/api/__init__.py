"""API routers package."""
from fastapi import APIRouter
from app.api.tickets import router as tickets_router
from app.api.reviews import router as reviews_router

api_router = APIRouter(prefix="/api")
api_router.include_router(tickets_router)
api_router.include_router(reviews_router)

__all__ = ["api_router"]
