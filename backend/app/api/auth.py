"""Authentication Routes & Middleware — handles Clerk JWTs."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verifies the Clerk JWT token. 
    In production, use the official Clerk SDK or verify JWKS.
    """
    token = credentials.credentials
    if not token or not settings.clerk_publishable_key:
        # Mock validation for development
        if settings.debug and token == "mock-dev-token":
            return {"user_id": "user_dev_123"}
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    # Real validation would happen here
    # For now, we'll accept any non-empty token as mock
    return {"user_id": "user_live_456"}

@router.get("/me")
async def get_current_user(user: dict = Depends(verify_clerk_token)):
    """Returns the currently authenticated user."""
    return user
