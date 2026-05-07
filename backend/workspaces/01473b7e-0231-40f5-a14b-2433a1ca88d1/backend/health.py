# app/api/v1/endpoints/health.py
from fastapi import APIRouter, status
from core.config import settings
from custom_logger import logger

router = APIRouter(prefix="/health", tags=["health"])

@router.get(
    "/",
    summary="Health check endpoint",
    response_description="Application health status",
)
async def health_check():
    """Check the health status of the application."""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "1.0.0",
    }